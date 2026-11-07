# API Reference

## Authentication

Admin endpoints require HTTP Basic Authentication.

```bash
curl -u admin:password http://localhost:8000/api/v1/documents
```

## Endpoints

### POST /api/v1/upload

Upload a PDF for AI verification.

**Parameters (multipart/form-data):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | PDF | Yes | The document to verify |
| `student_name` | string | Yes | Student's full name |
| `student_id` | integer | Yes | Student ID |

**Response: 201 Created**

```json
{
  "document_id": 1,
  "filename": "notes.pdf",
  "file_size": 102400,
  "status": "UPLOADED",
  "message": "Document received. Verification in progress."
}
```

---

### GET /api/v1/documents

List all documents (admin endpoint).

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Pagination offset |
| `limit` | integer | 50 | Results per page |

**Response: 200 OK**

```json
[
  {
    "id": 1,
    "filename": "database_notes.pdf",
    "file_size": 102400,
    "mime_type": "application/pdf",
    "sha256_hash": "abc123...",
    "page_count": 5,
    "student_id": 2024001,
    "student_name": "John Doe",
    "uploaded_at": "2024-01-15T10:30:00Z",
    "current_status": "PENDING_ADMIN_REVIEW"
  }
]
```

---

### GET /api/v1/documents/{doc_id}

Get document details with AI verification results.

**Response: 200 OK**

```json
{
  "id": 1,
  "filename": "database_notes.pdf",
  "file_size": 102400,
  "mime_type": "application/pdf",
  "sha256_hash": "abc123...",
  "page_count": 5,
  "student_id": 2024001,
  "student_name": "John Doe",
  "uploaded_at": "2024-01-15T10:30:00Z",
  "current_status": "PENDING_ADMIN_REVIEW",
  "verification": {
    "is_academic": true,
    "category": "Academic Notes",
    "confidence": 92,
    "summary": "Document contains Database Management Systems material",
    "detected_subject": "Computer Science",
    "detected_topics": ["SQL", "Normalization", "Joins"],
    "language": "English",
    "quality_status": "Good",
    "reason": "Document contains relevant educational material",
    "recommendation": "APPROVE_FOR_ADMIN_REVIEW"
  }
}
```

---

### POST /api/v1/admin/action

Take admin action on a document.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `document_id` | integer | Yes | ID of document |
| `action` | string | Yes | `approve`, `reject`, or `request_manual_review` |
| `admin_id` | string | Yes | Admin identifier |
| `notes` | string | No | Optional notes |

**Response: 200 OK**

```json
{
  "success": true,
  "document_id": 1,
  "new_status": "APPROVED",
  "message": "Document approved by admin"
}
```

---

## AI Verification Output

The AI verification result (section 3) includes:

| Field | Type | Description |
|-------|------|-------------|
| `is_academic` | boolean | Whether document is academically relevant |
| `category` | string | One of 14 categories |
| `confidence` | integer | 0-100 confidence score |
| `summary` | string | Brief description of content |
| `detected_subject` | string | Academic subject detected |
| `detected_topics` | string[] | List of topics found |
| `language` | string | Document language |
| `quality_status` | string | `Good`/`Fair`/`Poor`/`Excellent` |
| `recommendation` | string | `APPROVE_FOR_ADMIN_REVIEW`, `MANUAL_REVIEW_REQUIRED`, or `FLAG_AS_SUSPICIOUS` |

## Error Responses

### 400 Bad Request

```json
{
  "detail": "File must be a PDF"
}
```

### 403 Forbidden (Admin)

```json
{
  "detail": "Admin access required"
}
```

### 404 Not Found

```json
{
  "detail": "Document not found"
}
```

### 429 Too Many Requests

Rate limited. Wait before retrying.

---

## Document Categories

| Category | Description |
|----------|-------------|
| Academic Notes | Lecture notes, study material |
| Assignments | Homework, coursework submissions |
| Worksheets | Practice exercises, problem sets |
| Research Papers | Academic papers, theses |
| Practical Files | Lab reports, experiment data |
| Lab Manuals | Experiment instructions |
| Question Papers | Past exams, practice tests |
| GATE Preparation | Graduate aptitude test material |
| Educational Books | Textbooks, reference materials |
| Project Reports | Capstone, final year projects |
| Tutorials | How-to guides, step-by-step instructions |
| Other Educational Content | Miscellaneous academic material |
| Unrelated Content | Non-academic documents |
| Suspicious Content | Potentially malicious or spam |