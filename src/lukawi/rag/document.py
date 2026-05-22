"""Document loader with sentence-boundary chunking and encoding fallback.

Provides DocumentChunk dataclass and DocumentLoader for reading
.txt / .md files, splitting text on sentence boundaries with
configurable overlap, and producing chunks with UUID identifiers.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from lukawi.rag.exceptions import DocumentLoadError


@dataclass
class DocumentChunk:
    """A single chunk of document text with metadata."""

    id: str
    content: str
    source_path: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)


class DocumentLoader:
    """Load documents from files with encoding fallback and sentence-boundary chunking.

    Parameters
    ----------
    chunk_size : int
        Target number of *tokens* per chunk (default 500).
    chunk_overlap : int
        Number of *tokens* of overlap between consecutive chunks (default 50).
    """

    # Encoding fallback chain – tried in order until one succeeds
    ENCODINGS: list[str] = ["utf-8", "gbk", "gb2312", "latin-1"]

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_file(self, file_path: str | Path) -> list[DocumentChunk]:
        """Load a single file and split into chunks.

        Raises
        ------
        DocumentLoadError
            If *file_path* does not exist, is not a file, or cannot be read.
        """
        path = Path(file_path)

        if not path.exists():
            raise DocumentLoadError(f"文件不存在: {path}")
        if not path.is_file():
            raise DocumentLoadError(f"路径不是文件: {path}")

        text = self._read_file(path)
        return self._split_text(text, source_path=str(path))

    def load_directory(self, dir_path: str | Path) -> list[DocumentChunk]:
        """Load all supported files from a directory.

        Supported extensions: ``.txt``, ``.md``, ``.markdown``.

        Raises
        ------
        DocumentLoadError
            If *dir_path* does not exist or is not a directory.
        """
        path = Path(dir_path)

        if not path.exists():
            raise DocumentLoadError(f"目录不存在: {path}")
        if not path.is_dir():
            raise DocumentLoadError(f"路径不是目录: {path}")

        chunks: list[DocumentChunk] = []
        allowed = {".txt", ".md", ".markdown"}

        for file_path in sorted(path.rglob("*")):
            if file_path.is_file() and file_path.suffix.lower() in allowed:
                chunks.extend(self.load_file(file_path))

        return chunks

    # ------------------------------------------------------------------
    # File reading with encoding fallback
    # ------------------------------------------------------------------

    def _read_file(self, path: Path) -> str:
        """Read file contents, trying each encoding in :attr:`ENCODINGS`."""
        last_error: Exception | None = None

        for enc in self.ENCODINGS:
            try:
                return path.read_text(encoding=enc)
            except (UnicodeDecodeError, UnicodeError) as exc:
                last_error = exc
                continue

        raise DocumentLoadError(
            f"无法解码文件 {path}，已尝试编码: {', '.join(self.ENCODINGS)}",
            cause=last_error,
        )

    # ------------------------------------------------------------------
    # Text splitting
    # ------------------------------------------------------------------

    def _split_text(self, text: str, source_path: str) -> list[DocumentChunk]:
        """Split *text* into chunks respecting sentence boundaries.

        1. Split paragraphs on ``\\n\\n``.
        2. Within each paragraph split on sentence boundaries ``[。！？\\n]``.
        3. Merge small consecutive sentences that fit within ``chunk_size`` tokens.
        4. If a merged group still exceeds ``chunk_size``, split it with overlap.
        """
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        sentences: list[str] = []

        for para in paragraphs:
            sentences.extend(self._split_sentences(para))

        if not sentences:
            return []

        groups = self._merge_small(sentences)
        chunks = self._build_chunks(groups, source_path)
        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        """Split *text* on sentence-end markers ``。！？`` and newlines.

        Each delimiter is attached to the sentence that precedes it.
        Empty strings are filtered out.
        """
        parts = re.split(r"(?<=[。！？\n])", text)
        return [s.strip() for s in parts if s.strip()]

    # ------------------------------------------------------------------
    # Token estimation
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Rough token-count heuristic.

        * Chinese / CJK characters → ~1.5 chars per token.
        * Other text → ~4 chars per token.
        """
        cjk = 0
        other = 0
        for ch in text:
            if "\u4e00" <= ch <= "\u9fff" or "\u3000" <= ch <= "\u303f":
                cjk += 1
            else:
                other += 1
        return int(cjk / 1.5 + other / 4)

    # ------------------------------------------------------------------
    # Grouping & chunking helpers
    # ------------------------------------------------------------------

    def _merge_small(self, sentences: list[str]) -> list[str]:
        """Merge consecutive sentences into groups that fit within ``chunk_size``."""
        groups: list[str] = []
        buf: list[str] = []
        buf_tokens = 0

        for sent in sentences:
            sent_tokens = self._estimate_tokens(sent)
            if buf_tokens + sent_tokens <= self.chunk_size:
                buf.append(sent)
                buf_tokens += sent_tokens
            else:
                if buf:
                    groups.append("".join(buf))
                buf = [sent]
                buf_tokens = sent_tokens

        if buf:
            groups.append("".join(buf))

        return groups

    def _build_chunks(self, groups: list[str], source_path: str) -> list[DocumentChunk]:
        """Build final chunks, splitting oversized groups with overlap."""
        chunks: list[DocumentChunk] = []
        idx = 0

        for group in groups:
            if self._estimate_tokens(group) <= self.chunk_size:
                chunks.append(self._make_chunk(group, source_path, idx))
                idx += 1
            else:
                # Oversized group → split with overlap
                oversize_chunks = self._split_oversized(group)
                for ch in oversize_chunks:
                    chunks.append(self._make_chunk(ch, source_path, idx))
                    idx += 1

        return chunks

    def _split_oversized(self, group: str) -> list[str]:
        """Split a group that exceeds ``chunk_size`` using sentence boundaries."""
        sentences = self._split_sentences(group)
        sub_chunks: list[str] = []
        current: list[str] = []
        current_tokens = 0

        for sent in sentences:
            st = self._estimate_tokens(sent)
            if current_tokens + st <= self.chunk_size:
                current.append(sent)
                current_tokens += st
            else:
                if current:
                    sub_chunks.append("".join(current))
                current = [sent]
                current_tokens = st

        if current:
            sub_chunks.append("".join(current))

        # Apply overlap
        if self.chunk_overlap > 0 and len(sub_chunks) > 1:
            sub_chunks = self._apply_overlap(sub_chunks)

        return sub_chunks

    def _apply_overlap(self, sub_chunks: list[str]) -> list[str]:
        """Prepend tail sentences of previous chunk as overlap."""
        result: list[str] = [sub_chunks[0]]
        for i in range(1, len(sub_chunks)):
            overlap_text = self._get_overlap(result[i - 1])
            if overlap_text:
                result.append(overlap_text + sub_chunks[i])
            else:
                result.append(sub_chunks[i])
        return result

    def _get_overlap(self, text: str) -> str:
        """Return tail sentences of *text* up to ``chunk_overlap`` tokens."""
        sentences = self._split_sentences(text)
        tail: list[str] = []
        tokens = 0
        for sent in reversed(sentences):
            st = self._estimate_tokens(sent)
            if tokens + st > self.chunk_overlap:
                break
            tail.append(sent)
            tokens += st
        tail.reverse()
        return "".join(tail)

    # ------------------------------------------------------------------
    # Chunk factory
    # ------------------------------------------------------------------

    def _make_chunk(
        self,
        content: str,
        source_path: str,
        chunk_index: int,
    ) -> DocumentChunk:
        """Create a :class:`DocumentChunk` with a UUID identifier."""
        return DocumentChunk(
            id=str(uuid.uuid4()),
            content=content.strip(),
            source_path=source_path,
            chunk_index=chunk_index,
            metadata={},
        )
