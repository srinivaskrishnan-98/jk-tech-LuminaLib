from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.core.database import engine
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import setup_logging

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup and shutdown hooks."""
    settings: Settings = app.state.settings

    setup_logging(debug=settings.DEBUG)
    logger.info("starting_luminalib", storage=settings.STORAGE_BACKEND, llm=settings.LLM_PROVIDER)

    # Initialize MinIO bucket if using MinIO storage
    if settings.STORAGE_BACKEND == "minio":
        from app.infrastructure.storage.minio_storage import MinIOStorage

        storage = MinIOStorage(settings)
        await storage.ensure_bucket_exists()
        logger.info("minio_bucket_ready", bucket=settings.MINIO_BUCKET_NAME)

    yield

    # Shutdown
    await engine.dispose()
    logger.info("luminalib_shutdown")


def create_app() -> FastAPI:
    """Application factory."""
    settings = Settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "Intelligent Library System with GenAI-powered"
            " summarization and recommendations"
        ),
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.settings = settings

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    register_exception_handlers(app)

    # Routers
    from app.api.router import api_router

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
