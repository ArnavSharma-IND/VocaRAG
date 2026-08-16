import os
import io
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np
from backend.config import settings
from backend.models.schemas import DocumentInfo, ChunkInfo, KnowledgeBaseStats
from backend.rag.chunking import ChunkingEngine
from backend.rag.embeddings import embedding_engine
from backend.rag.retriever import vector_retriever

logger = logging.getLogger(__name__)

class IngestionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IngestionManager, cls).__new__(cls)
            cls._instance._init_manager()
        return cls._instance

    def _init_manager(self):
        self.documents: Dict[str, DocumentInfo] = {}
        self.raw_texts: Dict[str, str] = {} # doc_id -> raw text
        self.active_strategy: str = settings.DEFAULT_CHUNK_STRATEGY
        self.active_chunk_size: int = settings.DEFAULT_CHUNK_SIZE
        self.active_chunk_overlap: int = settings.DEFAULT_CHUNK_OVERLAP
        self.last_indexed_at: Optional[str] = None

    def parse_file(self, filename: str, content_bytes: bytes) -> str:
        """Extracts plain text from various file formats (.txt, .md, .pdf, .docx)."""
        suffix = Path(filename).suffix.lower()

        if suffix in [".txt", ".md", ".csv", ".json", ".log"]:
            try:
                return content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return content_bytes.decode("latin-1", errors="ignore")

        elif suffix == ".pdf":
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
        auto_reindex: bool = True
    ) -> DocumentInfo:
        """Ingests a document, extracts text, saves it, and optionally updates vector index."""
        import hashlib
        doc_id = f"doc_{hashlib.md5(name.encode('utf-8')).hexdigest()[:8]}"
        
        raw_text = self.parse_file(name, content_bytes)
        self.raw_texts[doc_id] = raw_text

        # Determine source type and category badge
        is_gk = name.lower().startswith("general_knowledge")
        if is_gk:
            source_type = "general_knowledge"
            category_badge = "GENERAL"
        elif is_sample:
            source_type = "sample_policy"
            category_badge = "SAMPLE"
        else:
            source_type = "user_upload"
            category_badge = "UPLOAD"

        # Save to disk
        dest_dir = settings.SAMPLE_DOCS_DIR if is_sample else settings.UPLOAD_DIR
        dest_dir.mkdir(parents=True, exist_ok=True)
        file_path = dest_dir / name
        try:
            with open(file_path, "wb") as f:
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
            uploaded_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            is_sample=is_sample,
            source_type=source_type,
            category_badge=category_badge
        )
        self.documents[doc_id] = doc_info

        if auto_reindex:
            self.reindex_all(
                strategy=self.active_strategy,
                chunk_size=self.active_chunk_size,
                chunk_overlap=self.active_chunk_overlap
            )

        return self.documents[doc_id]

    def delete_document(self, doc_id: str) -> bool:
        """Removes a document and reindexes the remaining corpus."""
        if doc_id not in self.documents:
            return False

        doc = self.documents.pop(doc_id)
        self.raw_texts.pop(doc_id, None)

        # Delete physical file
        target_path = (settings.SAMPLE_DOCS_DIR if doc.is_sample else settings.UPLOAD_DIR) / doc.name
        if target_path.exists():
            try:
                target_path.unlink()
            except Exception as e:
                logger.warning(f"Could not delete physical file: {e}")

        self.reindex_all(
            strategy=self.active_strategy,
            chunk_size=self.active_chunk_size,
            chunk_overlap=self.active_chunk_overlap
        )
        return True

    def get_all_documents(self) -> List[DocumentInfo]:
        return list(self.documents.values())

    def reindex_all(
        self,
        strategy: str = "recursive",
        chunk_size: int = 450,
        chunk_overlap: int = 80
    ) -> KnowledgeBaseStats:
        """
        Rechunks all loaded documents using the requested strategy and rebuilds the FAISS vector index.
        """
        self.active_strategy = strategy
        self.active_chunk_size = chunk_size
        self.active_chunk_overlap = chunk_overlap

        all_chunks: List[ChunkInfo] = []

        for doc_id, doc in self.documents.items():
            raw_text = self.raw_texts.get(doc_id, "")
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
                    "source_name": doc.name
                }
            )
            doc.chunks_count = len(chunks)
            all_chunks.extend(chunks)

        # Batch compute embeddings
        texts_to_embed = [c.content for c in all_chunks]
        if texts_to_embed:
            embeddings = embedding_engine.embed_texts(texts_to_embed)
            vector_retriever.build_index(all_chunks, embeddings)
        else:
            vector_retriever.build_index([], np.empty((0, embedding_engine.dimension), dtype=np.float32))

        self.last_indexed_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        return self.get_stats()

    def get_stats(self) -> KnowledgeBaseStats:
        """Returns live statistics of the knowledge base."""
        total_chunks = sum(d.chunks_count for d in self.documents.values())
        return KnowledgeBaseStats(
            documents_count=len(self.documents),
            chunks_count=total_chunks,
            embeddings_count=vector_retriever.total_chunks,
            chunking_strategy=self.active_strategy,
            chunk_size=self.active_chunk_size,
            chunk_overlap=self.active_chunk_overlap,
            last_indexed_at=self.last_indexed_at,
            embedding_dimension=embedding_engine.dimension,
            index_ready=vector_retriever.is_indexed
        )

    def load_sample_knowledge_base(self):
        """Loads sample files from data/sample_docs if present."""
        if not settings.SAMPLE_DOCS_DIR.exists():
            return

        sample_files = sorted(list(settings.SAMPLE_DOCS_DIR.glob("*.*")), key=lambda p: p.name)
        logger.info(f"Found {len(sample_files)} sample documents to load.")

        for p in sample_files:
            if p.is_file() and p.suffix.lower() in [".txt", ".md", ".pdf", ".docx"]:
                with open(p, "rb") as f:
                    content = f.read()
                self.ingest_document(p.name, content, is_sample=True, auto_reindex=False)

        # Ingest uploads if any
        if settings.UPLOAD_DIR.exists():
            upload_files = sorted(list(settings.UPLOAD_DIR.glob("*.*")), key=lambda p: p.name)
            for p in upload_files:
                if p.is_file() and p.suffix.lower() in [".txt", ".md", ".pdf", ".docx"]:
                    with open(p, "rb") as f:
                        content = f.read()
                    self.ingest_document(p.name, content, is_sample=False, auto_reindex=False)

        # Single index build
        self.reindex_all(
            strategy=self.active_strategy,
            chunk_size=self.active_chunk_size,
            chunk_overlap=self.active_chunk_overlap
        )
        logger.info(f"Knowledge Base initialized with {len(self.documents)} documents.")

ingestion_manager = IngestionManager()
