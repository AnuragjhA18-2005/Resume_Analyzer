from __future__ import annotations

import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found")

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
APP_NAME = os.getenv("APP_NAME", "Resume Parser API")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")

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
