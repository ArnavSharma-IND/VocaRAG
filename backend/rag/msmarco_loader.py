import os
import json
import hashlib
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.config import settings
from backend.models.schemas import ChunkInfo
from backend.rag.chunking import ChunkingEngine, generate_chunk_id

logger = logging.getLogger(__name__)

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

LOCAL_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "msmarco"


class MSMARCOLoader:
    """
    Loads passages from bundled MSMARCO-XI dataset or HuggingFace Hub into the VocaRAG ingestion pipeline.
    Preserves exact passage-level metadata (passage_id, query_id, is_selected, language).
    """

    def __init__(self):
        self._loaded = False
        self._passage_docs: List[Dict[str, Any]] = []
        self._gold_pairs: List[Dict[str, Any]] = []

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def gold_pairs(self) -> List[Dict[str, Any]]:
        return self._gold_pairs

    @property
    def passage_docs(self) -> List[Dict[str, Any]]:
        return self._passage_docs

    def _load_from_local_jsonl(self, lang: str) -> List[Dict[str, Any]]:
        """Loads bundled JSONL dataset directly from data/msmarco/{lang}.jsonl."""
        jsonl_path = LOCAL_DATA_DIR / f"{lang}.jsonl"
        if not jsonl_path.exists():
            return []

        rows = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return rows

    def load_msmarco_corpus(self) -> List[Dict[str, Any]]:
        """
        Loads MSMARCO-XI passages for configured languages.
        First checks pre-bundled local data/msmarco/{lang}.jsonl for instant deterministic seeding.
        Preserves passage_id, query_id, is_selected for each individual passage.
        """
        if not settings.MSMARCO_ENABLED:
            logger.info("MSMARCO-XI ingestion is disabled.")
            return []

        all_passages = []
        self._gold_pairs = []

        for lang in settings.MSMARCO_LANGUAGES:
            lang = lang.strip()
            target_count = settings.MSMARCO_SLICE_SIZES.get(lang, 500)
            raw_count = int(target_count * settings.MSMARCO_RAW_OVERSAMPLE)

            logger.info(
                f"Loading MSMARCO-XI [{lang}] ({LANG_NAMES.get(lang, lang)}): "
                f"target {target_count} clean passages"
            )

            t_start = time.perf_counter()
            raw_rows = self._load_from_local_jsonl(lang)

            if not raw_rows:
                # Fallback to HuggingFace Hub if local jsonl is absent
                try:
                    from datasets import load_dataset
                    if lang == "en":
                        ds = load_dataset("microsoft/ms_marco", "v1.1", split=f"train[:{raw_count}]")
                    else:
                        ds = load_dataset("ai4bharat/MSMARCO-XI", "default", split=f"train[:{raw_count}]")
                    raw_rows = list(ds)
                except Exception as e:
                    logger.warning(f"Could not load MSMARCO-XI [{lang}] from Hub: {e}")
                    raw_rows = []

            load_time = round((time.perf_counter() - t_start) * 1000, 2)
            logger.info(f"Loaded {len(raw_rows)} raw rows for [{lang}] in {load_time}ms")

            seen_hashes = set()
            lang_passages = []

            for row_idx, row in enumerate(raw_rows):
                passages = row.get("passages", {})
                if not passages:
                    continue

                if isinstance(passages, list):
                    # Direct list of passage dicts: [{"passage_text": "...", "is_selected": 1}]
                    passage_texts = [p.get("passage_text", "") for p in passages]
                    is_selected_flags = [p.get("is_selected", 0) for p in passages]
                elif isinstance(passages, dict):
                    # HF Dict format: {"passage_text": [...], "is_selected": [...]}
                    passage_texts = passages.get("passage_text", [])
                    is_selected_flags = passages.get("is_selected", [])
                else:
                    continue

                query_text = row.get("query", "")
                query_id = str(row.get("query_id", f"{lang}_q{row_idx}"))

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

            logger.info(
                f"MSMARCO-XI [{lang}]: indexed {len(lang_passages)} clean passages "
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


msmarco_loader = MSMARCOLoader()
