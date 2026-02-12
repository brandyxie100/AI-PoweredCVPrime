"""
Text Chunker Service — LangChain RecursiveCharacterTextSplitter.

This module wraps LangChain's ``RecursiveCharacterTextSplitter`` to break
large CV text into smaller, overlapping chunks suitable for:
    - Embedding into a FAISS vector store.
    - Feeding into LLM context windows without exceeding token limits.

Workflow position:  **STEP 2 — CHUNK**
    load → chunk → extract → match → recommend
           ^^^^^

LangChain Component:
    ``RecursiveCharacterTextSplitter``
        Splits text by trying a hierarchy of separators (``\\n\\n``,
        ``\\n``, ``  ``, ``""``) to keep semantically related text
        together in each chunk.  Overlap ensures context is preserved
        across chunk boundaries.

Why chunk?
    1. LLMs have finite context windows — chunking prevents truncation.
    2. Vector search is more accurate on focused passages than on
       entire documents.
    3. Overlapping ensures no information is lost at split boundaries.
"""

from __future__ import annotations

import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import AppConfig

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Splits raw CV text into overlapping chunks using LangChain.

    Attributes:
        chunk_size    : int – Target size of each chunk (characters).
        chunk_overlap : int – Number of overlapping characters between
                              consecutive chunks.
        splitter      : RecursiveCharacterTextSplitter – The LangChain
                        splitter instance.
    """

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        """
        Initialise the chunker.

        If ``chunk_size`` / ``chunk_overlap`` are not provided, they are
        pulled from the ``AppConfig`` singleton (which reads from ``.env``).
        """
        config = AppConfig()
        self.chunk_size = chunk_size or config.chunk_size
        self.chunk_overlap = chunk_overlap or config.chunk_overlap

        # --- LangChain component: RecursiveCharacterTextSplitter ---
        # Tries these separators in order, falling back to the next if
        # the previous does not produce chunks within the size limit.
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        logger.info(
            "TextChunker ready — chunk_size=%d, overlap=%d",
            self.chunk_size,
            self.chunk_overlap,
        )

    def split(self, text: str) -> list[str]:
        """
        Split raw text into a list of chunk strings.

        Args:
            text: The full CV text to split.

        Returns:
            A list of text chunks (strings).
        """
        chunks = self.splitter.split_text(text)
        logger.info("Split text (%d chars) into %d chunks.", len(text), len(chunks))
        return chunks

    def split_with_metadata(self, text: str, source: str = "cv") -> list[dict]:
        """
        Split text and return dicts with chunk content + metadata.

        Useful for loading directly into the FAISS vector store with
        provenance information attached.

        Args:
            text   : The full CV text.
            source : An identifier for the source document.

        Returns:
            A list of dicts: ``{"content": str, "metadata": {...}}``.
        """
        chunks = self.split(text)
        results = []
        for idx, chunk in enumerate(chunks):
            results.append({
                "content": chunk,
                "metadata": {
                    "source": source,
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                },
            })
        return results
