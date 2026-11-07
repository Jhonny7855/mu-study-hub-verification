"""Step 3: AI classification service.

Classifies document content into academic categories.
Supports local Ollama models, external providers, or pure heuristic fallback.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime
from typing import Any

import httpx
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.config import settings
from app.models.document import DocumentCategory
from app.schemas.document import AIVerifyRequest, AIVerifyResponse

log = logging.getLogger(__name__)

# Academic keywords for heuristic classification
ACADEMIC_KEYWORDS = {
    "Computer Science": [
        "algorithm", "data structure", "database", "sql", "python", "java",
        "complexity", "recursion", "graph", "tree", "sorting",
        "normalization", "joins", "transaction", "storage", "indexing",
        "os", "network", "operating system", "software", "devops"
    ],
    "Mathematics": [
        "calculus", "derivative", "integral", "matrix", "determinant", "eigen",
        "vector", "probability", "statistics", "theorem", "proof", "equation",
        "linear algebra", "differential", "optimization"
    ],
    "Physics": [
        "Newton", "force", "energy", "motion", "quantum", "particle", "wave",
        "thermodynamics", "electromagnetism", "optics", "mechanics", "physics"
    ],
    "Chemistry": [
        "reaction", "compound", "molecule", "atom", "periodic", "acid",
        "base", "salt", "solution", "equilibrium", "stoichiometry"
    ],
    "Biology": [
        "cell", "dna", "rna", "protein", "enzyme", "genome", "evolution",
        "photosynthesis", "mitosis", "meiosis", "organism", "biology"
    ],
    "GATE": [
        "gate", "graduate", "aptitude", "general", "test", "engineering"
    ],
    "Economics": [
        "economics", "microeconomics", "macroeconomics", "gdp", "inflation",
        "supply", "demand", "market", "fiscal", "monetary"
    ],
    "Business Studies": [
        "business", "management", "marketing", "finance", "accounting",
        "entrepreneurship", "organization", "operations"
    ],
}

# Unrelated content keywords (triggers lower confidence)
UNRELATED_KEYWORDS = [
    "photo", "image", "picture", "selfie", "portrait",
    "movie", "film", "entertain", "comedy", "drama", "serial",
    "resume", "cv", "curriculum vitae", "job", "career", "hr",
    "invoice", "bill", "receipt", "payment", "due", "amount",
    "advert", "advertisement", "sale", "offer", "discount", "coupon",
    "spam", "free", "win", "prize", "lottery", "congratulations",
    "personal", "private", "password", "login",
    "confidential", "restricted", "secret",
]

# Academic file type indicators
FILE_TYPE_INDICATORS = {
    "notes": ["notes", "study", "revision", "summary", "summary of", "handwritten"],
    "assignments": ["assignment", "homework", "project work", "practical", "lab work"],
    "worksheets": ["worksheet", "practice", "exercise", "problems", "question bank"],
    "research": ["research", "paper", "study on", "investigation", "analysis"],
    "lab manual": ["lab", "manual", "experiment", "procedure"],
    "question paper": ["question paper", "exam", "questionnaire", "previous year"],
    "gate": ["gate", "gate preparation", "gate solution", "gate answer"],
    "educational book": ["book", "textbook", "notes", "chapter", "lesson"],
    "project report": ["project report", "final year", "capstone", "thesis"],
    "tutorial": ["tutorial", "guide", "learn", "how to", "step by step"],
}


class DocumentClassifier:
    """Classifies documents using AI or heuristics."""

    def __init__(self):
        self._ollama_available = self._check_ollama()

    def _check_ollama(self) -> bool:
        """Check if Ollama is running by making a simple HTTP request."""
        try:
            import asyncio

            async def check():
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get("http://localhost:11434/api/tags")
                    return resp.status_code == 200

            try:
                loop = asyncio.get_running_loop()
                return loop.run_until_complete(check())
            except RuntimeError:
                # No running event loop, check synchronously
                try:
                    asyncio.run(check())
                    return True
                except:
                    return False
        except Exception:
            return False

    async def classify(self, request: AIVerifyRequest) -> AIVerifyResponse:
        """Run classification, choosing engine based on settings."""
        if settings.ai_engine == "ollama" and self._ollama_available:
            return await self._classify_with_ollama(request)
        elif settings.ai_engine == "external":
            return await self._classify_with_external(request)
        else:
            return self._classify_with_heuristic(request)

    async def _classify_with_ollama(self, request: AIVerifyRequest) -> AIVerifyResponse:
        """Classify using local Ollama model via HTTP API."""
        prompt = self._build_classification_prompt(request.extracted_text)

        try:
            async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
                resp = await client.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": settings.ai_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "options": {"temperature": 0.0, "num_predict": 512},
                        "stream": False,
                    },
                )

            if resp.status_code != 200:
                log.warning("Ollama returned status %s: %s", resp.status_code, resp.text)
                return self._classify_with_heuristic(request)

            data = resp.json()
            content = data.get("message", {}).get("content", "")
            return self._parse_llm_response(content, request, settings.ai_model)

        except Exception as e:
            log.warning("Ollama classification failed: %s", e)
            return self._classify_with_heuristic(request)

    async def _classify_with_external(self, request: AIVerifyRequest) -> AIVerifyResponse:
        """Classify using external provider (OpenAI or Anthropic)."""
        if settings.openai_api_key:
            return await self._classify_with_openai(request)
        if settings.anthropic_api_key:
            return await self._classify_with_anthropic(request)
        return self._classify_with_heuristic(request)

    async def _classify_with_openai(self, request: AIVerifyRequest) -> AIVerifyResponse:
        """Classify using OpenAI GPT model."""
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        prompt = self._build_classification_prompt(request.extracted_text)

        try:
            response = await client.chat.completions.create(
                model=settings.ai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0.0,
            )

            content = response.choices[0].message.content or "{}"
            return self._parse_llm_response(content, request, settings.ai_model)

        except Exception as e:
            log.warning("OpenAI classification failed: %s", e)
            return self._classify_with_heuristic(request)

    async def _classify_with_anthropic(self, request: AIVerifyRequest) -> AIVerifyResponse:
        """Classify using Anthropic Claude model."""
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        prompt = self._build_classification_prompt(request.extracted_text)

        try:
            response = await client.messages.create(
                model=settings.ai_model,
                max_tokens=512,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text if response.content else "{}"
            return self._parse_llm_response(content, request, settings.ai_model)

        except Exception as e:
            log.warning("Anthropic classification failed: %s", e)
            return self._classify_with_heuristic(request)

    def _build_classification_prompt(self, text: str) -> str:
        """Build a safe classification prompt."""
        truncated = text[:4000]  # Respect token budget
        return f"""Classify this educational document content into ONE category and provide a confidence score.

Categories: Academic Notes, Assignments, Worksheets, Research Papers, Practical Files,
Lab Manuals, Question Papers, GATE Preparation, Educational Books, Project Reports,
Tutorials, Other Educational Content, Unrelated Content, Suspicious Content.

Return JSON only:
{{
  "is_academic": true/false,
  "category": "category name",
  "confidence": 0-100,
  "summary": "brief 1-2 sentence description",
  "detected_subject": "subject name or null",
  "detected_topics": ["topic1", "topic2"],
  "language": "language detected or English",
  "quality_status": "Good/Fair/Poor",
  "reason": "why this classification"
}}

Content:
{truncated}"""

    def _parse_llm_response(
        self, content: str, request: AIVerifyRequest, model_name: str
    ) -> AIVerifyResponse:
        """Parse LLM JSON response into structured output."""
        try:
            data = json.loads(content)
            return AIVerifyResponse(
                is_academic=data.get("is_academic", False),
                category=data.get("category", "Unrelated Content"),
                confidence=int(data.get("confidence", 0)),
                summary=data.get("summary", ""),
                detected_subject=data.get("detected_subject"),
                detected_topics=data.get("detected_topics", []),
                language=data.get("language", "English"),
                quality_status=data.get("quality_status", "Unknown"),
                suspicious_flags=[] if data.get("is_academic") else ["Low academic relevance"],
                ai_recommendation=self._compute_recommendation(data.get("confidence", 0)),
                model_name=model_name,
                raw_response=content,
            )
        except (json.JSONDecodeError, ValueError):
            log.warning("Failed to parse LLM JSON, falling back to heuristic")
            return self._classify_with_heuristic(request)

    def _classify_with_heuristic(self, request: AIVerifyRequest) -> AIVerifyResponse:
        """Pure deterministic classification (always available fallback)."""
        text = request.extracted_text.lower()
        filename = request.filename.lower()
        combined = text + " " + filename

        # Count suspicious keywords
        suspicious_count = sum(1 for kw in UNRELATED_KEYWORDS if kw in combined)

        # Detect academic subjects
        subject_scores: dict[str, int] = {}
        for subject, keywords in ACADEMIC_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in combined)
            if count > 0:
                subject_scores[subject] = count

        # Detect document type
        doc_type = self._detect_document_type(combined)

        # Determine if academic
        is_academic = (
            len(subject_scores) > 0 or
            suspicious_count == 0 and len(text) > 100 and
            ("study" in combined or "notes" in combined or "lecture" in combined or
             "chapter" in combined or "topic" in combined or "textbook" in combined)
        )

        # Detected subject
        detected_subject = None
        if subject_scores:
            detected_subject = max(subject_scores, key=subject_scores.get)

        # Topics from subject keywords
        detected_topics = []
        if detected_subject:
            detected_topics = [kw for kw in ACADEMIC_KEYWORDS.get(detected_subject, []) if kw in text]

        # Confidence calculation
        confidence = 50
        if suspicious_count > 0:
            confidence -= suspicious_count * 10
            is_academic = False

        if subject_scores:
            confidence += len(subject_scores) * 8
            confidence = min(confidence, 85)

        if doc_type:
            confidence += 5

        confidence = max(30, min(95, confidence))

        # Category determination
        if suspicious_count >= 2:
            category = DocumentCategory.SUSPICIOUS_CONTENT.value
            confidence = min(confidence, 40)
        elif not is_academic or confidence < 50:
            category = DocumentCategory.UNRELATED_CONTENT.value
        else:
            category = self._category_from_type(doc_type, detected_subject)

        quality = self._assess_quality(text)

        return AIVerifyResponse(
            is_academic=is_academic,
            category=category,
            confidence=confidence,
            summary=self._generate_summary(text[:500], detected_subject, doc_type),
            detected_subject=detected_subject,
            detected_topics=list(set(detected_topics))[:10],
            language="English",
            quality_status=quality,
            suspicious_flags=[f"Suspicious keyword: {kw}" for kw in UNRELATED_KEYWORDS if kw in combined][:3],
            ai_recommendation=self._compute_recommendation(confidence),
            model_name="heuristic",
        )

    def _detect_document_type(self, text: str) -> str | None:
        """Detect what type of academic document this is."""
        for doc_type, keywords in FILE_TYPE_INDICATORS.items():
            if any(kw in text for kw in keywords):
                return doc_type
        return None

    def _category_from_type(self, doc_type: str | None, subject: str | None) -> str:
        """Map document type to category enum."""
        if not doc_type:
            return DocumentCategory.ACADEMIC_NOTES.value

        type_to_category = {
            "notes": DocumentCategory.ACADEMIC_NOTES.value,
            "assignments": DocumentCategory.ASSIGNMENTS.value,
            "worksheets": DocumentCategory.WORKSHEETS.value,
            "research": DocumentCategory.RESEARCH_PAPERS.value,
            "lab manual": DocumentCategory.LAB_MANUALS.value,
            "question paper": DocumentCategory.QUESTION_PAPERS.value,
            "gate": DocumentCategory.GATE_PREPARATION.value,
            "educational book": DocumentCategory.EDUCATIONAL_BOOKS.value,
            "project report": DocumentCategory.PROJECT_REPORTS.value,
            "tutorial": DocumentCategory.TUTORIALS.value,
        }

        return type_to_category.get(doc_type, DocumentCategory.OTHER_EDUCATIONAL_CONTENT.value)

    def _assess_quality(self, text: str) -> str:
        """Assess document quality based on extracted text."""
        char_count = len(text)
        if char_count < 100:
            return "Poor"
        if char_count < 500:
            return "Fair"
        if char_count < 2000:
            return "Good"
        return "Excellent"

    def _generate_summary(self, text: str, subject: str | None, doc_type: str | None) -> str:
        """Generate a concise summary."""
        clean = re.sub(r"\s+", " ", text[:200]).strip()
        base = f"Document contains "
        if subject:
            base += f"{subject} material"
        elif doc_type:
            base += f"{doc_type} content"
        else:
            base += "educational material"
        return base + "."

    def _compute_recommendation(self, confidence: int) -> str:
        """Compute admin recommendation based on confidence score."""
        if confidence >= 85:
            return "APPROVE_FOR_ADMIN_REVIEW"
        elif confidence >= 60:
            return "MANUAL_REVIEW_REQUIRED"
        else:
            return "FLAG_AS_SUSPICIOUS"


classifier = DocumentClassifier()


async def classify_document(request: AIVerifyRequest) -> AIVerifyResponse:
    """Convenience function to classify a document."""
    return await classifier.classify(request)