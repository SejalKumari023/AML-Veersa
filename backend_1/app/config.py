import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# CORS configuration
CORS_CONFIG: Dict[str, Any] = {
    "origins": ["*"],
    "methods": ["*"],
    "headers": ["*"],
}

# File upload configuration
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB