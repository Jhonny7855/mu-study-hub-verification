# Security Policy

## Secure Handling of Uploaded Documents

The AI Document Verification Bot treats ALL uploaded content as untrusted and implements multiple layers of protection.

### 1. Input Validation

All uploads pass through strict validation BEFORE any content is parsed:

- Extension whitelist (`.pdf` only)
- MIME type verification (actual file magic bytes)
- File size limits (configurable, default 50 MB)
- SHA-256 hash calculation for duplicate detection

### 2. PDF Parsing Safety

The bot uses `pypdf` which has good security practices:

- No JavaScript execution in PDFs
- No external resource fetching
- Page count limits prevent DoS via massive PDFs
- Memory limits on extraction

### 3. OCR Isolation

For scanned PDFs requiring OCR:

- Tesseract runs in-process but with file size limits
- Only specific language packs are installed
- Temporary files are cleaned up after processing
- Maximum page limit enforced

### 4. AI Classification Safeguards

**Never** does the bot:

- Execute code from documents
- Fetch external URLs from documents  
- Send student documents to external APIs (unless explicitly configured via `AI_ENGINE=external`)

When using external providers:

- API keys stay server-side only
- No document content is logged
- Users are notified in UI when external analysis is used

### 5. Data Protection

- All stored documents have SHA-256 hashes for integrity verification
- Admin actions are auditable with timestamps
- AI results are stored separately from admin decisions
- Verification history is immutable (new records for re-checks)

## Security Recommendations

### For Your Deployment

1. **Change Default Credentials**
   - Set a strong `SECRET_KEY` environment variable
   - Add real admin users to `ADMIN_USERS`

2. **Database Security**
   - Use PostgreSQL in production (not SQLite)
   - Use a dedicated database user with minimal privileges
   - Enable SSL for PostgreSQL connections

3. **Network Security**
   - Run behind a reverse proxy (nginx, Caddy)
   - Use HTTPS
   - Configure firewall rules

4. **Storage Security**
   - Store uploaded files outside the web root
   - Use cloud storage with encryption-at-rest if needed
   - Implement file lifecycle (auto-delete old uploads)

5. **Rate Limiting**
   - Default limits are set (60 req/min for API, 10/min for uploads)
   - Adjust based on your deployment size

### Reporting Vulnerabilities

If you discover a security vulnerability, please report it:

1. Do NOT open a public issue
2. Email security@example.com with details
3. We'll respond within 48 hours

## Privacy Notes

- Documents are only processed for academic classification
- No user profiles or tracking
- File content is never shared with third parties
- AI analysis runs locally by default (Ollama or heuristic)

## Compliance Reminders

- Students should be informed that documents may be analyzed
- Store only documents with appropriate consent
- Implement data retention policies
- Consider GDPR/CCPA requirements for your jurisdiction