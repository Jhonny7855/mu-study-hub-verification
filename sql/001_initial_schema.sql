-- MU STUDY HUB - AI Verification Database Schema
-- Run once during initial setup

-- Enable UUID extension (if using UUIDs)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    sha256_hash TEXT UNIQUE NOT NULL,
    page_count INTEGER DEFAULT 0,
    is_ocr BOOLEAN DEFAULT FALSE,
    student_id INTEGER NOT NULL,
    student_name TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    current_status TEXT DEFAULT 'UPLOADED',
    status_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duplicate_of_id INTEGER REFERENCES documents(id)
);

-- AI verification results table (immutable records)
CREATE TABLE IF NOT EXISTS document_ai_verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    extracted_text_summary TEXT,
    detected_category TEXT,
    detected_subject TEXT,
    detected_topics JSON DEFAULT '[]',
    confidence_score REAL,
    is_academic BOOLEAN DEFAULT FALSE,
    quality_status TEXT DEFAULT 'Unknown',
    suspicious_flags JSON DEFAULT '[]',
    ai_recommendation TEXT DEFAULT 'PENDING',
    model_name TEXT DEFAULT 'heuristic',
    verification_status TEXT DEFAULT 'VERIFIED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    admin_decided BOOLEAN DEFAULT FALSE,
    admin_decision_at TIMESTAMP,
    admin_decision_by TEXT
);

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(current_status);
CREATE INDEX IF NOT EXISTS idx_documents_sha256 ON documents(sha256_hash);
CREATE INDEX IF NOT EXISTS idx_documents_student ON documents(student_id);
CREATE INDEX IF NOT EXISTS idx_verifications_doc_id ON document_ai_verifications(document_id);
CREATE INDEX IF NOT EXISTS idx_verifications_created_at ON document_ai_verifications(created_at);