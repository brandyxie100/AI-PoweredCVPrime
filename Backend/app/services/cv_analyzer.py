"""
CV Analyzer — Main Orchestrator (Pipeline / Workflow).

This is the **central coordinator** that ties together all pipeline
stages into a single, easy-to-call workflow:

    load → chunk → extract → match → recommend

Each stage is handled by a dedicated service:
    1. **Load**      → ``DocumentLoaderFactory``  (Factory pattern)
    2. **Chunk**     → ``TextChunker``            (LangChain splitter)
    3. **Extract**   → ``CVExtractorService``     (LangChain structured output)
    4. **Match**     → ``JobMatcherService``      (FAISS vector store)
    5. **Recommend** → ``RecommenderService``     (LCEL chain)

Design:
    - ``CVAnalyzer`` holds references to all services.
    - ``analyze()`` runs the full pipeline and returns a ``CVAnalysisResult``.
    - Each stage is independently testable — you can unit-test
      ``CVExtractorService`` without running the whole pipeline.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from app.models.schemas import CVAnalysisResult, CVUploadResponse, FileType
from app.services.cv_extractor import CVExtractorService
from app.services.document_loader import DocumentLoaderFactory
from app.services.job_matcher import JobMatcherService
from app.services.recommender import RecommenderService
from app.services.text_chunker import TextChunker

logger = logging.getLogger(__name__)


class CVAnalyzer:
    """
    Orchestrates the full CV analysis pipeline.

    Workflow::

        ┌────────┐   ┌────────┐   ┌──────────┐   ┌────────┐   ┌───────────┐
        │  LOAD  │──>│ CHUNK  │──>│ EXTRACT  │──>│ MATCH  │──>│ RECOMMEND │
        └────────┘   └────────┘   └──────────┘   └────────┘   └───────────┘
         Factory      LangChain    Structured     FAISS         LCEL Chain
         Pattern      Splitter     Output         Vector Store

    Usage::

        analyzer = CVAnalyzer()
        upload_resp = analyzer.upload("resume.pdf")
        result = await analyzer.analyze(upload_resp.file_id)
    """

    def __init__(self) -> None:
        # Service instances (composed, not inherited — "favour composition")
        self._chunker = TextChunker()
        self._extractor = CVExtractorService()
        self._matcher = JobMatcherService()
        self._recommender = RecommenderService()

        # In-memory store: file_id → {"path": Path, "text": str, "chunks": [...]}
        self._store: dict[str, dict] = {}

        logger.info("CVAnalyzer orchestrator initialised.")

    # ------------------------------------------------------------------
    # Stage 1: Upload & Load
    # ------------------------------------------------------------------

    def upload(self, file_path: str | Path) -> CVUploadResponse:
        """
        Load a CV file, extract its text, and store it for analysis.

        Uses the **Factory Pattern** — ``DocumentLoaderFactory`` picks
        the right loader (PDF / DOCX / TXT) based on the file extension.

        Args:
            file_path: Path to the CV file on disk.

        Returns:
            ``CVUploadResponse`` with a unique ``file_id``.
        """
        path = Path(file_path)
        file_id = uuid.uuid4().hex[:12]

        # Factory pattern: create the right loader automatically
        loader = DocumentLoaderFactory.create_loader(path)
        raw_text = loader.load()

        # Determine file type enum
        ext_map = {".pdf": FileType.PDF, ".docx": FileType.DOCX, ".txt": FileType.TXT}
        file_type = ext_map.get(path.suffix.lower(), FileType.TXT)

        # Store for later analysis
        self._store[file_id] = {
            "path": path,
            "text": raw_text,
            "chunks": [],
        }

        logger.info("Uploaded '%s' → file_id=%s (%d chars)", path.name, file_id, len(raw_text))

        return CVUploadResponse(
            file_id=file_id,
            filename=path.name,
            file_type=file_type,
            char_count=len(raw_text),
        )

    # ------------------------------------------------------------------
    # Stages 2–5: Full Analysis Pipeline
    # ------------------------------------------------------------------

    async def analyze(self, file_id: str) -> CVAnalysisResult:
        """
        Run the full analysis pipeline on a previously uploaded CV.

        Pipeline stages:
            1. Retrieve raw text from the store.
            2. **Chunk** — split text into overlapping chunks.
            3. **Extract** — use Claude to extract structured data.
            4. **Match** — embed CV summary and match against job catalogue.
            5. **Recommend** — generate actionable improvement advice.

        Args:
            file_id: The ID returned by ``upload()``.

        Returns:
            ``CVAnalysisResult`` containing all extracted data,
            job matches, and recommendations.
        """
        if file_id not in self._store:
            raise ValueError(f"Unknown file_id: {file_id}")

        entry = self._store[file_id]
        raw_text: str = entry["text"]

        # --- Stage 2: CHUNK ---
        logger.info("[%s] Stage 2 — Chunking text.", file_id)
        chunks = self._chunker.split(raw_text)
        entry["chunks"] = chunks

        # --- Stage 3: EXTRACT ---
        logger.info("[%s] Stage 3 — Extracting structured data.", file_id)
        extraction = await self._extractor.extract(raw_text)

        # --- Stage 4: MATCH ---
        logger.info("[%s] Stage 4 — Matching to job roles.", file_id)
        # Build a query from extracted skills + experience summaries
        query_text = self._build_match_query(extraction)
        job_matches = await self._matcher.match(query_text, top_k=5)

        # --- Stage 5: RECOMMEND ---
        logger.info("[%s] Stage 5 — Generating recommendations.", file_id)
        match_dicts = [m.model_dump() for m in job_matches]
        recommendations = await self._recommender.recommend(extraction, match_dicts)

        # --- Assemble final result ---
        result = CVAnalysisResult(
            file_id=file_id,
            candidate_name=extraction.candidate_name,
            email=extraction.email,
            summary=extraction.summary,
            skills=extraction.skills,
            experience=extraction.experience,
            education=extraction.education,
            job_matches=job_matches,
            recommendations=recommendations,
            overall_score=extraction.overall_quality_score,
        )
        logger.info("[%s] Analysis complete — score=%.1f", file_id, result.overall_score)
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_match_query(extraction) -> str:
        """Build a text query from extracted CV data for FAISS matching."""
        parts: list[str] = []
        if extraction.summary:
            parts.append(extraction.summary)
        if extraction.skills:
            skills = ", ".join(s.name for s in extraction.skills)
            parts.append(f"Skills: {skills}")
        if extraction.experience:
            for exp in extraction.experience[:3]:  # Top 3 experiences
                parts.append(f"{exp.title} at {exp.company}")
        return " | ".join(parts) or "General professional"

    def get_cv_text(self, file_id: str) -> str:
        """Retrieve stored CV text by file_id."""
        if file_id not in self._store:
            raise ValueError(f"Unknown file_id: {file_id}")
        return self._store[file_id]["text"]

    def get_cv_chunks(self, file_id: str) -> list[str]:
        """Retrieve stored CV chunks by file_id."""
        if file_id not in self._store:
            raise ValueError(f"Unknown file_id: {file_id}")
        return self._store[file_id]["chunks"]
