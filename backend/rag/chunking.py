import re
import hashlib
import logging
from typing import List, Dict, Any
from backend.models.schemas import ChunkInfo

logger = logging.getLogger(__name__)


def generate_chunk_id(doc_id: str, chunk_index: int, content: str) -> str:
    content_hash = hashlib.md5(content[:200].encode("utf-8")).hexdigest()[:8]
    return f"{doc_id}_chunk{chunk_index}_{content_hash}"


class ChunkingEngine:

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        sentence_end = re.compile(r'(?<=[.!?।॥])\s+')
        raw_sentences = sentence_end.split(text.strip())
        sentences = []
        for s in raw_sentences:
            s_clean = s.strip()
            if s_clean:
                sentences.append(s_clean)
        return sentences

    @staticmethod
    def chunk_fixed(
        text: str,
        doc_id: str,
        doc_name: str,
        chunk_size: int = 450,
        chunk_overlap: int = 80,
        metadata: Dict[str, Any] = None
    ) -> List[ChunkInfo]:
        """Fixed-size chunking with word-boundary snapping."""
        metadata = metadata or {}
        chunks: List[ChunkInfo] = []
        text = text.strip()
        if not text:
            return chunks

        start = 0
        index = 0

        while start < len(text):
            end = start + chunk_size
            if end < len(text):
                space_pos = text.rfind(" ", start, end)
                if space_pos > start:
                    end = space_pos + 1
            
            chunk_content = text[start:end].strip()
            if chunk_content:
                chunks.append(ChunkInfo(
                    id=generate_chunk_id(doc_id, index, chunk_content),
                    doc_id=doc_id,
                    doc_name=doc_name,
                    chunk_index=index,
                    content=chunk_content,
                    char_count=len(chunk_content),
                    metadata={
                        **metadata,
                        "strategy": "fixed",
                        "start_offset": start,
                        "end_offset": end
                    }
                ))
                index += 1
            
            start = end - chunk_overlap
            if start >= len(text):
                break

        return chunks

    @staticmethod
    def chunk_sentence(
        text: str,
        doc_id: str,
        doc_name: str,
        chunk_size: int = 450,
        chunk_overlap: int = 80,
        metadata: Dict[str, Any] = None
    ) -> List[ChunkInfo]:
        """Sentence-based chunking that groups complete sentences up to chunk_size."""
        metadata = metadata or {}
        sentences = ChunkingEngine._split_into_sentences(text)
        if not sentences:
            return ChunkingEngine.chunk_fixed(text, doc_id, doc_name, chunk_size, chunk_overlap, metadata)

        chunks: List[ChunkInfo] = []
        current_sentences: List[str] = []
        current_len = 0
        index = 0

        for s in sentences:
            s_len = len(s)
            if s_len > chunk_size and not current_sentences:
                sub_chunks = ChunkingEngine.chunk_fixed(s, doc_id, doc_name, chunk_size, chunk_overlap, metadata)
                for sc in sub_chunks:
                    sc.chunk_index = index
                    sc.id = generate_chunk_id(doc_id, index, sc.content)
                    sc.metadata["strategy"] = "sentence-fallback"
                    chunks.append(sc)
                    index += 1
                continue

            if current_len + s_len + 1 > chunk_size and current_sentences:
                chunk_content = " ".join(current_sentences).strip()
                chunks.append(ChunkInfo(
                    id=generate_chunk_id(doc_id, index, chunk_content),
                    doc_id=doc_id,
                    doc_name=doc_name,
                    chunk_index=index,
                    content=chunk_content,
                    char_count=len(chunk_content),
                    metadata={
                        **metadata,
                        "strategy": "sentence",
                        "sentence_count": len(current_sentences)
                    }
                ))
                index += 1

                overlap_sentences = []
                overlap_len = 0
                for prev_s in reversed(current_sentences):
                    if overlap_len + len(prev_s) <= chunk_overlap:
                        overlap_sentences.insert(0, prev_s)
                        overlap_len += len(prev_s)
                    else:
                        break

                current_sentences = overlap_sentences + [s]
                current_len = sum(len(x) + 1 for x in current_sentences)
            else:
                current_sentences.append(s)
                current_len += s_len + 1

        if current_sentences:
            chunk_content = " ".join(current_sentences).strip()
            chunks.append(ChunkInfo(
                id=generate_chunk_id(doc_id, index, chunk_content),
                doc_id=doc_id,
                doc_name=doc_name,
                chunk_index=index,
                content=chunk_content,
                char_count=len(chunk_content),
                metadata={
                    **metadata,
                    "strategy": "sentence",
                    "sentence_count": len(current_sentences)
                }
            ))

        return chunks

    @staticmethod
    def chunk_recursive(
        text: str,
        doc_id: str,
        doc_name: str,
        chunk_size: int = 450,
        chunk_overlap: int = 80,
        metadata: Dict[str, Any] = None
    ) -> List[ChunkInfo]:
        """
        Recursive hierarchical chunking:
        Splits by paragraphs, then lines, then sentences, then words.
        """
        metadata = metadata or {}
        separators = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]

        def _split_text(t: str, seps: List[str]) -> List[str]:
            if not t.strip():
                return []
            if not seps or len(t) <= chunk_size:
                return [t]

            sep = seps[0]
            if sep == "":
                return [t[i:i + chunk_size] for i in range(0, len(t), chunk_size - chunk_overlap)]

            if sep in [". ", "? ", "! "]:
                parts = re.split(rf'(?<=[{sep[0]}])\s+', t)
            else:
                parts = t.split(sep)

            result = []
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                if len(part) <= chunk_size:
                    result.append(part)
                else:
                    result.extend(_split_text(part, seps[1:]))
            return result

        raw_pieces = _split_text(text, separators)
        
        chunks: List[ChunkInfo] = []
        current_pieces: List[str] = []
        current_len = 0
        index = 0

        for piece in raw_pieces:
            piece_len = len(piece)
            if current_len + piece_len + 1 > chunk_size and current_pieces:
                chunk_content = " ".join(current_pieces).strip()
                chunks.append(ChunkInfo(
                    id=generate_chunk_id(doc_id, index, chunk_content),
                    doc_id=doc_id,
                    doc_name=doc_name,
                    chunk_index=index,
                    content=chunk_content,
                    char_count=len(chunk_content),
                    metadata={
                        **metadata,
                        "strategy": "recursive",
                        "piece_count": len(current_pieces)
                    }
                ))
                index += 1

                overlap_pieces = []
                overlap_len = 0
                for prev_p in reversed(current_pieces):
                    if overlap_len + len(prev_p) <= chunk_overlap:
                        overlap_pieces.insert(0, prev_p)
                        overlap_len += len(prev_p)
                    else:
                        break

                current_pieces = overlap_pieces + [piece]
                current_len = sum(len(x) + 1 for x in current_pieces)
            else:
                current_pieces.append(piece)
                current_len += piece_len + 1

        if current_pieces:
            chunk_content = " ".join(current_pieces).strip()
            chunks.append(ChunkInfo(
                id=generate_chunk_id(doc_id, index, chunk_content),
                doc_id=doc_id,
                doc_name=doc_name,
                chunk_index=index,
                content=chunk_content,
                char_count=len(chunk_content),
                metadata={
                    **metadata,
                    "strategy": "recursive",
                    "piece_count": len(current_pieces)
                }
            ))

        return chunks

    @staticmethod
    def chunk_semantic(
        text: str,
        doc_id: str,
        doc_name: str,
        chunk_size: int = 450,
        chunk_overlap: int = 80,
        metadata: Dict[str, Any] = None,
        similarity_threshold: float = 0.5
    ) -> List[ChunkInfo]:
        """
        Semantic chunking: splits at topic boundaries detected by embedding similarity.
        1. Split text into sentences.
        2. Embed each sentence.
        3. Break where consecutive-sentence cosine similarity drops below threshold.
        4. Merge resulting segments up to chunk_size.
        """
        metadata = metadata or {}
        sentences = ChunkingEngine._split_into_sentences(text)
        
        if len(sentences) < 3:
            return ChunkingEngine.chunk_recursive(
                text, doc_id, doc_name, chunk_size, chunk_overlap, metadata
            )

        # Lazy import to avoid circular dependency
        from backend.rag.embeddings import embedding_engine
        import numpy as np

        try:
            embeddings = embedding_engine.embed_texts(sentences)
        except Exception as e:
            logger.warning(f"Semantic chunking embedding failed: {e}. Falling back to recursive.")
            return ChunkingEngine.chunk_recursive(
                text, doc_id, doc_name, chunk_size, chunk_overlap, metadata
            )

        # Compute cosine similarities between consecutive sentences
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = float(np.dot(embeddings[i], embeddings[i + 1]))
            similarities.append(sim)

        # Find break points where similarity drops below threshold
        break_points = [0]
        for i, sim in enumerate(similarities):
            if sim < similarity_threshold:
                break_points.append(i + 1)
        break_points.append(len(sentences))

        # Build segments from break points
        segments = []
        for i in range(len(break_points) - 1):
            start_idx = break_points[i]
            end_idx = break_points[i + 1]
            segment_text = " ".join(sentences[start_idx:end_idx]).strip()
            if segment_text:
                segments.append(segment_text)

        # Merge segments up to chunk_size
        chunks: List[ChunkInfo] = []
        current_segments: List[str] = []
        current_len = 0
        index = 0

        for seg in segments:
            seg_len = len(seg)
            if current_len + seg_len + 1 > chunk_size and current_segments:
                chunk_content = " ".join(current_segments).strip()
                chunks.append(ChunkInfo(
                    id=generate_chunk_id(doc_id, index, chunk_content),
                    doc_id=doc_id,
                    doc_name=doc_name,
                    chunk_index=index,
                    content=chunk_content,
                    char_count=len(chunk_content),
                    metadata={
                        **metadata,
                        "strategy": "semantic",
                        "segment_count": len(current_segments),
                        "similarity_threshold": similarity_threshold
                    }
                ))
                index += 1
                current_segments = [seg]
                current_len = seg_len
            else:
                current_segments.append(seg)
                current_len += seg_len + 1

        if current_segments:
            chunk_content = " ".join(current_segments).strip()
            chunks.append(ChunkInfo(
                id=generate_chunk_id(doc_id, index, chunk_content),
                doc_id=doc_id,
                doc_name=doc_name,
                chunk_index=index,
                content=chunk_content,
                char_count=len(chunk_content),
                metadata={
                    **metadata,
                    "strategy": "semantic",
                    "segment_count": len(current_segments),
                    "similarity_threshold": similarity_threshold
                }
            ))

        return chunks if chunks else ChunkingEngine.chunk_recursive(
            text, doc_id, doc_name, chunk_size, chunk_overlap, metadata
        )

    @classmethod
    def chunk_document(
        cls,
        text: str,
        doc_id: str,
        doc_name: str,
        strategy: str = "recursive",
        chunk_size: int = 450,
        chunk_overlap: int = 80,
        metadata: Dict[str, Any] = None
    ) -> List[ChunkInfo]:
        strategy = (strategy or "recursive").lower()
        if strategy == "fixed":
            return cls.chunk_fixed(text, doc_id, doc_name, chunk_size, chunk_overlap, metadata)
        elif strategy == "sentence":
            return cls.chunk_sentence(text, doc_id, doc_name, chunk_size, chunk_overlap, metadata)
        elif strategy == "semantic":
            return cls.chunk_semantic(text, doc_id, doc_name, chunk_size, chunk_overlap, metadata)
        else:
            return cls.chunk_recursive(text, doc_id, doc_name, chunk_size, chunk_overlap, metadata)
