-- MU STUDY HUB - Cloudflare D1 Database Schema
-- Run with: wrangler d1 execute mu-study-hub --local < migrations/001_initial.sql

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sha256_hash TEXT UNIQUE NOT NULL,
    original_filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    page_count INTEGER DEFAULT 0,
    student_id INTEGER NOT NULL,
    student_name TEXT NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    current_status TEXT DEFAULT 'UPLOADED',
    status_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    duplicate_of_id INTEGER DEFAULT NULL,
    is_ocr INTEGER DEFAULT 0
);

-- AI verification results table (immutable records)
CREATE TABLE IF NOT EXISTS document_ai_verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    extracted_text_summary TEXT,
    detected_category TEXT,
    detected_subject TEXT,
    detected_topics TEXT,
    confidence_score REAL,
    is_academic INTEGER DEFAULT 0,
    quality_status TEXT DEFAULT 'Unknown',
    suspicious_flags TEXT,
    ai_recommendation TEXT DEFAULT 'PENDING',
    model_name TEXT DEFAULT 'groq',
    verification_status TEXT DEFAULT 'VERIFIED',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    admin_decided INTEGER DEFAULT 0,
    admin_decision_at DATETIME DEFAULT NULL,
    admin_decision_by TEXT DEFAULT NULL,
    raw_response TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Create indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(current_status);
CREATE INDEX IF NOT EXISTS idx_documents_sha256 ON documents(sha256_hash);
CREATE INDEX IF NOT EXISTS idx_documents_student ON documents(student_id);
CREATE INDEX IF NOT EXISTS idx_verifications_doc_id ON document_ai_verifications(document_id);
CREATE INDEX IF NOT EXISTS idx_verifications_created_at ON document_ai_verifications(created_at);

-- Insert migration record
CREATE TABLE IF NOT EXISTS migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO migrations (name) VALUES ('001_initial');
