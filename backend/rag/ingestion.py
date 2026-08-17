import io
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import numpy as np
from backend.models.schemas import DocumentInfo, ChunkInfo, KnowledgeBaseStats
from backend.config import settings
from backend.rag.chunking import ChunkingEngine
from backend.rag.embeddings import embedding_engine
from backend.rag.retriever import retriever_registry

logger = logging.getLogger(__name__)

class IngestionManager:
    def __init__(self):
        self.documents_by_coll: Dict[str, Dict[str, DocumentInfo]] = {
            "enterprise": {},
            "msmarco": {}
        }
        self.raw_texts_by_coll: Dict[str, Dict[str, str]] = {
            "enterprise": {},
            "msmarco": {}
        }
        self.active_strategy = settings.DEFAULT_CHUNK_STRATEGY
        self.active_chunk_size = settings.DEFAULT_CHUNK_SIZE
        self.active_chunk_overlap = settings.DEFAULT_CHUNK_OVERLAP
        self.last_indexed_at_by_coll: Dict[str, Optional[str]] = {
            "enterprise": None,
            "msmarco": None
        }

    @property
    def documents(self) -> Dict[str, DocumentInfo]:
        return self.documents_by_coll["enterprise"]

    @property
    def raw_texts(self) -> Dict[str, str]:
        return self.raw_texts_by_coll["enterprise"]

    def parse_file(self, filename: str, content_bytes: bytes) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(content_bytes))
                text_pages = []
                for idx, page in enumerate(reader.pages):
                    p_text = page.extract_text()
                    if p_text:
                        text_pages.append(f"--- Page {idx + 1} ---\n{p_text}")
                return "\n\n".join(text_pages)
            except Exception as e:
                logger.error(f"Error parsing PDF '{filename}': {e}")
                return content_bytes.decode("latin-1", errors="ignore")
        elif suffix in [".docx", ".doc"]:
            try:
                import docx
                doc = docx.Document(io.BytesIO(content_bytes))
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                return "\n\n".join(paragraphs)
            except Exception as e:
                logger.error(f"Error parsing DOCX '{filename}': {e}")
                return content_bytes.decode("latin-1", errors="ignore")
        else:
            return content_bytes.decode("utf-8", errors="ignore")

    def ingest_document(
        self,
        name: str,
        content_bytes: bytes,
        is_sample: bool = False,
        collection: str = "enterprise",
        language: Optional[str] = None,
        auto_reindex: bool = True
    ) -> DocumentInfo:
        import hashlib
        doc_id = f"doc_{hashlib.md5(f'{collection}_{name}'.encode('utf-8')).hexdigest()[:8]}"
        raw_text = self.parse_file(name, content_bytes)

        if collection not in self.documents_by_coll:
            self.documents_by_coll[collection] = {}
            self.raw_texts_by_coll[collection] = {}

        self.raw_texts_by_coll[collection][doc_id] = raw_text

        is_msmarco = name.lower().startswith("msmarco") or collection == "msmarco"
        is_gk = name.lower().startswith("general_knowledge")
        
        if is_msmarco:
            source_type = "msmarco_xi"
            category_badge = "MSMARCO"
        elif is_gk:
            source_type = "general_knowledge"
            category_badge = "GENERAL"
        elif is_sample:
            source_type = "sample_policy"
            category_badge = "SAMPLE"
        else:
            source_type = "user_upload"
            category_badge = "UPLOAD"

        if is_sample and not is_msmarco:
            dest_dir = settings.SAMPLE_DOCS_DIR
            dest_dir.mkdir(parents=True, exist_ok=True)
            try:
                with open(dest_dir / name, "wb") as f:
                    f.write(content_bytes)
            except Exception as e:
                logger.warning(f"Could not save file to disk: {e}")

        file_type = Path(name).suffix.upper().replace(".", "") or "TXT"

        doc_info = DocumentInfo(
            id=doc_id,
            name=name,
            size_bytes=len(content_bytes),
            file_type=file_type,
            chunks_count=0,
            uploaded_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            is_sample=is_sample,
            source_type=source_type,
            category_badge=category_badge,
            language=language,
            collection=collection
        )
        self.documents_by_coll[collection][doc_id] = doc_info

        if auto_reindex:
            self.reindex_all(
                collection=collection,
                strategy=self.active_strategy,
                chunk_size=self.active_chunk_size,
                chunk_overlap=self.active_chunk_overlap
            )

        return doc_info

    def delete_document(self, doc_id: str, collection: str = "enterprise") -> bool:
        docs = self.documents_by_coll.get(collection, {})
        if doc_id not in docs:
            return False

        doc = docs.pop(doc_id)
        self.raw_texts_by_coll.get(collection, {}).pop(doc_id, None)

        target_path = (settings.SAMPLE_DOCS_DIR if doc.is_sample else settings.UPLOAD_DIR) / doc.name
        if target_path.exists():
            try:
                target_path.unlink()
            except Exception as e:
                logger.warning(f"Could not delete physical file: {e}")

        self.reindex_all(collection=collection, strategy=self.active_strategy, chunk_size=self.active_chunk_size, chunk_overlap=self.active_chunk_overlap)
        return True

    def get_all_documents(self, collection: Optional[str] = None) -> List[DocumentInfo]:
        if collection:
            return list(self.documents_by_coll.get(collection, {}).values())
        result = []
        for coll_docs in self.documents_by_coll.values():
            result.extend(coll_docs.values())
        return result

    def reindex_all(
        self,
        collection: str = "enterprise",
        strategy: str = "recursive",
        chunk_size: int = 450,
        chunk_overlap: int = 80
    ) -> KnowledgeBaseStats:
        self.active_strategy = strategy
        self.active_chunk_size = chunk_size
        self.active_chunk_overlap = chunk_overlap

        # Special metadata-preserving path for MSMARCO collection
        if collection == "msmarco":
            from backend.rag.msmarco_loader import msmarco_loader
            if not msmarco_loader.is_loaded:
                msmarco_loader.load_msmarco_corpus()
            all_chunks = msmarco_loader.get_passage_chunks(chunk_size, chunk_overlap)
        else:
            docs = self.documents_by_coll.get(collection, {})
            raws = self.raw_texts_by_coll.get(collection, {})
            all_chunks: List[ChunkInfo] = []

            for doc_id, doc in docs.items():
                raw_text = raws.get(doc_id, "")
                if not raw_text.strip():
                    continue

                chunks = ChunkingEngine.chunk_document(
                    text=raw_text,
                    doc_id=doc_id,
                    doc_name=doc.name,
                    strategy=strategy,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    metadata={
                        "is_sample": doc.is_sample,
                        "file_type": doc.file_type,
                        "source_type": doc.source_type,
                        "category_badge": doc.category_badge,
                        "source_name": doc.name,
                        "language": doc.language,
                        "collection": collection
                    }
                )
                doc.chunks_count = len(chunks)
                all_chunks.extend(chunks)

        retriever = retriever_registry.get_retriever(collection)
        texts_to_embed = [c.content for c in all_chunks]
        if texts_to_embed:
            embeddings = embedding_engine.embed_texts(texts_to_embed)
            retriever.build_index(all_chunks, embeddings)
        else:
            retriever.build_index([], np.empty((0, embedding_engine.dimension), dtype=np.float32))

        self.last_indexed_at_by_coll[collection] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        return self.get_stats(collection)

    def get_stats(self, collection: str = "enterprise") -> KnowledgeBaseStats:
        docs = self.documents_by_coll.get(collection, {})
        retriever = retriever_registry.get_retriever(collection)
        total_chunks = retriever.total_chunks
        return KnowledgeBaseStats(
            documents_count=len(docs),
            chunks_count=total_chunks,
            embeddings_count=retriever.total_chunks,
            chunking_strategy=self.active_strategy,
            chunk_size=self.active_chunk_size,
            chunk_overlap=self.active_chunk_overlap,
            last_indexed_at=self.last_indexed_at_by_coll.get(collection),
            embedding_dimension=embedding_engine.dimension,
            index_ready=retriever.is_indexed,
            collection=collection
        )

    def load_sample_knowledge_base(self):
        """Loads sample files from data/sample_docs into the enterprise collection."""
        if not settings.SAMPLE_DOCS_DIR.exists():
            return

        sample_files = sorted(list(settings.SAMPLE_DOCS_DIR.glob("*.*")), key=lambda p: p.name)
        logger.info(f"Loading {len(sample_files)} enterprise sample documents.")

        for p in sample_files:
            if p.is_file() and p.suffix.lower() in [".txt", ".md", ".pdf", ".docx"]:
                with open(p, "rb") as f:
                    content = f.read()
                self.ingest_document(p.name, content, is_sample=True, collection="enterprise", auto_reindex=False)

        if settings.UPLOAD_DIR.exists():
            upload_files = sorted(list(settings.UPLOAD_DIR.glob("*.*")), key=lambda p: p.name)
            for p in upload_files:
                if p.is_file() and p.suffix.lower() in [".txt", ".md", ".pdf", ".docx"]:
                    with open(p, "rb") as f:
                        content = f.read()
                    self.ingest_document(p.name, content, is_sample=False, collection="enterprise", auto_reindex=False)

        self.reindex_all(collection="enterprise", strategy=self.active_strategy, chunk_size=self.active_chunk_size, chunk_overlap=self.active_chunk_overlap)
        logger.info(f"Enterprise Knowledge Base initialized with {len(self.documents_by_coll['enterprise'])} documents.")

    def load_msmarco_knowledge_base(self):
        """
        Loads MSMARCO-XI multilingual passages directly into the msmarco collection
        with intact passage-level metadata (passage_id, query_id, is_selected).
        """
        if not settings.MSMARCO_ENABLED:
            logger.info("MSMARCO loading is disabled.")
            return

        from backend.rag.msmarco_loader import msmarco_loader
        msmarco_loader.load_msmarco_corpus()
        
        # Ingest document records per language
        for lang in settings.MSMARCO_LANGUAGES:
            lang = lang.strip()
            lang_passages = [p for p in msmarco_loader.passage_docs if p["language"] == lang]
            doc_id = f"msmarco_{lang}"
            doc_name = f"msmarco_xi_{lang}.txt"
            
            doc_info = DocumentInfo(
                id=doc_id,
                name=doc_name,
                size_bytes=sum(len(p["text"].encode("utf-8")) for p in lang_passages),
                file_type="TXT",
                chunks_count=len(lang_passages),
                uploaded_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                is_sample=True,
                source_type="msmarco_xi",
                category_badge="MSMARCO",
                language=lang,
                collection="msmarco"
            )
            self.documents_by_coll["msmarco"][doc_id] = doc_info

        # Build index preserving passage metadata
        self.reindex_all(collection="msmarco", strategy=self.active_strategy, chunk_size=self.active_chunk_size, chunk_overlap=self.active_chunk_overlap)
        logger.info(f"MSMARCO Knowledge Base initialized with {len(self.documents_by_coll['msmarco'])} language collections.")

ingestion_manager = IngestionManager()
