import hashlib
import logging
import time
from typing import List, Dict, Any, Optional
from backend.config import settings
from backend.models.schemas import ChunkInfo
from backend.rag.chunking import ChunkingEngine, generate_chunk_id

logger = logging.getLogger(__name__)

# Language code to MSMARCO-XI HuggingFace config mapping
LANG_TO_HF_CONFIG = {
    "hi": "hi",
    "te": "te",
    "en": "en",
    "bn": "bn",
    "ta": "ta",
    "kn": "kn",
    "ml": "ml",
    "mr": "mr",
    "gu": "gu",
    "pa": "pa",
    "or": "or",
    "ur": "ur",
    "as": "as",
    "ne": "ne",
    "sa": "sa",
}

LANG_NAMES = {
    "hi": "Hindi",
    "te": "Telugu",
    "en": "English",
    "bn": "Bengali",
    "ta": "Tamil",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "or": "Odia",
    "ur": "Urdu",
    "as": "Assamese",
    "ne": "Nepali",
    "sa": "Sanskrit",
}


class MSMARCOLoader:
    """
    Loads passages from ai4bharat/MSMARCO-XI into the VocaRAG ingestion pipeline.
    Preserves exact passage-level metadata (passage_id, query_id, is_selected, language).
    """

    def __init__(self):
        self._loaded = False
        self._passage_docs: List[Dict[str, Any]] = []
        self._gold_pairs: List[Dict[str, Any]] = []  # For IR eval (Recall@k, MRR)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def gold_pairs(self) -> List[Dict[str, Any]]:
        return self._gold_pairs

    @property
    def passage_docs(self) -> List[Dict[str, Any]]:
        return self._passage_docs

    def load_msmarco_corpus(self) -> List[Dict[str, Any]]:
        """
        Downloads and processes MSMARCO-XI passages for configured languages.
        Preserves passage_id, query_id, is_selected for each individual passage.
        """
        if not settings.MSMARCO_ENABLED:
            logger.info("MSMARCO-XI ingestion is disabled.")
            return []

        try:
            from datasets import load_dataset
        except ImportError:
            logger.error("'datasets' library not installed. Run: pip install datasets")
            return []

        all_passages = []
        self._gold_pairs = []

        for lang in settings.MSMARCO_LANGUAGES:
            lang = lang.strip()
            if lang not in LANG_TO_HF_CONFIG:
                logger.warning(f"Unknown MSMARCO-XI language: {lang}. Skipping.")
                continue

            target_count = settings.MSMARCO_SLICE_SIZES.get(lang, 500)
            raw_count = int(target_count * settings.MSMARCO_RAW_OVERSAMPLE)

            logger.info(
                f"Loading MSMARCO-XI [{lang}] ({LANG_NAMES.get(lang, lang)}): "
                f"sampling {raw_count} raw rows -> target {target_count} clean passages"
            )

            t_start = time.perf_counter()

            try:
                hf_config = LANG_TO_HF_CONFIG[lang]
                if lang == "en":
                    ds = load_dataset(
                        "microsoft/ms_marco",
                        "v1.1",
                        split=f"train[:{raw_count}]",
                        trust_remote_code=True,
                    )
                else:
                    ds = load_dataset(
                        "ai4bharat/MSMARCO-XI",
                        hf_config,
                        split=f"train[:{raw_count}]",
                        trust_remote_code=True,
                    )
            except Exception as e:
                logger.error(f"Failed to load MSMARCO-XI [{lang}]: {e}")
                continue

            load_time = round((time.perf_counter() - t_start) * 1000, 2)
            logger.info(f"Downloaded {len(ds)} rows for [{lang}] in {load_time}ms")

            seen_hashes = set()
            lang_passages = []

            for row_idx, row in enumerate(ds):
                passages = row.get("passages", {})
                if not passages:
                    continue

                passage_texts = passages.get("passage_text", [])
                is_selected_flags = passages.get("is_selected", [])
                query_text = row.get("query", "")
                query_id = str(row.get("query_id", row_idx))

                for p_idx, p_text in enumerate(passage_texts):
                    if not p_text or not isinstance(p_text, str):
                        continue

                    p_text = p_text.strip()
                    if len(p_text) < 40:
                        continue

                    content_hash = hashlib.md5(p_text.encode("utf-8")).hexdigest()
                    if content_hash in seen_hashes:
                        continue
                    seen_hashes.add(content_hash)

                    is_selected = bool(
                        is_selected_flags[p_idx]
                        if p_idx < len(is_selected_flags)
                        else 0
                    )
                    passage_id = f"{lang}_{query_id}_p{p_idx}"

                    passage_doc = {
                        "text": p_text,
                        "language": lang,
                        "language_name": LANG_NAMES.get(lang, lang),
                        "query_id": query_id,
                        "passage_id": passage_id,
                        "is_selected": is_selected,
                        "source": "msmarco_xi",
                        "content_hash": content_hash,
                    }
                    lang_passages.append(passage_doc)

                    if is_selected and query_text:
                        self._gold_pairs.append({
                            "query": query_text,
                            "passage_id": passage_id,
                            "query_id": query_id,
                            "language": lang,
                            "language_name": LANG_NAMES.get(lang, lang),
                        })

                    if len(lang_passages) >= target_count:
                        break

                if len(lang_passages) >= target_count:
                    break

            logger.info(
                f"MSMARCO-XI [{lang}]: extracted {len(lang_passages)} clean passages "
                f"({len([p for p in lang_passages if p['is_selected']])} gold-relevant)"
            )
            all_passages.extend(lang_passages)

        self._passage_docs = all_passages
        self._loaded = True
        logger.info(
            f"MSMARCO-XI total: {len(all_passages)} passages across "
            f"{len(settings.MSMARCO_LANGUAGES)} languages, "
            f"{len(self._gold_pairs)} gold query-passage pairs for IR eval"
        )
        return all_passages

    def get_passage_chunks(self, chunk_size: int = 450, chunk_overlap: int = 80) -> List[ChunkInfo]:
        """
        Directly converts individual MS MARCO passages into ChunkInfo objects.
        Preserves passage_id, query_id, is_selected in metadata without lossy document concatenation.
        """
        chunks: List[ChunkInfo] = []
        
        for idx, p in enumerate(self._passage_docs):
            p_text = p["text"]
            doc_id = f"msmarco_{p['language']}"
            doc_name = f"msmarco_xi_{p['language']}.txt"
            
            meta = {
                "passage_id": p["passage_id"],
                "query_id": p["query_id"],
                "is_selected": p["is_selected"],
                "language": p["language"],
                "language_name": p["language_name"],
                "source_type": "msmarco_xi",
                "category_badge": "MSMARCO",
                "collection": "msmarco",
                "is_sample": True
            }

            # If passage fits inside chunk_size, create 1 ChunkInfo directly
            if len(p_text) <= chunk_size:
                c_id = generate_chunk_id(doc_id, idx, p_text)
                chunks.append(ChunkInfo(
                    id=c_id,
                    doc_id=doc_id,
                    doc_name=doc_name,
                    chunk_index=idx,
                    content=p_text,
                    char_count=len(p_text),
                    metadata={**meta, "strategy": "passage-direct"}
                ))
            else:
                # Sub-chunk only large passages, preserving passage-level metadata on each sub-chunk
                sub_chunks = ChunkingEngine.chunk_recursive(
                    text=p_text,
                    doc_id=doc_id,
                    doc_name=doc_name,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    metadata=meta
                )
                for sc in sub_chunks:
                    sc.chunk_index = len(chunks)
                    sc.id = generate_chunk_id(doc_id, sc.chunk_index, sc.content)
                    chunks.append(sc)

        return chunks


# Singleton instance
msmarco_loader = MSMARCOLoader()
