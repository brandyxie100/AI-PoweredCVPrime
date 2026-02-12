"""
Application Configuration Manager - Singleton Pattern.

This module implements the Singleton design pattern to ensure only one
configuration instance exists throughout the application lifecycle.
All settings (API keys, model parameters, feature flags) are loaded
once from environment variables and shared across all services.

Design Pattern: Singleton
    - Guarantees a single source of truth for configuration.
    - Thread-safe via Python's module-level import mechanism.
    - Lazy initialization: config is loaded only when first accessed.

Usage:
    from app.config import AppConfig
    config = AppConfig()          # Always returns the SAME instance
    llm = config.get_llm()        # Pre-configured ChatAnthropic
"""

from __future__ import annotations

import logging
import os
from typing import ClassVar

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_openai import OpenAIEmbeddings

# ---------------------------------------------------------------------------
# Load .env file so secrets never appear in source code
# ---------------------------------------------------------------------------
load_dotenv()

logger = logging.getLogger(__name__)


class AppConfig:
    """
    Singleton configuration manager for the CV Analysis application.

    Attributes:
        anthropic_api_key : str  – Anthropic API key (from ANTHROPIC_API_KEY).
        openai_api_key    : str  – OpenAI API key for embeddings (from OPENAI_API_KEY).
        model_name        : str  – Claude model identifier (default: claude-sonnet-4-20250514).
        temperature       : float – LLM creativity parameter (default: 0.3).
        chunk_size        : int   – Characters per text chunk (default: 1000).
        chunk_overlap     : int   – Overlap between consecutive chunks (default: 200).

    How the Singleton works:
        1.  ``_instance`` is a class variable that holds the single object.
        2.  ``__new__`` checks if ``_instance`` already exists.
        3.  If not, it creates a new instance and stores it in ``_instance``.
        4.  Subsequent calls to ``AppConfig()`` return the **same** object.
    """

    # ------------------------------------------------------------------
    # Singleton machinery
    # ------------------------------------------------------------------
    _instance: ClassVar[AppConfig | None] = None

    def __new__(cls) -> AppConfig:
        """Return the existing instance or create one (Singleton)."""
        if cls._instance is None:
            logger.info("Creating new AppConfig singleton instance.")
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False  # guard for __init__
        return cls._instance

    def __init__(self) -> None:
        """Load configuration from environment variables (runs once)."""
        if self._initialized:
            return  # Skip re-initialization on subsequent calls

        # ---- API keys (loaded from .env) ----
        self.anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

        # ---- LLM settings ----
        self.model_name: str = os.getenv("MODEL_NAME", "claude-sonnet-4-20250514")
        self.temperature: float = float(os.getenv("TEMPERATURE", "0.3"))
        self.max_tokens: int = int(os.getenv("MAX_TOKENS", "4096"))

        # ---- Text-splitting settings ----
        self.chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))

        # ---- Application settings ----
        self.upload_dir: str = os.getenv("UPLOAD_DIR", "/tmp/cv_uploads")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)

        self._initialized = True
        logger.info("AppConfig initialized — model=%s, temp=%.1f", self.model_name, self.temperature)

    # ------------------------------------------------------------------
    # Factory-style helpers that return pre-configured LangChain objects
    # ------------------------------------------------------------------

    def get_llm(self) -> ChatAnthropic:
        """
        Return a pre-configured ChatAnthropic LLM instance.

        This is the primary language model used for CV analysis,
        information extraction, and recommendation generation.
        """
        return ChatAnthropic(
            model=self.model_name,
            anthropic_api_key=self.anthropic_api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    def get_embeddings(self) -> OpenAIEmbeddings:
        """
        Return a pre-configured OpenAI embeddings model.

        Used by the FAISS vector store to embed CV text chunks
        and job-role descriptions for semantic similarity matching.
        """
        return OpenAIEmbeddings(
            openai_api_key=self.openai_api_key,
            model="text-embedding-3-small",
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (useful for testing)."""
        cls._instance = None

    def __repr__(self) -> str:
        return (
            f"AppConfig(model={self.model_name!r}, "
            f"temperature={self.temperature}, "
            f"chunk_size={self.chunk_size})"
        )
