from contextlib import asynccontextmanager
import os
import time
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_CONFIG, MAX_CONTENT_LENGTH
from app.database.connection import Database
from app.routes.document_routes import document_router
from app.routes.image_routes import image_router
from app.routes.agent_routes import agent_router
from app.agents.doc_agent import DEFAULT_PROMPTS
from app.database import prompt_store
from app.utils.logging_config import setup_logging

logger = setup_logging()
_rate_window_start = time.time()
_rate_hits: dict[str, int] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.initialize_async()
    prompt_store.seed_defaults(DEFAULT_PROMPTS)
    yield
    await Database.close_async()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    # Initialize FastAPI application
    app = FastAPI(
        title="AML Backend 2",
        description="Document & Image Corroboration API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_CONFIG.get("origins", ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def basic_rate_limit(request, call_next):
        global _rate_window_start
        now = time.time()
        window_seconds = 60
        limit = int(os.getenv("RATE_LIMIT_PER_MIN", "120"))
        if now - _rate_window_start >= window_seconds:
            _rate_hits.clear()
            _rate_window_start = now

        client = request.client.host if request.client else "unknown"
        key = f"{client}:{request.url.path}"
        count = _rate_hits.get(key, 0) + 1
        _rate_hits[key] = count
        if count > limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please retry shortly."},
            )
        return await call_next(request)

    # Include routers
    app.include_router(document_router, prefix="/api/documents", tags=["documents"])
    app.include_router(image_router, prefix="/api/images", tags=["images"])
    app.include_router(agent_router, prefix="/api", tags=["agent"])

    @app.get("/")
    async def root():
        return {"message": "AML Backend 2 - Document & Image Corroboration API"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app
