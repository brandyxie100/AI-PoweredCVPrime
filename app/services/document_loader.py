"""
Document Loader Service - Factory Pattern.

This module uses the **Factory** design pattern to create the correct
document loader based on the file extension. The caller does not need
to know *which* concrete loader is used — the factory decides.

Design Pattern: Factory Method
    ``DocumentLoaderFactory.create_loader(file_path)``
    inspects the file extension and returns the appropriate
    ``BaseDocumentLoader`` subclass.

Supported formats:
    - PDF  → ``PDFLoader``   (uses pdfplumber for accurate text extraction)
    - DOCX → ``DocxLoader``  (uses python-docx)
    - TXT  → ``TxtLoader``   (plain-text read)

Workflow position:  **STEP 1 — LOAD**
    load → chunk → extract → match → recommend
    ^^^^
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import docx
import pdfplumber

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract base class — all loaders share this interface
# ---------------------------------------------------------------------------

class BaseDocumentLoader(ABC):
    """
    Abstract base class for document loaders.

    Every concrete loader must implement ``load()`` which returns
    the full text content of the document as a single string.
    """

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

    @abstractmethod
    def load(self) -> str:
        """Extract and return the full text from the document."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(file={self.file_path.name})"


# ---------------------------------------------------------------------------
# Concrete loaders
# ---------------------------------------------------------------------------

class PDFLoader(BaseDocumentLoader):
    """Extract text from a PDF file using pdfplumber."""

    def load(self) -> str:
        logger.info("Loading PDF: %s", self.file_path.name)
        pages: list[str] = []
        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        full_text = "\n\n".join(pages).strip()
        logger.info("Extracted %d characters from PDF.", len(full_text))
        return full_text


class DocxLoader(BaseDocumentLoader):
    """Extract text from a DOCX file using python-docx."""

    def load(self) -> str:
        logger.info("Loading DOCX: %s", self.file_path.name)
        doc = docx.Document(str(self.file_path))
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        full_text = "\n".join(paragraphs).strip()
        logger.info("Extracted %d characters from DOCX.", len(full_text))
        return full_text


class TxtLoader(BaseDocumentLoader):
    """Read a plain-text file."""

    def load(self) -> str:
        logger.info("Loading TXT: %s", self.file_path.name)
        full_text = self.file_path.read_text(encoding="utf-8").strip()
        logger.info("Extracted %d characters from TXT.", len(full_text))
        return full_text


# ---------------------------------------------------------------------------
# Factory — the single entry-point for creating loaders
# ---------------------------------------------------------------------------

class DocumentLoaderFactory:
    """
    Factory that returns the correct loader for a given file path.

    Usage::

        loader = DocumentLoaderFactory.create_loader("resume.pdf")
        text   = loader.load()

    How the Factory Pattern works here:
        1. The client calls ``create_loader(file_path)`` — a *static* method.
        2. The factory inspects the file extension.
        3. It instantiates and returns the matching ``BaseDocumentLoader``
           subclass (``PDFLoader``, ``DocxLoader``, or ``TxtLoader``).
        4. The client never imports or references the concrete class.

    Benefits:
        - Adding a new format only requires a new loader class +
          one entry in ``_LOADERS``.  No client code changes needed.
        - All loaders share a common ``load()`` interface (polymorphism).
    """

    # Registry mapping extension → concrete loader class
    _LOADERS: dict[str, type[BaseDocumentLoader]] = {
        ".pdf": PDFLoader,
        ".docx": DocxLoader,
        ".txt": TxtLoader,
    }

    @staticmethod
    def create_loader(file_path: str | Path) -> BaseDocumentLoader:
        """
        Create and return the appropriate document loader.

        Args:
            file_path: Path to the CV file.

        Returns:
            A ``BaseDocumentLoader`` instance ready to call ``.load()``.

        Raises:
            ValueError: If the file extension is not supported.
            FileNotFoundError: If the file does not exist.
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        loader_cls = DocumentLoaderFactory._LOADERS.get(suffix)

        if loader_cls is None:
            supported = ", ".join(DocumentLoaderFactory._LOADERS.keys())
            raise ValueError(
                f"Unsupported file format '{suffix}'. "
                f"Supported formats: {supported}"
            )

        logger.info("Factory selected %s for '%s'.", loader_cls.__name__, path.name)
        return loader_cls(path)

    @classmethod
    def supported_formats(cls) -> list[str]:
        """Return a list of supported file extensions."""
        return list(cls._LOADERS.keys())
