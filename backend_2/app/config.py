import os
from typing import Dict, Any

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5002))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "*")
CORS_CONFIG: Dict[str, Any] = {
    "origins": [o.strip() for o in cors_origins.split(",")] if cors_origins else ["*"],
    "methods": ["*"],
    "headers": ["*"],
}

# File upload configuration
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# AI/ML API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_BASE = os.getenv("GROQ_API_BASE", "")

# Sightengine API configuration for AI image detection
SIGHTENGINE_API_USER = os.getenv("SIGHTENGINE_API_USER", "")
SIGHTENGINE_API_SECRET = os.getenv("SIGHTENGINE_API_SECRET", "")
SIGHTENGINE_ENABLED = bool(SIGHTENGINE_API_USER and SIGHTENGINE_API_SECRET)

# SerpAPI configuration for reverse image search
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
SERPAPI_ENABLED = bool(SERPAPI_API_KEY)

# Document processing configuration
ALLOWED_DOCUMENT_TYPES = [".pdf", ".doc", ".docx", ".txt"]
ALLOWED_IMAGE_TYPES = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
UPLOAD_DIRECTORY = "uploads/"

# Google Cloud Vision API configuration
GOOGLE_CLOUD_VISION_ENABLED = (
    os.getenv("GOOGLE_CLOUD_VISION_ENABLED", "True").lower() == "true"
)
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
GOOGLE_VISION_API_KEY = os.getenv("GOOGLE_VISION_API_KEY", "")

# PostgreSQL/Supabase configuration
DATABASE_URL = os.getenv("DATABASE_URL", "")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
