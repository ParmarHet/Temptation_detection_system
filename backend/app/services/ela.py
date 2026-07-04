"""Error Level Analysis (ELA) technique module.

Detects regions with inconsistent JPEG compression history by re-saving
the image at a known quality factor and measuring per-pixel differences.
Regions that were edited after original save show higher error levels.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from PIL import Image

from app.config import settings


def compute_ela(
    img: np.ndarray,
    quality: int = None,
    gain: float = None,
    threshold: float = None,
) -> Tuple[np.ndarray, dict]:
    """Compute Error Level Analysis on an image.

    Args:
        img: BGR image (uint8)
        quality: JPEG quality for re-save (default from config)
        gain: amplification factor for differences (default from config)
        threshold: anomaly threshold (default from config)

    Returns:
        (ela_heatmap, details_dict)
    """
    quality = quality or settings.ELA_QUALITY
    gain = gain or settings.ELA_GAIN
    threshold = threshold or settings.ELA_THRESHOLD

    # Convert to RGB PIL Image for JPEG re-save
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)

    # Re-save at known quality
    buffer = io.BytesIO()
    pil_img.save(buffer, format="JPEG", quality=quality, subsampling=0)
    buffer.seek(0)
    resaved = Image.open(buffer)
    resaved_array = np.array(resaved).astype(np.float64)

    # Compute per-pixel absolute difference
    original_array = rgb.astype(np.float64)
    diff = np.abs(original_array - resaved_array)

    # Amplify and average across channels
    ela_raw = np.mean(diff, axis=2) * gain

    # Normalize to 0-255
    ela_normalized = np.clip(ela_raw, 0, 255).astype(np.uint8)

    # Apply Gaussian blur to smooth quantization noise
    ela_smoothed = cv2.GaussianBlur(ela_normalized, (5, 5), 0)

    # Compute anomaly score
    total_pixels = ela_smoothed.shape[0] * ela_smoothed.shape[1]
    suspicious_pixels = np.sum(ela_smoothed > threshold * 255)
    anomaly_ratio = suspicious_pixels / total_pixels

    # Find contours of suspicious regions
    _, binary = cv2.threshold(ela_smoothed, int(threshold * 255), 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter small noise contours
    min_area = total_pixels * 0.001  # 0.1% of image
    significant_contours = [c for c in contours if cv2.contourArea(c) > min_area]

    # Compute region-level scores
    regions = []
    for contour in significant_contours:
        x, y, w, h = cv2.boundingRect(contour)
        roi = ela_smoothed[y:y + h, x:x + w]
        region_score = float(np.mean(roi) / 255 * 100)
        regions.append({
            "bbox": [x, y, w, h],
            "score": round(region_score, 2),
            "area": int(cv2.contourArea(contour)),
        })

    # Overall score: weighted by anomaly ratio and mean intensity
    mean_ela = float(np.mean(ela_smoothed)) / 255 * 100
    score = min(100, (anomaly_ratio * 500 + mean_ela * 0.5) * 100)
    score = max(0, min(100, score))

    details = {
        "mean_error_level": round(mean_ela, 4),
        "anomaly_pixel_ratio": round(anomaly_ratio, 6),
        "regions_flagged": len(regions),
        "regions": regions[:20],  # Top 20 regions
        "quality_used": quality,
        "gain_used": gain,
    }

    return ela_smoothed, details, score


def create_ela_heatmap(img: np.ndarray, ela_result: np.ndarray) -> np.ndarray:
    """Create a colored ELA heatmap overlay on the original image."""
    colored = cv2.applyColorMap(ela_result, cv2.COLORMAP_JET)
    blended = cv2.addWeighted(img, 0.6, colored, 0.4, 0)
    return blended
