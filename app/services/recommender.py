"""
Recommendation Engine — LangChain Chains & Prompt Engineering.

Generates actionable, specific improvement recommendations for a CV
by combining the extracted structured data with a carefully engineered
prompt chain.

Workflow position:  **STEP 5 — RECOMMEND**
    load → chunk → extract → match → recommend
                                      ^^^^^^^^^

LangChain Components:
    - ``ChatPromptTemplate``  – Constructs the recommendation prompt.
    - ``ChatAnthropic``       – Claude Sonnet generates the recommendations.
    - ``StrOutputParser``     – Parses the LLM response to a plain string.
    - **LCEL (LangChain Expression Language)** – The ``|`` (pipe) operator
      chains prompt → llm → parser into a single runnable.

What is LCEL?
    LCEL lets you compose LangChain components using the pipe ``|``
    operator, similar to Unix pipes::

        chain = prompt | llm | parser

    Each component's output is fed as input to the next.  The chain
    is *lazy* — it only executes when you call ``.invoke()`` or
    ``.ainvoke()``.  This makes it easy to swap components (e.g.
    replace Claude with GPT) without rewriting logic.
"""

from __future__ import annotations

import json
import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.config import AppConfig
from app.models.schemas import Recommendation
from app.services.cv_extractor import CVExtraction

logger = logging.getLogger(__name__)


class RecommenderService:
    """
    Generates actionable CV improvement recommendations.

    The recommendation chain:
        ChatPromptTemplate → ChatAnthropic → StrOutputParser

    The prompt receives the extracted CV data (skills, experience,
    score, job matches) and asks the LLM to produce specific,
    prioritised improvements.

    Usage::

        recommender = RecommenderService()
        recs = await recommender.recommend(extraction, job_matches)
    """

    SYSTEM_PROMPT = (
        "You are an expert career coach who specialises in CV optimisation "
        "for the technology industry.  Given structured information extracted "
        "from a candidate's CV and their top job-role matches, generate "
        "actionable, specific improvement recommendations.\n\n"
        "Rules:\n"
        "- Be concrete: instead of 'add more skills', say *which* skills.\n"
        "- Categorise each recommendation (e.g., Skills Gap, Formatting, "
        "Impact Metrics, Keywords, Summary).\n"
        "- Assign a priority (low / medium / high).\n"
        "- Return ONLY a JSON array of objects, each with keys: "
        "\"category\", \"suggestion\", \"priority\".\n"
        "- Return at least 5 and at most 10 recommendations."
    )

    HUMAN_TEMPLATE = (
        "## Extracted CV Data\n"
        "- **Candidate**: {candidate_name}\n"
        "- **Overall Score**: {score}/100\n"
        "- **Skills**: {skills}\n"
        "- **Experience Summary**: {experience}\n"
        "- **Education**: {education}\n\n"
        "## Top Job Matches\n"
        "{job_matches}\n\n"
        "Generate improvement recommendations as a JSON array."
    )

    def __init__(self) -> None:
        config = AppConfig()
        self._llm = config.get_llm()

        # Build the LCEL chain: prompt → LLM → string parser
        self._prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human", self.HUMAN_TEMPLATE),
        ])
        self._chain = self._prompt | self._llm | StrOutputParser()
        logger.info("RecommenderService initialised with LCEL chain.")

    async def recommend(
        self,
        extraction: CVExtraction,
        job_matches: list[dict] | None = None,
    ) -> list[Recommendation]:
        """
        Generate CV improvement recommendations.

        Args:
            extraction  : Structured CV data from ``CVExtractorService``.
            job_matches : Top job matches (list of dicts with role + score).

        Returns:
            A list of ``Recommendation`` Pydantic models.
        """
        # Format inputs for the prompt template
        skills_str = ", ".join(
            f"{s.name} ({s.level.value})" for s in extraction.skills
        )
        experience_str = "; ".join(
            f"{e.title} at {e.company} ({e.duration})"
            for e in extraction.experience
        )
        education_str = "; ".join(
            f"{ed.degree} — {ed.institution}" for ed in extraction.education
        )
        matches_str = (
            "\n".join(
                f"- {m['role']} (score: {m['similarity_score']})"
                for m in (job_matches or [])
            )
            or "No matches computed yet."
        )

        logger.info("Generating recommendations for %s.", extraction.candidate_name)

        raw_output: str = await self._chain.ainvoke({
            "candidate_name": extraction.candidate_name,
            "score": extraction.overall_quality_score,
            "skills": skills_str or "None extracted",
            "experience": experience_str or "None extracted",
            "education": education_str or "None extracted",
            "job_matches": matches_str,
        })

        # Parse the JSON array from the LLM response
        recommendations = self._parse_recommendations(raw_output)
        logger.info("Generated %d recommendations.", len(recommendations))
        return recommendations

    @staticmethod
    def _parse_recommendations(raw: str) -> list[Recommendation]:
        """
        Parse LLM output (expected JSON array) into Recommendation models.

        Falls back to a single generic recommendation if parsing fails.
        """
        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:])  # Remove opening fence
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        try:
            items = json.loads(cleaned)
            return [Recommendation(**item) for item in items]
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("Failed to parse recommendations JSON: %s", exc)
            # Return the raw text as a single recommendation
            return [
                Recommendation(
                    category="General",
                    suggestion=raw.strip()[:500],
                    priority="medium",
                )
            ]
