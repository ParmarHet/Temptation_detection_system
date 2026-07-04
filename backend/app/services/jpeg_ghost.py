"""Double JPEG Compression / DCT Coefficient Analysis technique module.

Detects when a JPEG has been decompressed and re-compressed at a different
quality factor, which leaves periodic artifacts in DCT coefficient histograms.
Only applicable to images with JPEG compression history.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Tuple, Optional

import cv2
import numpy as np

from app.config import settings


def compute_jpeg_ghost_analysis(
    img: np.ndarray,
    image_bytes: bytes = None,
    filename: str = "",
) -> Tuple[Optional[np.ndarray], dict, float]:
    """Analyze DCT coefficients for double JPEG compression artifacts.

    Args:
        img: BGR image (uint8)
        image_bytes: raw file bytes for JPEG header parsing
        filename: original filename

    Returns:
        (heatmap_or_None, details_dict, score)
    """
    # Check if input is JPEG
    is_jpeg = _is_jpeg(image_bytes, filename)
    if not is_jpeg:
        return None, {
            "score": 0,
            "double_compression_detected": False,
            "skipped": True,
            "skip_reason": "Input is not a JPEG image — double compression analysis not applicable",
        }, 0

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    h, w = gray.shape

    # Extract quantization table from JPEG header
    qtable = _extract_quantization_table(image_bytes)

    # Compute DCT coefficient histograms
    histograms = _compute_dct_histograms(gray)

    # Detect periodic patterns (comb artifacts) indicating double compression
    double_comp_score, detected_qf = _detect_double_compression(histograms, qtable)

    # Create visualization heatmap
    if double_comp_score > 20:
        heatmap = _create_ghost_heatmap(gray, histograms)
    else:
        heatmap = None

    details = {
        "double_compression_detected": double_comp_score > 30,
        "detected_qf": detected_qf,
        "quantization_table": str(qtable) if qtable else None,
        "histogram_analysis": {
            "num_bands_analyzed": len(histograms),
            "peak_periodicity_scores": {
                band: round(score, 4)
                for band, score in histograms.items()
            } if isinstance(histograms, dict) else {},
        },
    }

    return heatmap, details, double_comp_score


def _is_jpeg(image_bytes: bytes, filename: str) -> bool:
    """Check if the input is a JPEG image."""
    suffix = Path(filename).suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        return True
    # Check magic bytes
    if image_bytes and len(image_bytes) >= 2:
        return image_bytes[:2] == b"\xff\xd8"
    return False


def _extract_quantization_table(image_bytes: bytes) -> Optional[dict]:
    """Extract quantization table from JPEG header."""
    try:
        import io
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        if not hasattr(img, "quantization"):
            return None

        qt = img.quantization
        if qt:
            return {"table": str(qt)}
        return None
    except Exception:
        return None


def _compute_dct_histograms(gray: np.ndarray) -> dict:
    """Compute DCT coefficient histograms for different frequency bands.

    Divides each 8x8 DCT block into frequency bands and builds
    histograms for each band.
    """
    h, w = gray.shape
    # Ensure dimensions are multiples of 8
    h_crop = (h // 8) * 8
    w_crop = (w // 8) * 8
    cropped = gray[:h_crop, :w_crop]

    # Reshape into 8x8 blocks
    blocks = cropped.reshape(h_crop // 8, 8, w_crop // 8, 8)
    blocks = blocks.transpose(0, 2, 1, 3).reshape(-1, 8, 8)

    # Compute DCT for all blocks
    dct_blocks = np.zeros_like(blocks, dtype=np.float64)
    for i in range(len(blocks)):
        dct_blocks[i] = cv2.dct(blocks[i].astype(np.float64))

    # Extract frequency bands
    band_names = {
        "dc": (0, 0),
        "low": (1, 1),
        "mid": (3, 3),
        "high": (5, 5),
    }

    histograms = {}
    for band_name, (row, col) in band_names.items():
        coeffs = dct_blocks[:, row, col]
        # Build histogram of coefficient values
        hist, _ = np.histogram(coeffs, bins=settings.JPEG_GHOST_DCT_BINS, range=(-50, 50))
        histograms[band_name] = hist

    return histograms


def _detect_double_compression(
    histograms: dict, qtable: Optional[dict]
) -> Tuple[float, Optional[int]]:
    """Detect double compression from DCT histogram periodicity.

    Double quantization creates a "comb" pattern in DCT histograms —
    alternating peaks and empty bins. We detect this via autocorrelation.
    """
    scores = []

    for band_name, hist in histograms.items():
        if band_name == "dc":
            continue  # DC band is unreliable for this analysis

        # Compute autocorrelation of histogram
        hist_float = hist.astype(np.float64)
        hist_centered = hist_float - np.mean(hist_float)

        autocorr = np.correlate(hist_centered, hist_centered, mode="full")
        autocorr = autocorr[len(autocorr) // 2:]  # Keep positive lags
        autocorr = autocorr / max(autocorr[0], 1e-6)  # Normalize

        # Look for periodic peaks (skip lag 0)
        if len(autocorr) > 4:
            # Find peaks at lags 2-20
            peak_lags = autocorr[2:min(20, len(autocorr))]
            if len(peak_lags) > 0:
                max_peak = np.max(peak_lags)
                if max_peak > 0.3:  # Threshold for periodicity
                    scores.append(max_peak)

    if not scores:
        return 0, None

    # Overall double compression score
    avg_score = np.mean(scores)
    double_comp_score = min(100, avg_score * 200)

    # Estimate quality factor if possible
    detected_qf = None
    if qtable and double_comp_score > 30:
        detected_qf = _estimate_qf_from_table(qtable)

    return double_comp_score, detected_qf


def _estimate_qf_from_table(qtable: dict) -> Optional[int]:
    """Estimate JPEG quality factor from quantization table."""
    try:
        table_str = str(qtable.get("table", ""))
        # Simple heuristic: average quantization values correlate with QF
        # Higher values = lower quality
        import re
        values = [int(x) for x in re.findall(r"\d+", table_str)]
        if values:
            avg = np.mean(values)
            # Rough mapping: avg 1-5 → QF ~95, avg 5-10 → QF ~85, avg 10-20 → QF ~75
            if avg < 5:
                return 95
            elif avg < 10:
                return 85
            elif avg < 20:
                return 75
            elif avg < 30:
                return 65
            else:
                return 50
    except Exception:
        pass
    return None


def _create_ghost_heatmap(gray: np.ndarray, histograms: dict) -> np.ndarray:
    """Create a spatial heatmap showing double compression artifact regions."""
    h, w = gray.shape
    heatmap = np.zeros((h, w), dtype=np.float64)

    # Analyze per-block double compression
    h_crop = (h // 8) * 8
    w_crop = (w // 8) * 8
    cropped = gray[:h_crop, :w_crop]

    blocks = cropped.reshape(h_crop // 8, 8, w_crop // 8, 8)
    blocks = blocks.transpose(0, 2, 1, 3).reshape(-1, 8, 8)

    n_blocks_y = h_crop // 8
    n_blocks_x = w_crop // 8

    for i, block in enumerate(blocks):
        by = i // n_blocks_x
        bx = i % n_blocks_x
        if by >= n_blocks_y or bx >= n_blocks_x:
            continue

        dct_block = cv2.dct(block.astype(np.float64))

        # Check mid-frequency coefficients for anomalies
        mid_coeffs = dct_block[2:5, 2:5].flatten()
        block_energy = np.var(mid_coeffs)
        heatmap[by * 8:(by + 1) * 8, bx * 8:(bx + 1) * 8] = block_energy

    # Normalize
    hmin, hmax = heatmap.min(), heatmap.max()
    if hmax - hmin > 0:
        heatmap = ((heatmap - hmin) / (hmax - hmin) * 255)
    heatmap = np.clip(heatmap, 0, 255).astype(np.uint8)
    heatmap = cv2.GaussianBlur(heatmap, (5, 5), 0)

    return heatmap
