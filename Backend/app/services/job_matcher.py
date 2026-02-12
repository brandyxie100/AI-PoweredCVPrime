"""
Job Matcher Service — FAISS Vector Store.

This module builds a FAISS vector store from a predefined catalogue of
job-role descriptions, then performs semantic similarity search to find
the best-matching roles for a given CV.

Workflow position:  **STEP 4 — MATCH**
    load → chunk → extract → match → recommend
                             ^^^^^

LangChain Components:
    - ``FAISS``              – Facebook AI Similarity Search, an efficient
                               library for nearest-neighbour lookup on dense
                               vectors.  LangChain wraps it so we can index
                               and query with a single API call.
    - ``OpenAIEmbeddings``   – Converts text into 1536-dim vectors that
                               capture semantic meaning (``text-embedding-3-small``).
    - ``Document``           – LangChain's container for text + metadata,
                               required by FAISS ingestion.

How FAISS works (conceptual):
    1. Each job description is turned into a high-dimensional vector by
       the embedding model.
    2. All vectors are stored in an index optimised for fast cosine /
       L2 similarity search.
    3. At query time, the CV text is also embedded, and the index
       returns the *k* nearest job-description vectors along with their
       distance scores.
    4. We normalise the distances to a 0-1 similarity score for the API.
"""

from __future__ import annotations

import logging
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.config import AppConfig
from app.models.schemas import JobMatch

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pre-defined job-role catalogue (could be loaded from DB in production)
# ---------------------------------------------------------------------------

JOB_CATALOGUE: list[dict[str, str]] = [
    {
        "role": "Senior Software Engineer",
        "description": (
            "Design and build scalable backend services, REST APIs, "
            "microservices.  Proficient in Python, Java, or Go.  "
            "Experience with CI/CD, Docker, Kubernetes.  Strong "
            "system design and code review skills."
        ),
    },
    {
        "role": "Data Scientist",
        "description": (
            "Develop machine-learning models, perform statistical "
            "analysis, build data pipelines.  Proficient in Python, "
            "pandas, scikit-learn, TensorFlow.  Experience with A/B "
            "testing and experiment design."
        ),
    },
    {
        "role": "Machine Learning Engineer",
        "description": (
            "Deploy ML models to production, build feature stores, "
            "optimise inference latency.  Proficient in Python, "
            "PyTorch, MLflow, Docker.  Strong software engineering "
            "fundamentals."
        ),
    },
    {
        "role": "DevOps / Platform Engineer",
        "description": (
            "Build and maintain CI/CD pipelines, infrastructure as "
            "code (Terraform, CloudFormation).  Manage Kubernetes "
            "clusters, monitoring, and alerting.  Strong Linux and "
            "networking skills."
        ),
    },
    {
        "role": "Frontend Developer",
        "description": (
            "Build responsive web applications with React, Vue, or "
            "Angular.  Proficient in TypeScript, HTML/CSS, and "
            "state management.  Experience with design systems "
            "and accessibility best practices."
        ),
    },
    {
        "role": "Full Stack Developer",
        "description": (
            "Work across frontend and backend, building end-to-end "
            "features.  Proficient in JavaScript/TypeScript, Python, "
            "databases (SQL & NoSQL).  Experience with cloud services."
        ),
    },
    {
        "role": "Product Manager",
        "description": (
            "Define product roadmap, prioritise features, work with "
            "engineering and design teams.  Strong analytical skills, "
            "user research, A/B testing, stakeholder communication."
        ),
    },
    {
        "role": "Data Analyst",
        "description": (
            "Analyse business data, build dashboards and reports. "
            "Proficient in SQL, Excel, Tableau/Power BI.  Experience "
            "with statistical analysis and data visualisation."
        ),
    },
    {
        "role": "AI / NLP Engineer",
        "description": (
            "Build NLP pipelines, fine-tune large language models, "
            "develop RAG systems.  Proficient in Python, LangChain, "
            "Hugging Face, vector databases.  Research background "
            "is a plus."
        ),
    },
    {
        "role": "University Lecturer / Researcher",
        "description": (
            "Teach courses in computer science or related fields. "
            "Publish research papers, supervise students, apply for "
            "grants.  PhD required.  Strong communication and "
            "presentation skills."
        ),
    },
]


# ---------------------------------------------------------------------------
# Job Matcher Service
# ---------------------------------------------------------------------------

class JobMatcherService:
    """
    Matches a CV to the most relevant job roles using FAISS similarity search.

    Internally:
        1. Embeds every job description in ``JOB_CATALOGUE`` into a FAISS index.
        2. At query time, embeds the CV summary / skills text.
        3. Returns top-*k* nearest job roles with normalised similarity scores.

    Usage::

        matcher = JobMatcherService()
        await matcher.build_index()
        matches = await matcher.match("Python, ML, 5 years backend experience")
    """

    def __init__(self) -> None:
        config = AppConfig()
        self._embeddings = config.get_embeddings()
        self._vectorstore: Optional[FAISS] = None
        self._job_docs: list[Document] = []
        logger.info("JobMatcherService created (index not yet built).")

    async def build_index(self) -> None:
        """
        Build the FAISS index from the job catalogue.

        Each catalogue entry becomes a LangChain ``Document`` whose
        ``page_content`` is the description and ``metadata`` holds
        the role title.
        """
        self._job_docs = [
            Document(
                page_content=job["description"],
                metadata={"role": job["role"]},
            )
            for job in JOB_CATALOGUE
        ]

        # FAISS.from_documents embeds all documents and builds the index
        self._vectorstore = await FAISS.afrom_documents(
            documents=self._job_docs,
            embedding=self._embeddings,
        )
        logger.info("FAISS index built with %d job-role documents.", len(self._job_docs))

    async def match(
        self,
        query_text: str,
        top_k: int = 5,
    ) -> list[JobMatch]:
        """
        Find the *top_k* job roles most similar to the query text.

        Args:
            query_text: A text describing the candidate's profile
                        (e.g. skills summary + experience highlights).
            top_k: Number of matches to return.

        Returns:
            A list of ``JobMatch`` objects sorted by descending similarity.
        """
        if self._vectorstore is None:
            await self.build_index()

        # ``similarity_search_with_score`` returns (Document, distance) pairs.
        # Lower distance = more similar.  We convert to a 0–1 similarity.
        results = await self._vectorstore.asimilarity_search_with_score(
            query_text, k=top_k
        )

        matches: list[JobMatch] = []
        for doc, distance in results:
            # Normalise L2 distance to a 0–1 similarity score
            similarity = 1.0 / (1.0 + distance)
            matches.append(
                JobMatch(
                    role=doc.metadata["role"],
                    similarity_score=round(similarity, 3),
                    reason=doc.page_content[:120] + "...",
                )
            )

        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        logger.info("Matched query to %d job roles.", len(matches))
        return matches
