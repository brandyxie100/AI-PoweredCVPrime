# Analysis_CV_V2 — AI-Powered CV Analysis with LangChain & Claude Sonnet

A production-ready FastAPI application that analyses CVs using **LangChain**, **Anthropic Claude Sonnet**, and **FAISS** vector search. Built with OOP design patterns (Singleton, Factory) and containerised with Docker.

---

## Table of Contents

1. [Features](#features)
2. [Architecture Overview](#architecture-overview)
3. [Project Structure](#project-structure)
4. [Design Patterns Explained](#design-patterns-explained)
5. [LangChain Components Deep Dive](#langchain-components-deep-dive)
6. [Agent & Tools Explained](#agent--tools-explained)
7. [Workflow Pipeline Explained](#workflow-pipeline-explained)
8. [Setup & Installation](#setup--installation)
9. [Docker Deployment](#docker-deployment)
10. [API Reference](#api-reference)
11. [Testing](#testing)
12. [Security Best Practices](#security-best-practices)

---

## Features

- **CV Parsing**: Supports PDF, DOCX, and TXT file formats.
- **Structured Extraction**: Uses Claude Sonnet to extract skills, experience, education, and contact info into typed Pydantic models.
- **Job Matching**: Embeds CV content with OpenAI embeddings and matches against a job catalogue using FAISS vector similarity search.
- **Actionable Recommendations**: Generates 5–10 specific, prioritised improvement suggestions.
- **Interactive Agent**: A LangChain ReAct agent answers free-form questions about any uploaded CV.
- **RESTful API**: FastAPI with automatic OpenAPI docs at `/docs`.
- **Docker-Ready**: Multi-stage Dockerfile + docker-compose for one-command deployment.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
│                         (app/main.py)                            │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────────┐    │
│  │  /upload │  │ /analyze/{id}│  │ /agent/query             │    │
│  └─────┬────┘  └──────┬───────┘  └────────────┬─────────────┘    │
│        │               │                       │                 │
│        ▼               ▼                       ▼                 │
│  ┌─────────────────────────────┐  ┌──────────────────────────┐   │
│  │      CVAnalyzer             │  │    CVAgentService        │   │
│  │    (Orchestrator)           │  │   (LangGraph ReAct Agent)│   │
│  │                             │  │                          │   │
│  │  1. DocumentLoaderFactory   │  │  Tools:                  │   │
│  │     (Factory Pattern)       │  │  - get_cv_full_text      │   │
│  │  2. TextChunker             │  │  - get_cv_chunks         │   │
│  │     (LangChain Splitter)    │  │  - search_cv_section     │   │
│  │  3. CVExtractorService      │  │  - analyze_cv_formatting │   │
│  │     (Structured Output)     │  │                          │   │
│  │  4. JobMatcherService       │  └──────────────────────────┘   │
│  │     (FAISS Vector Store)    │                                 │
│  │  5. RecommenderService      │                                 │
│  │     (LCEL Chain)            │                                 │
│  └─────────────────────────────┘                                 │
│                                                                  │
│  ┌─────────────────────────────┐                                 │
│  │    AppConfig (Singleton)    │  ← loads .env via python-dotenv │
│  │  - API keys                 │                                 │
│  │  - Model settings           │                                 │
│  │  - get_llm() / get_embed()  │                                 │
│  └─────────────────────────────┘                                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
Analysis_CV_V2/
├── app/
│   ├── __init__.py              # Package metadata & version
│   ├── config.py                # Singleton config manager
│   ├── main.py                  # FastAPI application & endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic request/response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_loader.py   # Factory pattern: PDF/DOCX/TXT loaders
│   │   ├── text_chunker.py      # LangChain text splitting
│   │   ├── cv_extractor.py      # Structured CV extraction (Claude)
│   │   ├── job_matcher.py       # FAISS vector store matching
│   │   ├── recommender.py       # LCEL recommendation chain
│   │   ├── cv_analyzer.py       # Pipeline orchestrator
│   │   └── agent.py             # LangChain ReAct agent
│   └── tools/
│       ├── __init__.py
│       └── cv_tools.py          # Custom tools for the agent
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest configuration
│   ├── test_loader.py           # Document loader unit tests
│   └── test_analyzer.py         # Pipeline & endpoint tests
├── sample_cvs/
│   └── sample_cv.txt            # Example CV for testing
├── .env.example                 # Template for environment variables
├── .gitignore
├── Dockerfile                   # Multi-stage Docker build
├── docker-compose.yml           # One-command deployment
├── requirements.txt             # Pinned Python dependencies
└── README.md                    # This file
```

---

## Design Patterns Explained

### 1. Singleton Pattern — `AppConfig`

**Problem**: We need one shared configuration object across all services. Creating multiple instances would waste memory and risk inconsistent state.

**Solution**: The `AppConfig` class overrides `__new__()` to ensure only one instance ever exists.

```python
class AppConfig:
    _instance: ClassVar[AppConfig | None] = None

    def __new__(cls) -> AppConfig:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return  # Skip re-initialization
        # ... load config from .env ...
        self._initialized = True
```

**How it works**:
1. First call: `_instance` is `None` → creates a new object, stores it.
2. Second call: `_instance` already exists → returns the **same** object.
3. `_initialized` flag prevents `__init__` from running twice.

**Usage**: `config = AppConfig()` — always returns the same instance.

### 2. Factory Pattern — `DocumentLoaderFactory`

**Problem**: Different CV file formats (PDF, DOCX, TXT) require different parsing logic, but the caller shouldn't care about which parser to use.

**Solution**: A Factory class inspects the file extension and returns the correct loader.

```python
class DocumentLoaderFactory:
    _LOADERS = {
        ".pdf": PDFLoader,
        ".docx": DocxLoader,
        ".txt": TxtLoader,
    }

    @staticmethod
    def create_loader(file_path) -> BaseDocumentLoader:
        suffix = Path(file_path).suffix.lower()
        loader_cls = DocumentLoaderFactory._LOADERS.get(suffix)
        return loader_cls(path)
```

**How it works**:
1. All loaders inherit from `BaseDocumentLoader` (abstract class with `load()` method).
2. The factory maps extensions → concrete classes.
3. The caller just writes `DocumentLoaderFactory.create_loader("resume.pdf").load()`.
4. To add a new format, create a new loader class and add one entry to `_LOADERS`. **No other code changes needed**.

---

## LangChain Components Deep Dive

### Component 1: `ChatAnthropic` (LLM)

The primary language model. Used for:
- Structured CV extraction (via `with_structured_output`).
- Recommendation generation.
- Agent reasoning.

```python
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.3)
```

### Component 2: `RecursiveCharacterTextSplitter`

Splits long text into smaller chunks while preserving semantic boundaries:

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,          # Max chars per chunk
    chunk_overlap=200,        # Overlap between chunks
    separators=["\n\n", "\n", ". ", " ", ""],
)
chunks = splitter.split_text(cv_text)
```

**Why these separators?** The splitter tries `\n\n` first (paragraph breaks), then `\n` (line breaks), then sentences, then words. This keeps related content together.

### Component 3: `with_structured_output` (Structured Extraction)

Forces the LLM to return data matching a Pydantic schema:

```python
class CVExtraction(BaseModel):
    candidate_name: str
    skills: list[ExtractedSkill]
    # ... more fields ...

chain = prompt | llm.with_structured_output(CVExtraction)
result: CVExtraction = await chain.ainvoke({"cv_text": text})
# result.candidate_name, result.skills — fully typed!
```

**How it works internally**: LangChain converts the Pydantic model into a tool definition and instructs the LLM to call that tool. The LLM's JSON response is automatically validated and parsed.

### Component 4: `FAISS` (Vector Store)

Facebook AI Similarity Search — finds the most similar job descriptions:

```python
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# Build index from job descriptions
docs = [Document(page_content=desc, metadata={"role": title}) for ...]
vectorstore = await FAISS.afrom_documents(docs, embeddings)

# Query: find jobs matching this CV
results = await vectorstore.asimilarity_search_with_score(cv_summary, k=5)
```

**How it works**:
1. Each job description is converted to a 1536-dimensional vector.
2. Vectors are stored in an optimised index.
3. At query time, the CV text is also embedded.
4. FAISS returns the *k* nearest neighbours (most similar jobs).

### Component 5: LCEL (LangChain Expression Language)

The `|` pipe operator chains components together:

```python
chain = prompt | llm | StrOutputParser()
result = await chain.ainvoke({"input": "data"})
```

**The flow**: `prompt` formats the input → `llm` generates a response → `StrOutputParser` extracts the text.

### Component 6: `OpenAIEmbeddings`

Converts text into dense vectors for FAISS:

```python
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
```

---

## Agent & Tools Explained

### What is a LangChain Agent?

An agent is an LLM that can **autonomously decide** which actions (tools) to take. Unlike a static chain, an agent can loop:

```
User Question
      ↓
┌─── Thought ──── Action (tool call) ──── Observation (tool result) ───┐
│         ↑                                           │                │
│         └───────────────────────────────────────────┘                │
│              (loop until enough info to answer)                      │
└──────────────────────────────────────────────────────────────────────┘
      ↓
Final Answer
```

### Agent Type: ReAct (Reasoning + Acting)

We use `create_react_agent` from LangGraph. The LLM explicitly writes its reasoning before selecting a tool, making decisions transparent:

```
Thought: The user wants to know about AWS certifications.
         I should search the CV for "AWS" or "certifications".
Action:  search_cv_section(file_id="abc123", query="certifications")
Observation: "- AWS Solutions Architect – Associate (2022)"
Thought: I found the answer.
Final Answer: The CV lists an AWS Solutions Architect – Associate certification from 2022.
```

### Custom Tools

Tools are Python functions decorated with `@tool`:

```python
@tool
def search_cv_section(file_id: str, query: str) -> str:
    """Search for specific information within a CV."""
    # ... implementation ...
```

The agent reads the tool's **name** and **docstring** to decide when to use it.

### How to Modify the Agent

1. **Add a new tool**: Write a function with `@tool` in `cv_tools.py`, add it to `ALL_CV_TOOLS`.
2. **Change personality**: Edit `AGENT_SYSTEM_PROMPT` in `agent.py`.
3. **Swap the LLM**: Replace `config.get_llm()` with any LangChain chat model.
4. **Limit iterations**: Add `recursion_limit=10` to prevent infinite loops.

---

## Workflow Pipeline Explained

The full analysis follows a 5-stage pipeline:

```
┌────────┐    ┌────────┐    ┌──────────┐    ┌────────┐    ┌───────────┐
│  LOAD  │───>│ CHUNK  │───>│ EXTRACT  │───>│ MATCH  │───>│ RECOMMEND │
└────────┘    └────────┘    └──────────┘    └────────┘    └───────────┘
 Factory       LangChain     Structured      FAISS         LCEL Chain
 Pattern       Splitter      Output          VectorStore
```

| Stage | Service | LangChain Component | What it Does |
|-------|---------|-------------------|--------------|
| **Load** | `DocumentLoaderFactory` | — | Reads PDF/DOCX/TXT → raw text string |
| **Chunk** | `TextChunker` | `RecursiveCharacterTextSplitter` | Splits text into overlapping 1000-char chunks |
| **Extract** | `CVExtractorService` | `ChatAnthropic.with_structured_output` | Extracts name, skills, experience → Pydantic model |
| **Match** | `JobMatcherService` | `FAISS` + `OpenAIEmbeddings` | Finds top-5 matching job roles by similarity |
| **Recommend** | `RecommenderService` | `ChatPromptTemplate \| ChatAnthropic \| StrOutputParser` | Generates 5-10 actionable improvement tips |

The `CVAnalyzer` class orchestrates all stages in sequence via its `analyze()` method.

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)
- An [OpenAI API key](https://platform.openai.com/) (for embeddings)

### Local Setup

```bash
# 1. Navigate to the project
cd Analysis_CV_V2

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and add your API keys

# 5. Run the application
uvicorn app.main:app --reload --port 8000

# 6. Open API docs
open http://localhost:8000/docs
```

---

## Docker Deployment

### Build & Run

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 2. Build and start with Docker Compose
docker compose up --build

# 3. Verify it's running
curl http://localhost:8000/health

# 4. Stop
docker compose down
```

### Docker Architecture

The Dockerfile uses a **multi-stage build**:
- **Stage 1 (builder)**: Installs all dependencies in a virtual environment.
- **Stage 2 (runtime)**: Copies only the virtual env + app code → smaller image.

```dockerfile
# Stage 1: Builder — install deps
FROM python:3.11-slim AS builder
RUN pip install -r requirements.txt

# Stage 2: Runtime — lean production image
FROM python:3.11-slim AS runtime
COPY --from=builder /opt/venv /opt/venv
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## API Reference

### `GET /health`
Returns health status.

### `POST /upload`
Upload a CV file. Returns a `file_id` for subsequent analysis.

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@sample_cvs/sample_cv.txt"
```

**Response**:
```json
{
  "file_id": "a1b2c3d4e5f6",
  "filename": "sample_cv.txt",
  "file_type": "txt",
  "char_count": 1523,
  "message": "CV uploaded and text extracted successfully."
}
```

### `GET /analyze/{file_id}`
Run the full analysis pipeline.

```bash
curl http://localhost:8000/analyze/a1b2c3d4e5f6
```

**Response** (abbreviated):
```json
{
  "file_id": "a1b2c3d4e5f6",
  "candidate_name": "John Doe",
  "summary": "Senior Software Engineer with 8+ years...",
  "skills": [{"name": "Python", "level": "expert", "years": 8.0}],
  "job_matches": [{"role": "Senior Software Engineer", "similarity_score": 0.87}],
  "recommendations": [{"category": "Skills Gap", "suggestion": "Add cloud certifications..."}],
  "overall_score": 82.5
}
```

### `POST /agent/query`
Ask a free-form question about a CV.

```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"file_id": "a1b2c3d4e5f6", "question": "Does this CV mention any AWS experience?"}'
```

---

## Testing

```bash
# Run all unit tests
pytest tests/ -v

# Run only fast tests (no API calls)
pytest tests/ -v -m "not integration"

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

---

## Security Best Practices

1. **Never hardcode API keys** — use `.env` files loaded by `python-dotenv`.
2. **`.env` is in `.gitignore`** — secrets never reach version control.
3. **Docker runs as non-root** — `USER appuser` in the Dockerfile.
4. **Input validation** — Pydantic models validate all API inputs.
5. **File type restriction** — only PDF, DOCX, TXT accepted.
6. **CORS configuration** — restrict `allow_origins` in production.
