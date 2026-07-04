"""Fusion / Scoring layer module.

Combines outputs from all 6 techniques into a single tamper probability
score (0-100) and generates a fused heatmap overlay showing which regions
triggered which signal.
"""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np

from app.config import settings
from app.utils.heatmap import create_fused_overlay, save_heatmap
from pathlib import Path


def fuse_scores(
    technique_scores: dict[str, float],
    technique_details: dict[str, dict],
    image_format: str,
) -> Tuple[float, str, dict]:
    """Fuse technique scores into overall tamper probability.

    Uses weighted rule-based scoring with dynamic weight adjustment
    based on image format and technique applicability.

    Args:
        technique_scores: dict of technique_name -> score (0-100)
        technique_details: dict of technique_name -> details dict
        image_format: input image format (jpg, png, pdf)

    Returns:
        (overall_score, verdict, fusion_details)
    """
    weights = dict(settings.FUSION_WEIGHTS)

    # Dynamic weight adjustment based on format
    format_lower = image_format.lower()
    is_jpeg = format_lower in ("jpg", "jpeg")

    if not is_jpeg:
        # ELA and JPEG ghost are unreliable on non-JPEG inputs
        if "ela" in weights:
            weights["ela"] = weights["ela"] * 0.3  # Reduce but don't eliminate
        if "jpeg_ghost" in weights:
            weights["jpeg_ghost"] = 0  # Completely skip

    # Check if technique was skipped
    for tech in list(weights.keys()):
        if tech in technique_details:
            detail = technique_details[tech]
            if isinstance(detail, dict) and detail.get("skipped"):
                weights[tech] = 0

    # Normalize weights to sum to 1.0
    total_weight = sum(weights.values())
    if total_weight > 0:
        weights = {k: v / total_weight for k, v in weights.items()}
    else:
        # Fallback: equal weights for all available techniques
        available = [k for k in technique_scores if technique_scores[k] > 0]
        if available:
            w = 1.0 / len(available)
            weights = {k: w for k in available}

    # Weighted sum
    overall_score = 0.0
    contributing_techniques = {}
    for tech, weight in weights.items():
        score = technique_scores.get(tech, 0)
        contribution = weight * score
        overall_score += contribution
        contributing_techniques[tech] = {
            "raw_score": round(score, 2),
            "weight": round(weight, 4),
            "contribution": round(contribution, 2),
        }

    overall_score = max(0, min(100, overall_score))

    # Determine verdict
    if overall_score <= settings.VERDICT_SUSPICIOUS - 1:
        verdict = "clean"
    elif overall_score <= settings.VERDICT_TAMPERED - 1:
        verdict = "suspicious"
    else:
        verdict = "likely_tampered"

    fusion_details = {
        "weights_used": {k: round(v, 4) for k, v in weights.items()},
        "contributing_techniques": contributing_techniques,
        "format_adjusted": not is_jpeg,
        "verdict_thresholds": {
            "clean": f"0-{settings.VERDICT_SUSPICIOUS - 1}",
            "suspicious": f"{settings.VERDICT_SUSPICIOUS}-{settings.VERDICT_TAMPERED - 1}",
            "likely_tampered": f"{settings.VERDICT_TAMPERED}-100",
        },
    }

    return overall_score, verdict, fusion_details


def generate_fused_heatmap(
    original: np.ndarray,
    heatmaps: dict[str, np.ndarray],
    scores: dict[str, float],
    analysis_id: str,
    output_dir: Path,
) -> str:
    """Generate and save fused heatmap overlay.

    Returns the relative URL path to the saved heatmap.
    """
    fused = create_fused_overlay(original, heatmaps, scores)

    # Save heatmap (endpoint expects {technique}.png)
    heatmap_path = output_dir / "fused.png"
    save_heatmap(fused, heatmap_path)

    return f"/api/v1/heatmap/{analysis_id}/fused"


def generate_individual_heatmaps(
    original: np.ndarray,
    heatmaps: dict[str, np.ndarray],
    analysis_id: str,
    output_dir: Path,
) -> dict[str, str]:
    """Generate and save individual technique heatmaps.

    Returns dict of technique_name -> URL path.
    """
    from app.utils.heatmap import create_overlay

    urls = {}
    for name, heatmap in heatmaps.items():
        if heatmap is None:
            continue

        overlay = create_overlay(original, heatmap)
        # Endpoint expects {technique}.png
        path = output_dir / f"{name}.png"
        save_heatmap(overlay, path)
        urls[name] = f"/api/v1/heatmap/{analysis_id}/{name}"

    return urls
