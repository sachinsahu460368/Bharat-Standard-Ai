"""FastAPI application entry point."""

from __future__ import annotations

import logging
import time
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analyze, health, reports, search, standards
from app.core.config import settings
from app.core.exceptions import AppError, app_error_handler
from app.core.logging import generate_request_id, request_id_var, setup_logging
from app.services.lexical_search_service import lexical_search_service
from app.services.semantic_search_service import semantic_search_service
from app.services.standards_service import standards_service

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Load data services on startup, clean up on shutdown."""
    logger.info("Loading standards knowledge base…")
    standards_service.load()

    logger.info("Building BM25 lexical search index…")
    lexical_search_service.build(standards_service)

    if not settings.render_demo_mode:
        logger.info("Initializing semantic search service…")
        semantic_search_service.initialize()
        if not semantic_search_service.has_index:
            logger.info("Building FAISS semantic search index…")
            semantic_search_service.build_or_refresh_index()
    else:
        logger.info("Skipping semantic search service initialization due to RENDER_DEMO_MODE.")

    logger.info(
        "Startup complete — %d standards loaded, lexical index ready, semantic index ready: %s.",
        standards_service.count,
        semantic_search_service.is_ready,
    )
    yield
    # Shutdown — nothing to clean for now
    logger.info("Shutting down.")


def create_app() -> FastAPI:
    application = FastAPI(
        title="Bharat Standards AI",
        description=(
            "AI-Powered Recommendation Engine for Identifying "
            "Applicable Indian Standards for Procurement Specifications."
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    if settings.frontend_origin:
        origins_from_env = [o.strip() for o in settings.frontend_origin.split(",") if o.strip()]
        allowed_origins.extend(origins_from_env)

    # Remove duplicates while preserving order
    allowed_origins = list(dict.fromkeys(allowed_origins))

    application.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-Id"],
    )

    # Exception handler
    application.add_exception_handler(AppError, app_error_handler)

    # Request logging middleware
    @application.middleware("http")
    async def request_logging(request: Request, call_next):  # noqa: ANN001
        rid = generate_request_id()
        request_id_var.set(rid)
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = round((time.perf_counter() - start) * 1000, 1)
        logger.info(
            "%s %s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        response.headers["X-Request-Id"] = rid
        return response

    # Routes
    application.include_router(health.router)
    application.include_router(analyze.router)
    application.include_router(search.router)
    application.include_router(standards.router)
    application.include_router(reports.router)

    return application


app = create_app()
