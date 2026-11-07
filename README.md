# MU STUDY HUB - AI Document Verification Bot

A self-contained service that automatically verifies student-uploaded PDF documents before they enter the administrator approval queue.

## Quick Start

```bash
# Backend
cd backend
uv pip install -r requirements.txt --break-system-packages
export AI_ENGINE=heuristic  # No LLM required for dev testing
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 to upload documents.
Open http://localhost:8000/docs for the API reference.

## Architecture

```
STUDENT UPLOAD
       │
       ▼
   File Validation (ext, MIME, size, corruption check)
       │
       ▼
   Text Extraction (native + OCR fallback)
       │
       ▼
   AI Classification (14 academic categories)
       │
       ▼
   ADMIN REVIEW QUEUE
    ┌──┴──┐
    ▼     ▼
 APPROVE  REJECT/FLAG
```

## Components

**Backend** (`backend/`)
- FastAPI server with async PostgreSQL/SQLite support
- 3-step verification pipeline
- Heuristic classifier (works offline) with Ollama/OpenAI optional
- Admin API with HTTP Basic auth
- Background task processing

**Frontend** (`frontend/`)
- React 18 with Vite
- Student upload page
- Admin dashboard with document cards
- Action buttons: Approve / Reject / Manual Review

## Database

```bash
# Initialize database
python -c "from app.models import Base; from app.core.database import get_engine; import asyncio; asyncio.run(Base.metadata.create_all(get_engine()))"

# Or use raw SQL
psql -f sql/001_initial_schema.sql
```

## AI Engine Options

| Engine | Setup | Description |
|--------|-------|-------------|
| `heuristic` | None | Rule-based classifier (always works) |
| `ollama` | Install Ollama + model | Free local model |
| `external` | API key in `.env` | OpenAI or Anthropic |

Set via `AI_ENGINE` in `.env`.

## File Structure

```
mu-study-hub/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── config.py     # Settings
│   │   ├── core/         # DB helpers
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Validator, extractor, classifier
│   │   └── main.py       # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   └── pages/        # Page views
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── sql/
│   └── 001_initial_schema.sql
├── docs/
│   ├── README.md
│   ├── CONFIGURATION.md
│   └── SECURITY.md
└── .env.example
```

## Configuration

See `.env.example` and `docs/CONFIGURATION.md` for all options.

Key settings:
- `AI_ENGINE` – `heuristic` (default), `ollama`, or `external`
- `AI_MODEL` – Model name (e.g., `qwen2.5:7b-instruct`)
- `ADMIN_USERS` – Comma-separated admin usernames
- `DATABASE_URL` – PostgreSQL or SQLite URL

## Security

See `docs/SECURITY.md`. Key points:

- All uploads treated as untrusted
- PDF parsing sandboxed
- No code execution
- File size limits enforced
- SHA-256 hashing for duplicates

## Documentation

- docs/README.md – Project overview
- docs/CONFIGURATION.md – Environment setup
- docs/SECURITY.md – Security policy