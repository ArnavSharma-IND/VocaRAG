import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from backend.config import settings
from backend.models.schemas import SourceItem, ChunkInfo

logger = logging.getLogger(__name__)

class VectorRetriever:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorRetriever, cls).__new__(cls)
            cls._instance._init_retriever()
        return cls._instance

    def _init_retriever(self):
        self.chunks: List[ChunkInfo] = []
        self.embeddings: Optional[np.ndarray] = None
        self.faiss_index = None
        self.use_faiss = False
        self.dimension = settings.EMBEDDING_DIMENSION
        self._init_faiss()

    def _init_faiss(self):
        try:
            import faiss
            self.faiss_module = faiss
            self.faiss_index = faiss.IndexFlatIP(self.dimension)
            self.use_faiss = True
            logger.info("FAISS IndexFlatIP initialized.")
        except Exception as e:
            logger.warning(f"FAISS not available ({e}). Using optimized numpy cosine indexing.")
            self.use_faiss = False

    @property
    def total_chunks(self) -> int:
        return len(self.chunks)

    @property
    def is_indexed(self) -> bool:
        return len(self.chunks) > 0 and (self.faiss_index is not None or self.embeddings is not None)

    def build_index(self, chunks: List[ChunkInfo], embeddings: np.ndarray):
        """Builds or resets the vector index with fresh chunks and embeddings."""
        self.chunks = list(chunks)
        self.embeddings = embeddings.astype(np.float32)

        if self.embeddings.shape[0] > 0:
            self.dimension = self.embeddings.shape[1]

        if self.use_faiss and self.faiss_module is not None:
            try:
                self.faiss_index = self.faiss_module.IndexFlatIP(self.dimension)
                if len(self.chunks) > 0 and self.embeddings.shape[0] > 0:
                    self.faiss_index.add(self.embeddings)
                logger.info(f"FAISS index built with {len(self.chunks)} vectors (dim: {self.dimension}).")
            except Exception as e:
                logger.error(f"Failed to populate FAISS index: {e}. Falling back to numpy.")
                self.use_faiss = False

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.25,
        filter_doc_id: Optional[str] = None
    ) -> List[SourceItem]:
        """
        Executes vector similarity search, filters by threshold & metadata,
        deduplicates, and computes relevance tiers & source categories.
        """
        if len(self.chunks) == 0:
            return []

        query_vector = np.array(query_vector, dtype=np.float32).reshape(1, -1)
        # Ensure query vector is normalized
        q_norm = np.linalg.norm(query_vector)
        if q_norm > 0:
            query_vector = query_vector / q_norm

        top_k = min(top_k, len(self.chunks))

        scores: np.ndarray
        indices: np.ndarray

        fetch_k = min(len(self.chunks), max(top_k * 4, 20))

        if self.use_faiss and self.faiss_index is not None and self.faiss_index.ntotal > 0:
            scores_raw, indices_raw = self.faiss_index.search(query_vector, fetch_k)
            scores = scores_raw[0]
            indices = indices_raw[0]
        else:
            all_scores = np.dot(self.embeddings, query_vector.T).flatten()
            sorted_idx = np.argsort(-all_scores)
            indices = sorted_idx[:fetch_k]
            scores = all_scores[indices]

        raw_candidates = []
        for score, idx in zip(scores, indices):
            if idx < 0 or idx >= len(self.chunks):
                continue

            similarity = float(score)
            if similarity < threshold:
                continue

            chunk = self.chunks[idx]
            if filter_doc_id and chunk.doc_id != filter_doc_id:
                continue

            raw_candidates.append((similarity, chunk))

        # Check if domain specific policy has strong evidence
        # Domain priority: if high-confidence domain policy exists (score >= 0.35), ensure it ranks top
        domain_candidates = [c for c in raw_candidates if not c[1].doc_name.lower().startswith("general_knowledge")]
        gk_candidates = [c for c in raw_candidates if c[1].doc_name.lower().startswith("general_knowledge")]

        # Determine ordering:
        # If top domain candidate has strong match (>= 0.38), rank domain candidates first then GK
        # Otherwise sort purely by cosine similarity
        if domain_candidates and domain_candidates[0][0] >= 0.38:
            ordered_candidates = domain_candidates + gk_candidates
        else:
            ordered_candidates = sorted(raw_candidates, key=lambda x: x[0], reverse=True)

        results: List[SourceItem] = []
        seen_texts = set()

        for similarity, chunk in ordered_candidates:
            text_fingerprint = chunk.content[:100].lower()
            if text_fingerprint in seen_texts:
                continue
            seen_texts.add(text_fingerprint)

            # Assign relevance tier
            if similarity >= 0.65:
                tier = "High"
            elif similarity >= 0.45:
                tier = "Medium"
            else:
                tier = "Low"

            # Assign category label and source_type
            is_gk = chunk.doc_name.lower().startswith("general_knowledge") or chunk.metadata.get("source_type") == "general_knowledge"
            if is_gk:
                src_type = "general_knowledge"
                cat_label = "GENERAL KNOWLEDGE"
            elif chunk.metadata.get("is_sample"):
                src_type = "sample_policy"
                cat_label = "POLICY"
            else:
                src_type = "user_upload"
                cat_label = "DOCUMENT"

            results.append(SourceItem(
                id=chunk.id,
                doc_id=chunk.doc_id,
                doc_name=chunk.doc_name,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                similarity=round(similarity, 4),
                relevance_tier=tier,
                source_type=src_type,
                category_label=cat_label,
                metadata=chunk.metadata
            ))

            if len(results) >= top_k:
                break

        return results

    def explain_retrieval(self, query: str, results: List[SourceItem]) -> str:
        """Generates dynamic explanation for why results were retrieved."""
        if not results:
            return "No chunks met the minimum similarity confidence threshold."
        
        top_res = results[0]
        types_represented = list(dict.fromkeys(r.category_label for r in results))
        type_summary = " & ".join(types_represented)

        explanation = (
            f"Top evidence from '{top_res.doc_name}' ({top_res.category_label}) achieved {int(top_res.similarity * 100)}% cosine similarity. "
            f"Retrieved {len(results)} evidence passages across [{type_summary}] with an average similarity of "
            f"{int(np.mean([r.similarity for r in results]) * 100)}%."
        )
        return explanation

    def save(self, directory: Path = settings.INDEX_STORAGE_DIR):
        """Persists the index and chunk metadata to disk."""
        directory.mkdir(parents=True, exist_ok=True)
        meta_file = directory / "metadata.json"
        
        data = {
            "chunks": [c.model_dump() for c in self.chunks],
            "dimension": self.dimension
        }
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        if self.embeddings is not None:
            np.save(directory / "embeddings.npy", self.embeddings)

        if self.use_faiss and self.faiss_module is not None and self.faiss_index is not None:
            self.faiss_module.write_index(self.faiss_index, str(directory / "faiss.index"))
        logger.info(f"Persisted {len(self.chunks)} chunks to {directory}")

    def load(self, directory: Path = settings.INDEX_STORAGE_DIR) -> bool:
        """Loads index and metadata from disk if present."""
        meta_file = directory / "metadata.json"
        if not meta_file.exists():
            return False

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.chunks = [ChunkInfo(**c) for c in data.get("chunks", [])]
            self.dimension = data.get("dimension", settings.EMBEDDING_DIMENSION)

            emb_file = directory / "embeddings.npy"
            if emb_file.exists():
                self.embeddings = np.load(emb_file)

            faiss_file = directory / "faiss.index"
            if self.use_faiss and self.faiss_module is not None and faiss_file.exists():
                self.faiss_index = self.faiss_module.read_index(str(faiss_file))

            logger.info(f"Loaded {len(self.chunks)} chunks from {directory}")
            return True
        except Exception as e:
            logger.error(f"Error loading saved index: {e}")
            return False

# Singleton instance
vector_retriever = VectorRetriever()
