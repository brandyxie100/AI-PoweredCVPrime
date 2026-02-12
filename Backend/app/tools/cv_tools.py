"""
Custom LangChain Tools for the CV Analysis Agent.

LangChain **Tools** are functions that an Agent can decide to call
autonomously.  Each tool has:
    - A ``name`` : unique identifier the agent uses to select it.
    - A ``description`` : tells the agent *when* and *why* to use it.
    - A callable : the Python function that executes the action.

When the agent receives a question like "What skills does this CV list?",
it reads the tool descriptions, decides which tool to call, passes
arguments, and uses the tool's output to formulate its answer.

LangChain Component:
    ``@tool`` decorator — converts a plain Python function into a
    LangChain ``StructuredTool`` with automatic argument parsing.

How Tools work with Agents:
    1. The agent receives a user question.
    2. It examines all available tools and their descriptions.
    3. It generates a tool call (function name + arguments).
    4. LangChain executes the function and returns the result.
    5. The agent reads the result and either calls another tool
       or writes the final answer.

This "Thought → Action → Observation" loop repeats until the agent
decides it has enough information to answer.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from langchain_core.tools import tool

if TYPE_CHECKING:
    from app.services.cv_analyzer import CVAnalyzer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level reference to the CVAnalyzer — set by the agent service
# ---------------------------------------------------------------------------
_analyzer_ref: CVAnalyzer | None = None


def set_analyzer(analyzer: CVAnalyzer) -> None:
    """Inject the CVAnalyzer instance so tools can access CV data."""
    global _analyzer_ref
    _analyzer_ref = analyzer


def _get_analyzer() -> CVAnalyzer:
    """Retrieve the injected CVAnalyzer (raises if not set)."""
    if _analyzer_ref is None:
        raise RuntimeError("CVAnalyzer not injected. Call set_analyzer() first.")
    return _analyzer_ref


# ---------------------------------------------------------------------------
# Tool 1: Retrieve full CV text
# ---------------------------------------------------------------------------

@tool
def get_cv_full_text(file_id: str) -> str:
    """
    Retrieve the full raw text of a previously uploaded CV.

    Use this tool when you need to read the complete CV content
    to answer questions about specific sections, wording, or details
    not captured in the structured extraction.

    Args:
        file_id: The unique identifier of the uploaded CV.

    Returns:
        The full text of the CV as a string.
    """
    logger.info("Tool: get_cv_full_text called for file_id=%s", file_id)
    analyzer = _get_analyzer()
    text = analyzer.get_cv_text(file_id)
    # Truncate if extremely long to fit in agent context
    if len(text) > 8000:
        return text[:8000] + "\n\n... [truncated for brevity]"
    return text


# ---------------------------------------------------------------------------
# Tool 2: Retrieve chunked CV text
# ---------------------------------------------------------------------------

@tool
def get_cv_chunks(file_id: str) -> str:
    """
    Retrieve the chunked version of a CV (split into smaller pieces).

    Use this tool when you need to examine individual sections or
    paragraphs of the CV separately.

    Args:
        file_id: The unique identifier of the uploaded CV.

    Returns:
        A formatted string showing each chunk with its index.
    """
    logger.info("Tool: get_cv_chunks called for file_id=%s", file_id)
    analyzer = _get_analyzer()
    chunks = analyzer.get_cv_chunks(file_id)
    formatted = []
    for i, chunk in enumerate(chunks):
        formatted.append(f"--- Chunk {i + 1}/{len(chunks)} ---\n{chunk}")
    return "\n\n".join(formatted)


# ---------------------------------------------------------------------------
# Tool 3: Search for specific information in the CV
# ---------------------------------------------------------------------------

@tool
def search_cv_section(file_id: str, query: str) -> str:
    """
    Search for specific information within a CV.

    Use this tool when the user asks about a specific topic (e.g.,
    "Does the CV mention Python?" or "What certifications are listed?").
    It searches through the CV chunks and returns the most relevant ones.

    Args:
        file_id: The unique identifier of the uploaded CV.
        query: The search query (e.g., "certifications", "Python experience").

    Returns:
        Matching chunks from the CV, or a message if nothing found.
    """
    logger.info("Tool: search_cv_section — file_id=%s, query='%s'", file_id, query)
    analyzer = _get_analyzer()
    chunks = analyzer.get_cv_chunks(file_id)

    query_lower = query.lower()
    matches = [
        chunk for chunk in chunks
        if query_lower in chunk.lower()
    ]

    if matches:
        return f"Found {len(matches)} matching section(s):\n\n" + "\n---\n".join(matches)
    return f"No sections mentioning '{query}' were found in the CV."


# ---------------------------------------------------------------------------
# Tool 4: Provide formatting feedback
# ---------------------------------------------------------------------------

@tool
def analyze_cv_formatting(file_id: str) -> str:
    """
    Analyse the formatting quality of a CV.

    Use this tool to check for common formatting issues such as:
    - Inconsistent bullet points
    - Missing sections (education, skills, experience)
    - Very short or very long CVs
    - Missing contact information patterns

    Args:
        file_id: The unique identifier of the uploaded CV.

    Returns:
        A formatted report of formatting observations.
    """
    logger.info("Tool: analyze_cv_formatting for file_id=%s", file_id)
    analyzer = _get_analyzer()
    text = analyzer.get_cv_text(file_id)

    observations: list[str] = []

    # Length check
    word_count = len(text.split())
    if word_count < 150:
        observations.append(f"⚠️  CV is very short ({word_count} words). Aim for 400-800 words.")
    elif word_count > 1500:
        observations.append(f"⚠️  CV is very long ({word_count} words). Consider condensing to 1-2 pages.")
    else:
        observations.append(f"✅ Length is appropriate ({word_count} words).")

    # Section detection
    text_lower = text.lower()
    expected_sections = ["education", "experience", "skills", "summary", "contact"]
    for section in expected_sections:
        if section in text_lower:
            observations.append(f"✅ '{section.title()}' section detected.")
        else:
            observations.append(f"⚠️  No '{section.title()}' section found — consider adding one.")

    # Email detection
    import re
    if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text):
        observations.append("✅ Email address detected.")
    else:
        observations.append("⚠️  No email address found — essential for contact.")

    # Bullet point consistency
    bullet_types = set()
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped and stripped[0] in "•-*▪►":
            bullet_types.add(stripped[0])
    if len(bullet_types) > 1:
        observations.append(
            f"⚠️  Multiple bullet styles used ({bullet_types}). Pick one for consistency."
        )

    return "\n".join(observations)


# ---------------------------------------------------------------------------
# Collect all tools into a list for the agent
# ---------------------------------------------------------------------------

ALL_CV_TOOLS = [
    get_cv_full_text,
    get_cv_chunks,
    search_cv_section,
    analyze_cv_formatting,
]
