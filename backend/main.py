"""FastAPI application entry point for CloudSync Log Intelligence System."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import api_router

# Configure production logging format
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cloudsync")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup and shutdown lifecycle events for the application."""
    logger.info("Starting CloudSync Behavioral Log Intelligence System API...")
    yield
    logger.info("Shutting down CloudSync API server.")


def create_app() -> FastAPI:
    """Application factory for configuring and building the FastAPI instance."""
    app = FastAPI(
        title="CloudSync Behavioral Log Intelligence System",
        description=(
            "Production-grade cybersecurity behavioral log intelligence architecture "
            "providing log collection, event normalization, risk scoring, and SIEM analytics."
        ),
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router hierarchy
    app.include_router(api_router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    logger.info("Running CloudSync API server on %s:%d", host, port)
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)