"""FastAPI application entry point.

Configures CORS, async job system, and API routes.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import settings
from app.routers import analysis
from app.services.job_manager import job_manager

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    app = FastAPI(
        title="Temptation Detection System API",
        description="Async rule-based document tamper detection",
        version="1.0.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize job manager with event loop
    @app.on_event("startup")
    async def startup():
        loop = asyncio.get_event_loop()
        job_manager.set_loop(loop)
        logger.info("JobManager started with event loop")

    @app.on_event("shutdown")
    async def shutdown():
        logger.info("Shutting down JobManager...")

    # Routes
    app.include_router(analysis.router, prefix="/api/v1")

    @app.get("/api/v1/health")
    async def health():
        stats = job_manager.get_queue_stats()
        return {
            "status": "ok",
            "version": "1.0.0",
            "queue": stats,
        }

    @app.get("/api/v1/heatmap/{analysis_id}/{technique}")
    async def get_heatmap(analysis_id: str, technique: str):
        """Serve a saved heatmap image."""
        heatmap_path = settings.HEATMAP_DIR / analysis_id / f"{technique}.png"
        if heatmap_path.exists():
            return FileResponse(str(heatmap_path), media_type="image/png")
        return {"error": "Heatmap not found"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
