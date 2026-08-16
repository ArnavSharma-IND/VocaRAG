import re
import hashlib
from typing import List, Dict, Any
from backend.models.schemas import ChunkInfo

def generate_chunk_id(doc_id: str, index: int, content: str) -> str:
    hash_str = hashlib.md5(f"{doc_id}_{index}_{content[:50]}".encode("utf-8")).hexdigest()[:8]
    return f"{doc_id}_c{index}_{hash_str}"

class ChunkingEngine:
    """
    Implements multiple configurable text chunking strategies for VocaRAG:
    1. Fixed-Size Chunking with Overlap
    2. Sentence-Based Chunking with Overlap
    3. Recursive Character Chunking
    """

    @staticmethod
    def chunk_fixed(
        text: str,
        doc_id: str,
        doc_name: str,
        chunk_size: int = 450,
        chunk_overlap: int = 80,
        metadata: Dict[str, Any] = None
    ) -> List[ChunkInfo]:
        """Fixed character size chunking respecting word boundaries where possible."""
        metadata = metadata or {}
        cleaned_text = re.sub(r'\s+', ' ', text).strip()
        if not cleaned_text:
            return []

        chunks: List[ChunkInfo] = []
        start = 0
        text_len = len(cleaned_text)
        index = 0

        while start < text_len:
            end = min(start + chunk_size, text_len)
            
            # If not at the end of text, find the nearest space to avoid cutting words
            if end < text_len:
                space_pos = cleaned_text.rfind(' ', start + int(chunk_size * 0.7), end)
                if space_pos != -1 and space_pos > start:
                    end = space_pos

            chunk_content = cleaned_text[start:end].strip()
            if chunk_content:
                chunk_id = generate_chunk_id(doc_id, index, chunk_content)
                chunks.append(ChunkInfo(
                    id=chunk_id,
                    doc_id=doc_id,
                    doc_name=doc_name,
                    chunk_index=index,
                    content=chunk_content,
                    char_count=len(chunk_content),
                    metadata={
                        **metadata,
                        "strategy": "fixed",
                        "start_char": start,
                        "end_char": end,
                        "chunk_size_setting": chunk_size,
                        "overlap_setting": chunk_overlap
                    }
                ))
                index += 1

            if end >= text_len:
                break
            
            start = max(end - chunk_overlap, start + 1)

        return chunks

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        """Splits text into sentences while avoiding false positives on abbreviations/decimals."""
        # Clean multiple spaces while preserving punctuation
        sentence_end = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9"\'\(\[])')
        raw_sentences = sentence_end.split(text.strip())
        sentences = []
        for s in raw_sentences:
            s_clean = s.strip()
            if s_clean:
                sentences.append(s_clean)
        return sentences

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
            # If a single sentence exceeds chunk_size, split it fixed
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
                # Flush current chunk
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

                # Calculate overlap sentences
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
        Splits by paragraphs (\n\n), then lines (\n), then sentences (. ), then words.
        Ensures optimal semantic boundaries with sliding overlap.
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
                # Hard character slice
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
        
        # Merge pieces up to chunk_size with overlap
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

                # Overlap calculation
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
        else:
            return cls.chunk_recursive(text, doc_id, doc_name, chunk_size, chunk_overlap, metadata)
