import os
from typing import Dict, Any

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# CORS configuration
CORS_CONFIG: Dict[str, Any] = {
    "origins": ["*"],
    "methods": ["*"],
    "headers": ["*"],
}

# File upload configuration
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# AI/ML API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

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