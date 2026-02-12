"""
FastAPI Application — CV Analysis API.

This is the entry-point for the web application.  It exposes RESTful
endpoints for:
    1. ``POST /upload``          – Upload a CV file (PDF / DOCX / TXT).
    2. ``GET  /analyze/{id}``    – Run the full analysis pipeline.
    3. ``POST /agent/query``     – Ask a free-form question via the agent.
    4. ``GET  /health``          – Health check.

Architecture:
    - ``CVAnalyzer`` (the orchestrator) is created once at startup.
    - ``CVAgentService`` wraps a LangChain ReAct agent for Q&A.
    - Both are stored in ``app.state`` so they persist across requests.

Run locally:
    uvicorn app.main:app --reload --port 8000

Run via Docker:
    docker compose up --build
"""

from __future__ import annotations

import logging
import shutil
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import AppConfig
from app.models.schemas import (
    AgentQueryRequest,
    AgentQueryResponse,
    CVAnalysisResult,
    CVUploadResponse,
    HealthResponse,
)
from app.services.agent import CVAgentService
from app.services.cv_analyzer import CVAnalyzer

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — initialise services once at startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Runs on startup:
        - Creates the ``AppConfig`` singleton.
        - Initialises the ``CVAnalyzer`` orchestrator.
        - Initialises the ``CVAgentService``.

    On shutdown:
        - Releases resources (if any).
    """
    logger.info("🚀 Starting CV Analysis API v2.0 ...")
    config = AppConfig()
    logger.info("Config: %r", config)

    # Create the main orchestrator
    analyzer = CVAnalyzer()
    app.state.analyzer = analyzer

    # Create the agent service (injects analyzer into tools)
    agent_service = CVAgentService(analyzer)
    app.state.agent = agent_service

    logger.info("✅ All services ready.")
    yield  # Application is running
    logger.info("Shutting down CV Analysis API.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CV Analysis API",
    description=(
        "AI-powered CV analysis using LangChain, Claude Sonnet, "
        "and FAISS.  Upload a CV, get structured extraction, "
        "job matching, and actionable improvement recommendations."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow Frontend origins (localhost dev + Docker internal)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",       # Next.js dev server
        "http://frontend:3000",        # Docker internal network
        "http://127.0.0.1:3000",
        "*",                           # Fallback for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Return application health status."""
    return HealthResponse()


@app.post("/upload", response_model=CVUploadResponse, tags=["CV Analysis"])
async def upload_cv(file: UploadFile = File(...)) -> CVUploadResponse:
    """
    Upload a CV file (PDF, DOCX, or TXT).

    The file is saved to disk and its text is extracted immediately.
    Returns a ``file_id`` to use in subsequent ``/analyze`` calls.
    """
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Use PDF, DOCX, or TXT.",
        )

    # Save uploaded file to temp directory
    config = AppConfig()
    save_path = Path(config.upload_dir) / file.filename
    with save_path.open("wb") as buf:
        shutil.copyfileobj(file.file, buf)
    logger.info("Saved uploaded file to %s", save_path)

    # Load and extract text
    analyzer: CVAnalyzer = app.state.analyzer
    try:
        response = analyzer.upload(str(save_path))
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return response


@app.get(
    "/analyze/{file_id}",
    response_model=CVAnalysisResult,
    tags=["CV Analysis"],
)
async def analyze_cv(file_id: str) -> CVAnalysisResult:
    """
    Run the full CV analysis pipeline on a previously uploaded CV.

    Pipeline:  load → chunk → extract → match → recommend

    Returns structured extraction, job matches, and recommendations.
    """
    analyzer: CVAnalyzer = app.state.analyzer
    try:
        result = await analyzer.analyze(file_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Analysis failed for file_id=%s", file_id)
        raise HTTPException(status_code=500, detail=f"Analysis error: {exc}")

    return result


@app.post(
    "/agent/query",
    response_model=AgentQueryResponse,
    tags=["Agent"],
)
async def agent_query(request: AgentQueryRequest) -> AgentQueryResponse:
    """
    Ask a free-form question about a specific CV.

    The LangChain ReAct agent will autonomously decide which tools
    to call to answer your question.

    Examples:
        - "Does this CV mention any cloud certifications?"
        - "What are the candidate's strongest technical skills?"
        - "How could the summary section be improved?"
    """
    agent_svc: CVAgentService = app.state.agent
    try:
        response = await agent_svc.query(request.file_id, request.question)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Agent query failed for file_id=%s", request.file_id)
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}")

    return response


# ---------------------------------------------------------------------------
# Entrypoint for `python -m app.main`
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
