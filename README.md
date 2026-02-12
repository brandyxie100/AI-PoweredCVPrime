# AI-Powered CV Analysis

A full-stack application that analyses CVs using AI and provides actionable improvement recommendations.

## Architecture

```
AI-PoweredCVAnalysis/
├── Backend/       ← FastAPI + LangChain + Claude Sonnet (Python)
├── Frontend/      ← Next.js 14 + TypeScript 5 + Tailwind CSS 3
├── Docs/          ← Detailed documentation
└── docker-compose.yml
```

## Quick Start

### Option 1: Docker (recommended)

```bash
# 1. Configure API keys
cp Backend/.env.example Backend/.env
# Edit Backend/.env with your ANTHROPIC_API_KEY

# 2. Build and run both services
docker compose up --build

# 3. Open in browser
#    Frontend:  http://localhost:3000
#    Backend:   http://localhost:8000/docs
```

### Option 2: Local Development

**Backend** (terminal 1):
```bash
cd Backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your API keys
uvicorn app.main:app --reload --port 8000
```

**Frontend** (terminal 2):
```bash
cd Frontend
npm install
npm run dev
# Opens at http://localhost:3000
```

## Features

- **Upload** CV files (PDF, DOCX, TXT) via drag-and-drop
- **AI Analysis** — structured extraction of skills, experience, education
- **Job Matching** — FAISS vector similarity against a job catalogue
- **Recommendations** — 5-10 actionable improvement suggestions
- **Agent Q&A** — ask free-form questions about any uploaded CV
- **Quality Score** — 0-100 overall CV rating

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript 5, Tailwind CSS 3 |
| Backend | FastAPI, Python 3.11, LangChain |
| AI | Anthropic Claude Sonnet, FAISS, HuggingFace Embeddings |
| Infra | Docker, Docker Compose |

See `Docs/README.md` for detailed architecture documentation.
