from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TechniqueResult(BaseModel):
    score: float = Field(..., ge=0, le=100)
    details: dict = Field(default_factory=dict)
    heatmap_url: Optional[str] = None
    skipped: bool = False
    skip_reason: Optional[str] = None


class ELAResult(TechniqueResult):
    regions_flagged: int = 0
    mean_error_level: float = 0.0


class NoiseResult(TechniqueResult):
    blocks_flagged: int = 0
    total_blocks: int = 0
    global_noise_std: float = 0.0


class CopyMoveResult(TechniqueResult):
    matches_found: int = 0
    match_details: list = Field(default_factory=list)


class MetadataResult(TechniqueResult):
    flags: list = Field(default_factory=list)
    software_tag: Optional[str] = None
    has_exif: bool = False


class JPEGGhostResult(TechniqueResult):
    double_compression_detected: bool = False
    detected_qf: Optional[int] = None


class OCRResult(TechniqueResult):
    words_flagged: int = 0
    lines_flagged: int = 0
    flagged_regions: list = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    image_width: int
    image_height: int
    format: str
    overall_score: float
    verdict: str
    techniques: dict
    fused_heatmap_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
