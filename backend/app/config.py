"""Centralised configuration for the MU STUDY HUB AI verification service.

All values come from environment variables (see ../.env.example) with sane
defaults. The AI engine is designed to degrade gracefully: if no LLM is
reachable the classifier falls back to a deterministic heuristic that still
produces a structured, explainable verdict.
"""
from __future__ import annotations

import os
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from the environment."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    # --- Database -----------------------------------------------------------
    database_url: str = "sqlite+aiosqlite:///./mu_study_hub.db"
    db_echo: bool = False

    # --- Storage ------------------------------------------------------------
    storage_local_path: str = "./storage/uploads"
    storage_max_bytes: int = 52_428_800  # 50 MiB

    # --- AI / classification ------------------------------------------------
    ai_engine: str = "ollama"  # ollama | external | heuristic
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ai_model: str = "qwen2.5:7b-instruct"
    ai_timeout_seconds: int = 45
    ai_min_confidence_to_auto_review: int = 60

    # --- OCR ----------------------------------------------------------------
    ocr_enabled: bool = True
    ocr_language: str = "eng+hin"
    ocr_dpi: int = 300
    ocr_max_pages: int = 12

    # --- Security -----------------------------------------------------------
    allowed_mime_types: str = "application/pdf"
    max_pdf_pages: int = 200
    hash_algorithm: str = "sha256"
    cors_origins: str = "http://localhost:3000"
    secret_key: str = "change-me-in-production"
    access_token_minutes: int = 60
    admin_users: str = "admin"

    # --- Rate limiting ------------------------------------------------------
    rate_limit_per_minute: int = 60

    # --- Misc ---------------------------------------------------------------
    app_name: str = "MU STUDY HUB AI Verification Bot"
    app_version: str = "1.0.0"
    environment: str = "development"

    @property
    def allowed_mime_list(self) -> List[str]:
        return [m.strip() for m in self.allowed_mime_types.split(",") if m.strip()]

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def admin_user_list(self) -> List[str]:
        return [u.strip().lower() for u in self.admin_users.split(",") if u.strip()]


settings = Settings()