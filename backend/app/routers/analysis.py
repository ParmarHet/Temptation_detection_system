"""Analysis API router.

Async job-based architecture:
- POST /api/v1/analyze — submit job, returns job_id immediately
- POST /api/v1/analyze/deep — submit deep analysis job
- GET /api/v1/jobs/{job_id} — poll job status and result
- GET /api/v1/queue — queue statistics
"""

from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.services.job_manager import job_manager

router = APIRouter()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


async def _validate_and_read(file: UploadFile) -> bytes:
    """Validate file and read contents."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {len(contents)} bytes. Maximum: {MAX_FILE_SIZE} bytes",
        )
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    return contents


@router.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    """Submit a fast analysis job (5 techniques, no copy-move).

    Returns job_id immediately. Poll GET /api/v1/jobs/{job_id} for results.
    """
    contents = await _validate_and_read(file)
    job_id = job_manager.submit_job(contents, file.filename, deep=False)

    return JSONResponse(content={
        "job_id": job_id,
        "status": "queued",
        "message": "Analysis job submitted. Poll /api/v1/jobs/" + job_id + " for results.",
    })


@router.post("/analyze/deep")
async def analyze_document_deep(file: UploadFile = File(...)):
    """Submit a deep analysis job (all 6 techniques including copy-move).

    Returns job_id immediately. May take 30-120 seconds.
    """
    contents = await _validate_and_read(file)
    job_id = job_manager.submit_job(contents, file.filename, deep=True)

    return JSONResponse(content={
        "job_id": job_id,
        "status": "queued",
        "message": "Deep analysis job submitted. Poll /api/v1/jobs/" + job_id + " for results.",
    })


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Poll job status and get result when complete.

    Returns:
        - status: queued | processing | completed | failed
        - result: full analysis response (only when completed)
        - error: error message (only when failed)
    """
    status = job_manager.get_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JSONResponse(content=status)


@router.get("/queue")
async def get_queue_stats():
    """Get current queue statistics."""
    return JSONResponse(content=job_manager.get_queue_stats())
