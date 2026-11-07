# Cloudflare Deployment Guide

This guide covers deploying the AI Document Verification Bot to Cloudflare.

## Prerequisites

1. Cloudflare account
2. Domain (optional - can use workers.dev)
3. Groq API key (or Google Gemini API key)
4. Node.js 18+ installed

## Deployment Steps

### 1. Install Wrangler
```bash
npm install -g wrangler
```

### 2. Authenticate
```bash
wrangler login
```

### 3. Update wrangler.toml
- Set `account_id` to your Cloudflare account ID

### 4. Create D1 Database
```bash
wrangler d1 create mu-study-hub
```
Copy the `database_id` and paste it into `wrangler.toml`.

### 5. Create R2 Bucket
```bash
wrangler r2 bucket create mu-study-hub-uploads
```

### 6. Create KV Namespace
```bash
wrangler kv:namespace create CACHE
```
Copy the `id` and update `wrangler.toml`.

### 7. Apply Database Schema
```bash
wrangler d1 execute mu-study-hub --local < migrations/001_initial.sql
```

### 8. Set Environment Variables
```bash
wrangler secret put GROQ_API_KEY
```

### 9. Deploy
```bash
wrangler deploy
```

### 10. Deploy Frontend to Cloudflare Pages
```bash
cd frontend
npm install
npm run build
```
Connect the Pages project manually in Cloudflare dashboard.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /upload | Upload PDF for verification |
| GET | /documents | List all documents |
| GET | /documents/:id | Get document details |
| POST | /admin/action | Admin approve/reject |
| GET | /health | Health check |

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| GROQ_API_KEY | Your Groq API key | Yes |
| ADMIN_USERS | Comma-separated admin usernames | Yes |
| STORAGE_MAX_BYTES | Max upload size (default: 50MB) | No |

## Testing Locally
```bash
wrangler dev
```
The Worker will be available at `http://localhost:8787`.
