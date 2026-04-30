from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_CONFIG, MAX_CONTENT_LENGTH
from app.database.connection import Database
from app.routes.data_routes import data_router
from app.routes.user_routes import user_router
from app.utils.logging_config import setup_logging

logger = setup_logging()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    # Initialize FastAPI application
    app = FastAPI(
        title="AML Backend 1",
        description="Real-Time AML Monitoring & Alerts API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_CONFIG.get("origins", ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize database connection
    Database.initialize()

    # Include routers
    app.include_router(user_router, prefix="/api/users", tags=["users"])
    app.include_router(data_router, prefix="/api/data", tags=["data"])

    @app.get("/")
    async def root():
        return {"message": "AML Backend 1 - Real-Time Monitoring API"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app
