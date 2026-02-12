"""
CV Information Extractor — LangChain Structured Output.

This module uses **ChatAnthropic** with LangChain's ``with_structured_output``
to extract typed, structured data from raw CV text.  Instead of parsing
free-form LLM prose, we let the model fill a Pydantic schema directly.

Workflow position:  **STEP 3 — EXTRACT**
    load → chunk → extract → match → recommend
                   ^^^^^^^

LangChain Components:
    - ``ChatAnthropic``           – Claude Sonnet as the extraction LLM.
    - ``ChatPromptTemplate``      – Reusable prompt with system + human msgs.
    - ``with_structured_output``  – Forces the model to return data matching
                                    a Pydantic schema (tool-calling under the hood).

How ``with_structured_output`` works:
    1. You pass a Pydantic model (e.g. ``CVExtraction``) to the method.
    2. LangChain translates the schema into a tool definition and instructs
       the LLM to call that tool with the extracted values.
    3. The LLM's response is automatically validated and parsed into a
       Python object — no regex or manual JSON parsing needed.
"""

from __future__ import annotations

import logging
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.config import AppConfig
from app.models.schemas import (
    Education,
    ExtractedSkill,
    SkillLevel,
    WorkExperience,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic schema the LLM must fill (used by with_structured_output)
# ---------------------------------------------------------------------------

class CVExtraction(BaseModel):
    """
    Schema for structured CV extraction.

    The LLM receives the CV text and must populate every field.
    LangChain ensures the output conforms to this model.
    """

    candidate_name: str = Field(..., description="Full name of the candidate")
    email: str = Field(default="", description="Email address if found")
    summary: str = Field(
        ..., description="A concise 2-3 sentence professional summary"
    )
    skills: list[ExtractedSkill] = Field(
        default_factory=list,
        description="List of technical and soft skills with proficiency levels",
    )
    experience: list[WorkExperience] = Field(
        default_factory=list,
        description="Work experience entries in reverse chronological order",
    )
    education: list[Education] = Field(
        default_factory=list,
        description="Education entries",
    )
    overall_quality_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall CV quality score from 0 to 100",
    )


# ---------------------------------------------------------------------------
# Extractor service
# ---------------------------------------------------------------------------

class CVExtractorService:
    """
    Extracts structured information from CV text using Claude Sonnet.

    Usage::

        extractor = CVExtractorService()
        result: CVExtraction = extractor.extract(cv_text)
        print(result.candidate_name, result.skills)
    """

    # System prompt that instructs the model on what to extract
    SYSTEM_PROMPT = (
        "You are an expert HR analyst and CV reviewer. "
        "Given the full text of a CV / resume, extract all relevant "
        "information accurately. Estimate skill proficiency levels "
        "based on the described experience. Score the CV quality "
        "from 0 to 100 considering completeness, clarity, impact "
        "of bullet points, and overall presentation."
    )

    def __init__(self) -> None:
        config = AppConfig()
        self._llm = config.get_llm()

        # Build a reusable ChatPromptTemplate
        self._prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human", "Extract structured information from the following CV:\n\n{cv_text}"),
        ])

        # Chain: prompt → LLM with structured output
        # ``with_structured_output`` converts the Pydantic model into
        # a tool schema so the LLM returns validated JSON automatically.
        self._chain = self._prompt | self._llm.with_structured_output(CVExtraction)

        logger.info("CVExtractorService initialised.")

    async def extract(self, cv_text: str) -> CVExtraction:
        """
        Extract structured CV data from raw text.

        Args:
            cv_text: The full text of the CV.

        Returns:
            A ``CVExtraction`` Pydantic model populated by the LLM.
        """
        logger.info("Extracting structured data from CV (%d chars).", len(cv_text))
        result: CVExtraction = await self._chain.ainvoke({"cv_text": cv_text})
        logger.info(
            "Extraction complete — name=%s, skills=%d, experience=%d",
            result.candidate_name,
            len(result.skills),
            len(result.experience),
        )
        return result
