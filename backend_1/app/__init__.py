from contextlib import asynccontextmanager
import os
import time
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_CONFIG, MAX_CONTENT_LENGTH
from app.database.connection import Database, PostgresDatabase
from app.database.neo4j_connection import Neo4jDatabase
from app.routes.data_routes import data_router
from app.routes.user_routes import user_router
from app.routes.rules_routes import rule_router
from app.routes.customer_routes import customer_router
from app.routes.agent_routes import agent_router
from app.utils.logging_config import setup_logging

logger = setup_logging()
_rate_window_start = time.time()
_rate_hits: dict[str, int] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup: Initialize PostgreSQL database connection pool
    logger.info("Initializing PostgreSQL database connection pool...")
    try:
        await PostgresDatabase.initialize()
        await PostgresDatabase.seed_default_prompts()
        logger.info("PostgreSQL database connection pool initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize PostgreSQL: {e}")
        logger.warning("Running without PostgreSQL - rules will not be persisted")

    # Initialize Neo4j database connection
    logger.info("Initializing Neo4j graph database connection...")
    neo4j_db = Neo4jDatabase()
    try:
        await neo4j_db.initialize()
        logger.info("Neo4j graph database connection initialized")
        # Store instance in app state for access in routes
        app.state.neo4j_db = neo4j_db
    except Exception as e:
        logger.warning(f"Failed to initialize Neo4j: {e}")
        logger.warning(
            "Running without Neo4j - transaction relationships will not be stored"
        )
        app.state.neo4j_db = None

    # Initialize in-memory database for legacy support
    Database.initialize()

    yield

    # Shutdown: Close PostgreSQL connection pool
    logger.info("Closing PostgreSQL database connection pool...")
    try:
        await PostgresDatabase.close()
        logger.info("PostgreSQL database connection pool closed")
    except Exception as e:
        logger.warning(f"Error closing PostgreSQL pool: {e}")

    # Shutdown: Close Neo4j connection
    logger.info("Closing Neo4j connection...")
    try:
        if hasattr(app.state, "neo4j_db") and app.state.neo4j_db:
            await app.state.neo4j_db.close()
            logger.info("Neo4j connection closed")
    except Exception as e:
        logger.warning(f"Error closing Neo4j connection: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    # Initialize FastAPI application
    app = FastAPI(
        title="AML Backend 1",
        description="Real-Time AML Monitoring & Alerts API",
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
        # Keep this light for demo/public MVP.
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
    app.include_router(user_router, prefix="/api/users", tags=["users"])
    app.include_router(data_router, prefix="/api/data", tags=["data"])
    app.include_router(rule_router, prefix="/api/rules", tags=["rules"])
    app.include_router(customer_router, prefix="/api/customers", tags=["customers"])
    app.include_router(agent_router, prefix="/api", tags=["agent"])

    @app.get("/")
    async def root():
        return {"message": "AML Backend 1 - Real-Time Monitoring API"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app
