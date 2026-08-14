from __future__ import annotations

import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found")

def _parse_model_candidates(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    candidates = [model.strip() for model in value.split(",") if model.strip()]
    return tuple(dict.fromkeys(candidates))


def _build_model_candidates() -> tuple[str, ...]:
    configured_models = _parse_model_candidates(os.getenv("GROQ_MODELS"))
    if configured_models:
        return configured_models

    primary_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    fallback_models = ("qwen/qwen3.6-27b", "openai/gpt-oss-120b")
    return tuple(dict.fromkeys((primary_model, *fallback_models)))


GROQ_MODEL_CANDIDATES = _build_model_candidates()
GROQ_MODEL = GROQ_MODEL_CANDIDATES[0]
APP_NAME = os.getenv("APP_NAME", "Resume Parser API")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")

JOB_DESCRIPTION_MAX_CHARS = int(os.getenv("JOB_DESCRIPTION_MAX_CHARS", "8000"))
RESUME_TEXT_MAX_CHARS = int(os.getenv("RESUME_TEXT_MAX_CHARS", "12000"))

DEFAULT_CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173",
    ).split(",")
    if origin.strip()
]

ALLOWED_UPLOAD_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

client = Groq(api_key=GROQ_API_KEY)
model = GROQ_MODEL
