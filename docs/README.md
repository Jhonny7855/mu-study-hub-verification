# MU STUDY HUB - AI Document Verification Bot

A self-contained service that automatically verifies student-uploaded PDF documents before they enter the administrator approval queue.

## Overview

When a student uploads a document, the bot runs a structured 3-step pipeline:

1. **File Validation** – Verify extension, MIME type, PDF signature, file size, and check for corruption/password protection
2. **Text Extraction** – Extract text from native PDFs; use OCR (Tesseract) for scanned/image-based documents
3. **AI Classification** – Classify content into 14 academic categories with confidence scores

After classification, documents with confidence ≥85% go to admin review; lower scores are flagged for manual review.

## Quick Start

### Backend (Python FastAPI)

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your settings

# Run the server
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000/api/v1`.

### Frontend (React)

```bash
# Install dependencies
cd frontend
npm install

# Run the dev server
npm run dev
```

Open `http://localhost:3000` in your browser.

## Architecture

```
STUDENT UPLOAD
       |
       v
FILE VALIDATION (steps 1&2)
       |
       v
TEXT EXTRACTION / OCR
       |
       v
AI CLASSIFICATION
       |
       v
ADMIN REVIEW QUEUE
       |
    +--+--+
    |     |
    v     v
APPROVE  REJECT/FLAG
    |
    v
DOCUMENT PUBLISHED
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/upload` | Upload a PDF for verification |
| GET | `/api/v1/documents` | List all documents (admin) |
| GET | `/api/v1/documents/{id}` | Get document details |
| POST | `/api/v1/admin/action` | Admin action: approve/reject |

## Classification Categories

1. Academic Notes
2. Assignments
3. Worksheets
4. Research Papers
5. Practical Files
6. Lab Manuals
7. Question Papers
8. GATE Preparation
9. Educational Books
10. Project Reports
11. Tutorials
12. Other Educational Content
13. Unrelated Content
14. Suspicious Content

## AI Engine Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `AI_ENGINE` | `ollama` | `ollama`, `external`, or `heuristic` |
| `AI_MODEL` | `qwen2.5:7b-instruct` | Local model to use with Ollama |
| `AI_MIN_CONFIDENCE_TO_AUTO_REVIEW` | `60` | Threshold for admin queue |
| `OCR_ENABLED` | `true` | Enable OCR for scanned PDFs |

## Docker Deployment

```bash
docker build -t mu-study-hub-verification -f backend/Dockerfile .
docker run -p 8000:8000 -e DATABASE_URL=sqlite:///./data.db mu-study-hub-verification
```

## Security Notes

- All uploaded files are treated as untrusted
- PDF parsing is sandboxed; malicious PDFs are rejected
- No file content is sent to external APIs by default
- SHA-256 hashes enable duplicate detection
- Admin actions are logged with timestamps

## Database Schema

See `sql/001_initial_schema.sql` for the complete schema.

Key tables:

- `documents` – Original uploads with metadata
- `document_ai_verifications` – Immutable AI analysis records

## Frontend Integration

The React frontend provides:

- Student upload page (`/`)
- Admin dashboard (`/admin`)
- Real-time verification status
- Action buttons (approve/reject/manual review)

## Troubleshooting

**AI model not available?** Set `AI_ENGINE=heuristic` to use the fallback rule-based classifier.

**OCR failing?** Ensure `tesseract-ocr` and language packs are installed.

**Database locked?** SQLite in Docker may need volume persistence.