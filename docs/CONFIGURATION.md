# Configuration Guide

## Environment Variables

Copy `.env.example` to `.env` and edit the values.

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./mu_study_hub.db` | SQLAlchemy connection URL. Use `postgresql+asyncpg://user:pass@host/db` for production |

### Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_LOCAL_PATH` | `./storage/uploads` | Directory to store uploaded PDFs |
| `STORAGE_MAX_BYTES` | `52428800` | Maximum file size (50 MB) |

### AI Engine

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_ENGINE` | `ollama` | `ollama`, `external`, or `heuristic` |
| `AI_MODEL` | `qwen2.5:7b-instruct` | Model name for Ollama or external API |
| `AI_TIMEOUT_SECONDS` | `45` | Timeout for AI API calls |
| `AI_MIN_CONFIDENCE_TO_AUTO_REVIEW` | `60` | Confidence threshold for admin queue |

### External AI Providers (optional)

Only set these if `AI_ENGINE=external`. Keys are stored server-side only.

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | No | For OpenAI GPT models |
| `ANTHROPIC_API_KEY` | No | For Anthropic Claude models |

### OCR Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OCR_ENABLED` | `true` | Enable OCR for scanned PDFs |
| `OCR_LANGUAGE` | `eng+hin` | Tesseract language codes |
| `OCR_DPI` | `300` | Resolution for PDF-to-image conversion |
| `OCR_MAX_PAGES` | `12` | Maximum pages to OCR |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOWED_MIME_TYPES` | `application/pdf` | Only accept these MIME types |
| `MAX_PDF_PAGES` | `200` | Reject PDFs with more pages |
| `HASH_ALGORITHM` | `sha256` | File hashing algorithm |
| `SECRET_KEY` | `change-me` | Secret for session signing |
| `ADMIN_USERS` | `admin` | Comma-separated list of admin usernames |

### CORS

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed frontend origins |

## AI Engine Selection

### Option 1: Local Ollama (Default, Recommended)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull qwen2.5:7b-instruct

# Run the service
uvicorn app.main:app --reload
```

### Option 2: External Provider

```bash
export AI_ENGINE=external
export OPENAI_API_KEY=sk-...
# or
export ANTHROPIC_API_KEY=sk-...

uvicorn app.main:app --reload
```

### Option 3: Heuristic Only (No AI)

```bash
export AI_ENGINE=heuristic
uvicorn app.main:app --reload
```

## Production Deployment

### PostgreSQL Example

```bash
export DATABASE_URL="postgresql+asyncpg://mu_user:secure_password@db:5432/mu_study_hub"
export STORAGE_LOCAL_PATH="/data/uploads"
export AI_ENGINE=external  # or ollama if available
export SECRET_KEY="$(openssl rand -hex 32)"

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Environment-specific Overrides

For Docker, create a `.env.production` file and mount it:

```bash
docker run -v .env.production:/app/.env mu-study-hub-verification
```