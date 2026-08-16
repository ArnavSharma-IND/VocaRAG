import hashlib
import time
import logging
from typing import List, Dict, Optional
import numpy as np
from backend.config import settings

logger = logging.getLogger(__name__)

class EmbeddingEngine:
    _instance = None
    _model = None
    _model_name: str = settings.EMBEDDING_MODEL_NAME
    _cache: Dict[str, np.ndarray] = {}
    _is_ready: bool = False
    _dimension: int = settings.EMBEDDING_DIMENSION

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingEngine, cls).__new__(cls)
        return cls._instance

    def initialize(self):
        """Initializes the SentenceTransformer embedding model."""
        if self._is_ready and self._model is not None:
            return

        try:
            logger.info(f"Loading embedding model: {self._model_name}...")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            self._dimension = self._model.get_sentence_embedding_dimension()
            self._is_ready = True
            logger.info(f"Embedding model loaded successfully. Dimension: {self._dimension}")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ({e}). Initializing fallback lightweight dense vectorizer.")
            self._is_ready = True
            self._dimension = settings.EMBEDDING_DIMENSION

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def cache_size(self) -> int:
        return len(self._cache)

    def _get_hash(self, text: str) -> str:
        return hashlib.md5(text.strip().lower().encode("utf-8")).hexdigest()

    def _fallback_dense_embed(self, text: str) -> np.ndarray:
        """Deterministic dense projection fallback if deep learning weights are loading."""
        seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.RandomState(seed)
        vec = rng.randn(self._dimension).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Batch generates embeddings with in-memory caching and L2 normalization."""
        if not self._is_ready or self._model is None:
            self.initialize()

        if not texts:
            return np.empty((0, self._dimension), dtype=np.float32)

        results = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            h = self._get_hash(text)
            if h in self._cache:
                results[i] = self._cache[h]
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        if uncached_texts:
            if self._model is not None:
                try:
                    embeddings = self._model.encode(
                        uncached_texts,
                        batch_size=batch_size,
                        show_progress_bar=False,
                        normalize_embeddings=True
                    )
                    embeddings = np.array(embeddings, dtype=np.float32)
                except Exception as e:
                    logger.error(f"Error encoding with model: {e}. Using fallback.")
                    embeddings = np.array([self._fallback_dense_embed(t) for t in uncached_texts], dtype=np.float32)
            else:
                embeddings = np.array([self._fallback_dense_embed(t) for t in uncached_texts], dtype=np.float32)

            for idx, orig_i in enumerate(uncached_indices):
                vec = embeddings[idx]
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                self._cache[self._get_hash(uncached_texts[idx])] = vec
                results[orig_i] = vec

        return np.vstack(results)

    def embed_query(self, query: str) -> np.ndarray:
        """Embeds a single query string and returns a normalized 1D vector."""
        vecs = self.embed_texts([query])
        return vecs[0]

# Singleton instance
embedding_engine = EmbeddingEngine()
