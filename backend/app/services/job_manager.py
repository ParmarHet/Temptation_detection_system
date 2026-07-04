"""Async job manager for handling concurrent document analysis.

Uses a thread pool to run CPU-bound analysis work without blocking
the event loop, allowing 20-30 concurrent users.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    job_id: str
    filename: str
    status: JobStatus = JobStatus.QUEUED
    deep: bool = False
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    @property
    def elapsed(self) -> float:
        if self.started_at is None:
            return 0
        end = self.completed_at or time.time()
        return round(end - self.started_at, 2)

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "filename": self.filename,
            "status": self.status.value,
            "deep": self.deep,
            "elapsed_seconds": self.elapsed,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class JobManager:
    """Manages async document analysis jobs with thread pool execution."""

    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="docshield-analysis",
        )
        self._jobs: dict[str, Job] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        logger.info("JobManager initialized: max_workers=%d", max_workers)

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        """Store the event loop for scheduling."""
        self._loop = loop

    def submit_job(self, image_bytes: bytes, filename: str, deep: bool = False) -> str:
        """Submit a new analysis job. Returns job_id immediately."""
        job_id = str(uuid.uuid4())
        job = Job(job_id=job_id, filename=filename, deep=deep)
        self._jobs[job_id] = job

        # Schedule the work in the thread pool
        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        asyncio.run_coroutine_threadsafe(
            self._process_job(job_id, image_bytes, filename, deep),
            self._loop,
        )

        logger.info("Job submitted: job_id=%s filename=%s deep=%s", job_id, filename, deep)
        return job_id

    async def _process_job(self, job_id: str, image_bytes: bytes, filename: str, deep: bool):
        """Process a job in the thread pool."""
        job = self._jobs[job_id]
        job.status = JobStatus.PROCESSING
        job.started_at = time.time()
        logger.info("Job started: job_id=%s", job_id)

        try:
            # Run CPU-bound work in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor,
                self._run_analysis_sync,
                image_bytes,
                filename,
                deep,
            )

            job.result = result
            job.status = JobStatus.COMPLETED
            job.completed_at = time.time()
            logger.info(
                "Job completed: job_id=%s elapsed=%.2fs score=%.2f",
                job_id, job.elapsed, result.get("overall_score", 0),
            )

        except Exception as e:
            job.error = str(e)
            job.status = JobStatus.FAILED
            job.completed_at = time.time()
            logger.exception("Job failed: job_id=%s", job_id)

    def _run_analysis_sync(self, image_bytes: bytes, filename: str, deep: bool) -> dict:
        """Synchronous analysis runner (called in thread pool)."""
        # Import here to avoid circular imports and ensure fresh state
        from app.services.pipeline import run_analysis
        return run_analysis(image_bytes, filename, deep=deep)

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def get_status(self, job_id: str) -> Optional[dict]:
        """Get job status."""
        job = self.get_job(job_id)
        if job is None:
            return None
        status = job.to_dict()
        if job.status == JobStatus.COMPLETED and job.result:
            status["result"] = job.result
        if job.status == JobStatus.FAILED:
            status["error"] = job.error
        return status

    def get_queue_stats(self) -> dict:
        """Get current queue statistics."""
        counts = {"queued": 0, "processing": 0, "completed": 0, "failed": 0}
        for job in self._jobs.values():
            counts[job.status.value] += 1
        return {
            "total": len(self._jobs),
            "by_status": counts,
            "max_workers": self._executor._max_workers,
        }

    def cleanup_old_jobs(self, max_age_seconds: int = 3600):
        """Remove jobs older than max_age_seconds."""
        now = time.time()
        to_remove = [
            jid for jid, job in self._jobs.items()
            if job.completed_at and (now - job.completed_at) > max_age_seconds
        ]
        for jid in to_remove:
            del self._jobs[jid]
        if to_remove:
            logger.info("Cleaned up %d old jobs", len(to_remove))


# Global singleton
job_manager = JobManager(max_workers=4)
