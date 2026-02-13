# CVPrime — Intelligent Resume Optimisation Platform

A SaaS-ready platform that leverages Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG) to help job seekers tailor resumes to specific job descriptions, maximise ATS compatibility, and secure more interview opportunities.

**CVPrime** uses RAG to match your most relevant experiences to each JD requirement, producing **context-aware optimisations** that speak directly to what hiring managers and applicant tracking systems are looking for.

---

## How It Works

CVPrime automates the resume optimisation process through an **agentic AI workflow**:

1. **Upload your resume** — drag-and-drop or click-to-browse (PDF, DOCX, or TXT).
2. **Paste the target job description** — the system parses JD requirements automatically.
3. **Receive your results** —
   - An optimised resume with JD-aligned keywords and phrasing.
   - An ATS match score (0–100) measuring keyword and structure compatibility.
   - A gap analysis report highlighting missing skills and suggested additions.

```
 ┌──────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐    ┌────────────┐
 │  Upload  │───>│  Chunk   │───>│  Extract  │───>│  Match   │───>│ Recommend  │
 │  Resume  │    │  Text    │    │  Skills & │    │  to Job  │    │ & Optimise │
 │ (PDF/    │    │ (Lang-   │    │  Exp via  │    │  Roles   │    │ (LCEL      │
 │  DOCX/   │    │  Chain   │    │  Claude   │    │  (FAISS  │    │  Chain →   │
 │  TXT)    │    │  Splitter│    │  Sonnet)  │    │  Vector) │    │  Claude)   │
 └──────────┘    └──────────┘    └───────────┘    └──────────┘    └────────────┘
   Factory          LangChain      Structured        Semantic        Actionable
   Pattern          Component      Output            Search          Advice
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Smart Resume Parsing** | Extracts structured data (skills, experience, education, contact) from PDF, DOCX, and TXT files using a Factory-pattern document loader. |
| **RAG-Powered Matching** | Embeds resume content with HuggingFace `all-MiniLM-L6-v2` and performs semantic similarity search against job descriptions via FAISS vector store. |
| **ATS Compatibility Score** | Calculates a 0–100 quality score based on keyword density, section completeness, formatting, and JD alignment. |
| **Gap Analysis** | Identifies missing skills, certifications, and experience areas that the target JD requires but your resume lacks. |
| **Actionable Recommendations** | Generates 5–10 specific, prioritised improvement suggestions (not vague advice — concrete rewrites and additions). |
| **Interactive AI Agent** | A LangChain ReAct agent answers free-form questions about your resume ("Does my CV mention AWS?" / "How should I improve my summary?"). |
| **Drag-and-Drop UI** | Modern Next.js frontend with real-time upload, animated pipeline progress, and a clean results dashboard. |
| **Containerised Deployment** | One-command `docker compose up` launches both Backend and Frontend with health checks and volume persistence. |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Docker Compose                              │
│                                                                     │
│  ┌──────────────────────┐       ┌────────────────────────────────┐  │
│  │   Frontend (:3000)   │       │       Backend (:8000)          │  │
│  │                      │       │                                │  │
│  │   Next.js 14         │──────>│   FastAPI + LangChain          │  │
│  │   TypeScript 5       │ REST  │                                │  │
│  │   Tailwind CSS 3     │ API   │   ┌──────────────────────────┐ │  │
│  │                      │       │   │    CVAnalyzer (Orch.)    │ │  │
│  │   Components:        │       │   │                          │ │  │
│  │   - FileUpload       │       │   │  1. DocumentLoaderFactory│ │  │
│  │   - AnalysisResults  │       │   │  2. TextChunker          │ │  │
│  │   - LoadingSpinner   │       │   │  3. CVExtractorService   │ │  │
│  │   - Header           │       │   │  4. JobMatcherService    │ │  │
│  └──────────────────────┘       │   │  5. RecommenderService   │ │  │
│                                 │   └──────────────────────────┘ │  │
│                                 │                                │  │
│                                 │   ┌──────────────────────────┐ │  │
│                                 │   │   CVAgentService         │ │  │
│                                 │   │   (LangGraph ReAct Agent)│ │  │
│                                 │   │   4 custom tools         │ │  │
│                                 │   └──────────────────────────┘ │  │
│                                 │                                │  │
│                                 │   ┌──────────────────────────┐ │  │
│                                 │   │   AppConfig (Singleton)  │ │  │
│                                 │   │   .env → API keys        │ │  │
│                                 │   └──────────────────────────┘ │  │
│                                 └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Design Patterns:**
- **Singleton** — `AppConfig` ensures one shared configuration instance across all services.
- **Factory** — `DocumentLoaderFactory` selects the correct file parser (PDF / DOCX / TXT) based on extension.
- **Composition** — `CVAnalyzer` orchestrates all pipeline stages without inheritance.

**LangChain / LangGraph Components:**
- `ChatAnthropic` — Claude Sonnet for extraction, recommendation, and agent reasoning.
- `RecursiveCharacterTextSplitter` — chunking with semantic boundary awareness.
- `with_structured_output` — forces LLM to return typed Pydantic objects.
- `FAISS` + `HuggingFaceEmbeddings` — local vector similarity search (no API key needed).
- `create_react_agent` — ReAct agent with custom tools for interactive Q&A.
- **LCEL** (`|` pipe) — composable chains: `prompt | llm | parser`.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 14, TypeScript 5, Tailwind CSS 3 | Responsive SPA with drag-and-drop upload |
| **Backend** | FastAPI, Python 3.11, Pydantic v2 | REST API with async endpoints and type-safe schemas |
| **AI / LLM** | Anthropic Claude Sonnet (via LangChain) | Resume extraction, recommendations, agent reasoning |
| **RAG** | FAISS + HuggingFace `all-MiniLM-L6-v2` | Semantic similarity matching (runs locally, no API key) |
| **Agent** | LangGraph `create_react_agent` | Autonomous tool-using agent for free-form Q&A |
| **Infra** | Docker, Docker Compose | Multi-stage builds, health checks, volume persistence |
| **Security** | python-dotenv, non-root containers | Secrets via `.env`, `appuser` in Docker |

---

## Project Structure

```
AI-PoweredCVAnalysis/
│
├── Backend/                          # FastAPI + LangChain (Python)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py                # Singleton config (loads .env)
│   │   ├── main.py                  # FastAPI app & endpoints
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── cv_analyzer.py       # Pipeline orchestrator
│   │   │   ├── document_loader.py   # Factory: PDF / DOCX / TXT loaders
│   │   │   ├── text_chunker.py      # LangChain text splitter
│   │   │   ├── cv_extractor.py      # Structured extraction (Claude)
│   │   │   ├── job_matcher.py       # FAISS vector matching
│   │   │   ├── recommender.py       # LCEL recommendation chain
│   │   │   └── agent.py             # LangGraph ReAct agent
│   │   └── tools/
│   │       └── cv_tools.py          # 4 custom tools for the agent
│   ├── tests/                       # pytest unit & integration tests
│   ├── .env                         # API keys (gitignored)
│   ├── Dockerfile                   # Multi-stage Python build
│   ├── entrypoint.sh                # Fixes volume permissions
│   └── requirements.txt             # Pinned Python dependencies
│
├── Frontend/                         # Next.js 14 (TypeScript + Tailwind)
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # Root layout (Inter font, metadata)
│   │   │   ├── page.tsx             # Main page: upload → analyse → results
│   │   │   └── globals.css          # Tailwind directives + custom classes
│   │   ├── components/
│   │   │   ├── Header.tsx           # Top navigation bar
│   │   │   ├── FileUpload.tsx       # Drag-and-drop upload (react-dropzone)
│   │   │   ├── LoadingSpinner.tsx   # Animated pipeline progress
│   │   │   └── AnalysisResults.tsx  # Score, skills, matches, recommendations, agent chat
│   │   ├── lib/
│   │   │   └── api.ts              # API client → Backend endpoints
│   │   └── types/
│   │       └── index.ts            # TypeScript interfaces (mirrors Backend schemas)
│   ├── Dockerfile                   # Multi-stage Node.js build
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── Docs/                             # Documentation
│   ├── 01-git-workflow-guide.md
│   └── 02-system-architecture.md
│
├── docker-compose.yml                # Orchestrates Backend + Frontend
├── .gitignore                        # Python + Node.js + secrets rules
└── README.md                         # This file
```

---

## Quick Start

### Prerequisites

- **Docker** and **Docker Compose** (recommended) — OR —
- **Python 3.11+** and **Node.js 20+** for local development
- An [Anthropic API key](https://console.anthropic.com/) (for Claude Sonnet)

### Option 1: Docker (one command)

```bash
# 1. Clone the repository
git clone <repo-url> && cd AI-PoweredCVAnalysis

# 2. Configure API keys
cp .env.example Backend/.env
# Edit Backend/.env — add your ANTHROPIC_API_KEY

# 3. Build and launch both services
docker compose up --build

# 4. Open in browser
#    Frontend  →  http://localhost:3000
#    Backend   →  http://localhost:8000/docs  (Swagger UI)
```

### Option 2: Local Development

**Terminal 1 — Backend:**

```bash
cd Backend
python -m venv venv && source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
cp ../.env.example .env   # add your ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**

```bash
cd Frontend
npm install
npm run dev
# Opens at http://localhost:3000
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/upload` | Upload a CV file (PDF / DOCX / TXT) |
| `GET` | `/analyze/{file_id}` | Run the full analysis pipeline |
| `POST` | `/agent/query` | Ask a free-form question about a CV |

### Example: Upload and Analyse

```bash
# Upload a resume
curl -X POST http://localhost:8000/upload -F "file=@resume.pdf"
# → {"file_id": "a1b2c3d4e5f6", "char_count": 1523, ...}

# Run analysis
curl http://localhost:8000/analyze/a1b2c3d4e5f6
# → {skills, experience, job_matches, recommendations, overall_score, ...}

# Ask the agent a question
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"file_id": "a1b2c3d4e5f6", "question": "Does this CV mention AWS?"}'
```

---

## License

See [LICENSE](./LICENSE) for details.
