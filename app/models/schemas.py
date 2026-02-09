"""
Pydantic Schemas for request / response data validation.

Author: brandyxie
Email:  brandyxie100@qq.com

These models enforce strict type checking on every API boundary,
ensuring that the FastAPI endpoints receive well-formed data and
return predictable JSON structures to the client.

Key models:
    CVUploadResponse  – returned after a CV file is uploaded.
    CVAnalysisResult  – the full analysis payload (skills, experience,
                        job matches, recommendations).
    AgentQueryRequest – body for the free-form agent chat endpoint.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class FileType(str, Enum):
    """Supported CV file formats."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"


class SkillLevel(str, Enum):
    """Proficiency levels for extracted skills."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


# ---------------------------------------------------------------------------
# Sub-models (used inside the main response)
# ---------------------------------------------------------------------------

class ExtractedSkill(BaseModel):
    """A single skill extracted from the CV."""
    name: str = Field(..., description="Skill name, e.g. 'Python'")
    level: SkillLevel = Field(default=SkillLevel.INTERMEDIATE, description="Estimated proficiency")
    years: Optional[float] = Field(default=None, description="Years of experience, if detectable")


class WorkExperience(BaseModel):
    """A single work-experience entry extracted from the CV."""
    title: str = Field(..., description="Job title")
    company: str = Field(default="Unknown", description="Company / organisation name")
    duration: str = Field(default="Unknown", description="Duration string, e.g. '2019-2022'")
    domain: str = Field(default="General", description="Industry domain, e.g. 'FinTech'")
    highlights: list[str] = Field(default_factory=list, description="Key achievements / bullet points")


class Education(BaseModel):
    """A single education entry extracted from the CV."""
    degree: str = Field(..., description="Degree title, e.g. 'MSc Computer Science'")
    institution: str = Field(default="Unknown", description="University / school name")
    year: str = Field(default="Unknown", description="Graduation year or range")


class JobMatch(BaseModel):
    """A matched job role with a similarity score."""
    role: str = Field(..., description="Matched job title")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity 0–1")
    reason: str = Field(default="", description="Why this role matches the candidate")


class Recommendation(BaseModel):
    """A single actionable improvement recommendation."""
    category: str = Field(..., description="Category, e.g. 'Skills Gap', 'Formatting'")
    suggestion: str = Field(..., description="Concrete actionable advice")
    priority: str = Field(default="medium", description="Priority: low / medium / high")


# ---------------------------------------------------------------------------
# Top-level request / response models
# ---------------------------------------------------------------------------

class CVUploadResponse(BaseModel):
    """Returned immediately after uploading a CV file."""
    file_id: str = Field(..., description="Unique ID assigned to the uploaded CV")
    filename: str = Field(..., description="Original filename")
    file_type: FileType
    char_count: int = Field(..., description="Total characters extracted from the CV")
    message: str = Field(default="CV uploaded and text extracted successfully.")


class CVAnalysisResult(BaseModel):
    """
    The complete CV analysis payload.

    Returned by the ``/analyze/{file_id}`` endpoint after the full
    load → chunk → extract → match → recommend pipeline completes.
    """
    file_id: str
    candidate_name: str = Field(default="Unknown")
    email: str = Field(default="")
    summary: str = Field(default="", description="One-paragraph professional summary")
    skills: list[ExtractedSkill] = Field(default_factory=list)
    experience: list[WorkExperience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    job_matches: list[JobMatch] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    overall_score: float = Field(default=0.0, ge=0.0, le=100.0, description="CV quality score 0–100")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class AgentQueryRequest(BaseModel):
    """Body for the /agent/query endpoint (free-form chat)."""
    file_id: str = Field(..., description="The file_id of a previously uploaded CV")
    question: str = Field(..., description="Free-form question about the CV")


class AgentQueryResponse(BaseModel):
    """Response from the LangChain agent."""
    answer: str
    sources: list[str] = Field(default_factory=list, description="Source chunks used")
    tool_calls: list[str] = Field(default_factory=list, description="Tools the agent invoked")


class HealthResponse(BaseModel):
    """Health-check response."""
    status: str = "healthy"
    version: str = "2.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
