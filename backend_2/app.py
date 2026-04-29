#!/usr/bin/env python3
"""
Main application entry point
"""

from dotenv import load_dotenv
import uvicorn

# Load environment variables from .env file
load_dotenv()

from app import create_app
from app.config import DEBUG, HOST, PORT

# Create FastAPI application
app = create_app()

if __name__ == "__main__":
    # Start the Uvicorn server
    uvicorn.run(
        "app:create_app",
        factory=True,
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info" if not DEBUG else "debug"
    )
