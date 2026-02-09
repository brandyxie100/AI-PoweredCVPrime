"""
Integration Tests for the CV Analysis Pipeline.

Tests cover:
    - CV upload via the FastAPI endpoint.

Author: brandyxie
Email:  brandyxie100@qq.com
    - Text chunking.
    - Health check endpoint.
    - Config singleton behaviour.

Note:
    Tests that call the LLM (extract, match, recommend) require
    valid API keys and are marked with ``@pytest.mark.integration``.
    Run them with: ``pytest -m integration``
"""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import AppConfig
from app.services.text_chunker import TextChunker


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_config():
    """Reset the AppConfig singleton before each test."""
    AppConfig.reset()
    yield
    AppConfig.reset()


@pytest.fixture
def sample_cv_text() -> str:
    """A realistic sample CV text for testing."""
    return """
    JOHN DOE
    Email: john.doe@example.com | Phone: +44 7700 900000
    LinkedIn: linkedin.com/in/johndoe | GitHub: github.com/johndoe

    PROFESSIONAL SUMMARY
    Senior Software Engineer with 8+ years of experience designing and
    building scalable backend systems. Proficient in Python, Go, and
    cloud-native architectures. Passionate about clean code, mentoring
    junior developers, and delivering impactful products.

    SKILLS
    - Programming: Python, Go, JavaScript, SQL
    - Frameworks: FastAPI, Django, React
    - Cloud: AWS (EC2, S3, Lambda), Docker, Kubernetes
    - Data: PostgreSQL, Redis, Kafka, Elasticsearch
    - Tools: Git, CI/CD (GitHub Actions), Terraform

    WORK EXPERIENCE

    Senior Software Engineer — TechCorp Inc. (2021 – Present)
    - Designed microservices architecture serving 10M+ daily requests.
    - Reduced API latency by 40% through caching and query optimisation.
    - Led a team of 5 engineers; introduced code review culture.

    Software Engineer — StartupXYZ (2018 – 2021)
    - Built real-time data pipeline processing 500K events/minute.
    - Implemented CI/CD pipeline reducing deployment time from 2h to 15min.
    - Contributed to open-source Python libraries (1K+ GitHub stars).

    Junior Developer — WebAgency Ltd. (2016 – 2018)
    - Developed full-stack web applications using Django and React.
    - Maintained 99.9% uptime for client-facing services.

    EDUCATION
    MSc Computer Science — University of London (2016)
    BSc Mathematics — University of Manchester (2014)

    CERTIFICATIONS
    - AWS Solutions Architect – Associate
    - Certified Kubernetes Administrator (CKA)
    """


@pytest.fixture
def sample_cv_file(tmp_path: Path, sample_cv_text: str) -> Path:
    """Create a temporary .txt CV file."""
    cv_file = tmp_path / "john_doe_cv.txt"
    cv_file.write_text(sample_cv_text, encoding="utf-8")
    return cv_file


# ---------------------------------------------------------------------------
# Config Singleton Tests
# ---------------------------------------------------------------------------

class TestAppConfig:
    """Tests for the Singleton pattern in AppConfig."""

    def test_singleton_returns_same_instance(self) -> None:
        """Two calls to AppConfig() should return the same object."""
        config1 = AppConfig()
        config2 = AppConfig()
        assert config1 is config2

    def test_singleton_reset(self) -> None:
        """After reset(), a new instance should be created."""
        config1 = AppConfig()
        AppConfig.reset()
        config2 = AppConfig()
        assert config1 is not config2

    def test_default_values(self) -> None:
        """Default config values should be sensible."""
        config = AppConfig()
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
        assert config.temperature == 0.3


# ---------------------------------------------------------------------------
# Text Chunker Tests
# ---------------------------------------------------------------------------

class TestTextChunker:
    """Tests for the LangChain text chunker."""

    def test_split_produces_chunks(self, sample_cv_text: str) -> None:
        """Splitting a CV should produce multiple chunks."""
        chunker = TextChunker(chunk_size=500, chunk_overlap=100)
        chunks = chunker.split(sample_cv_text)
        assert len(chunks) > 1

    def test_split_preserves_content(self, sample_cv_text: str) -> None:
        """All original content should appear in at least one chunk."""
        chunker = TextChunker(chunk_size=500, chunk_overlap=100)
        chunks = chunker.split(sample_cv_text)
        combined = " ".join(chunks)
        assert "JOHN DOE" in combined
        assert "Python" in combined

    def test_split_with_metadata(self, sample_cv_text: str) -> None:
        """split_with_metadata should return dicts with content + metadata."""
        chunker = TextChunker(chunk_size=500, chunk_overlap=100)
        results = chunker.split_with_metadata(sample_cv_text, source="test")
        assert len(results) > 0
        assert "content" in results[0]
        assert "metadata" in results[0]
        assert results[0]["metadata"]["source"] == "test"

    def test_empty_text(self) -> None:
        """Empty text should produce an empty list of chunks."""
        chunker = TextChunker(chunk_size=500, chunk_overlap=100)
        chunks = chunker.split("")
        assert chunks == []


# ---------------------------------------------------------------------------
# FastAPI Endpoint Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestFastAPIEndpoints:
    """Tests for FastAPI endpoints using httpx."""

    async def test_health_check(self) -> None:
        """GET /health should return 200 with status='healthy'."""
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"

    async def test_upload_unsupported_format(self) -> None:
        """POST /upload with an unsupported file type should return 400."""
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/upload",
                files={"file": ("test.csv", b"a,b,c", "text/csv")},
            )

        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    async def test_upload_txt_file(self, sample_cv_file: Path) -> None:
        """POST /upload with a .txt CV should return 200 with file_id."""
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            with sample_cv_file.open("rb") as f:
                response = await client.post(
                    "/upload",
                    files={"file": ("resume.txt", f, "text/plain")},
                )

        assert response.status_code == 200
        data = response.json()
        assert "file_id" in data
        assert data["file_type"] == "txt"
        assert data["char_count"] > 0

    async def test_analyze_unknown_file_id(self) -> None:
        """GET /analyze/unknown should return 404."""
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/analyze/nonexistent")

        assert response.status_code == 404
