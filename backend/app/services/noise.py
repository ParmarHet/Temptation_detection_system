"""Noise / Residual Pattern Analysis technique module.

Extracts the noise residual via wavelet denoising and looks for regions
where local noise statistics deviate from the surrounding document.
Spliced-in content often has a different noise floor than the original.
"""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np

from app.config import settings


def compute_noise_analysis(
    img: np.ndarray,
    block_size: int = None,
    sigma_threshold: float = None,
) -> Tuple[np.ndarray, dict]:
    """Compute noise residual analysis.

    Args:
        img: BGR image (uint8)
        block_size: analysis block size (default from config)
        sigma_threshold: std deviations for anomaly flagging (default from config)

    Returns:
        (noise_heatmap, details_dict, score)
    """
    block_size = block_size or settings.NOISE_BLOCK_SIZE
    sigma_threshold = sigma_threshold or settings.NOISE_SIGMA_THRESHOLD

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    h, w = gray.shape

    # Wavelet denoising to extract noise residual
    residual = _wavelet_denoise_residual(gray)

    # Divide into overlapping blocks and compute local statistics (50% overlap)
    stride = block_size // 2
    blocks = []
    block_map = np.zeros((h, w), dtype=np.float64)

    for y in range(0, h - block_size + 1, stride):
        for x in range(0, w - block_size + 1, stride):
            block = residual[y:y + block_size, x:x + block_size]
            local_std = float(np.std(block))
            blocks.append({
                "x": x,
                "y": y,
                "std": local_std,
            })
            block_map[y:y + block_size, x:x + block_size] = local_std

    if not blocks:
        return np.zeros((h, w), dtype=np.uint8), {"score": 0, "blocks_flagged": 0}, 0

    # Global noise statistics
    all_stds = [b["std"] for b in blocks]
    global_mean = np.mean(all_stds)
    global_std = np.std(all_stds)

    # Flag blocks that deviate significantly
    flagged_blocks = []
    for b in blocks:
        z_score = abs(b["std"] - global_mean) / max(global_std, 1e-6)
        if z_score > sigma_threshold:
            b["z_score"] = round(float(z_score), 4)
            flagged_blocks.append(b)

    # Also compute text-aware analysis: separate text regions from background
    text_mask = _extract_text_mask(gray)
    bg_residual_std = float(np.std(residual[~text_mask > 0])) if np.any(~text_mask > 0) else 0
    text_residual_std = float(np.std(residual[text_mask > 0])) if np.any(text_mask > 0) else 0

    # Score calculation
    total_blocks = len(blocks)
    flagged_ratio = len(flagged_blocks) / max(total_blocks, 1)

    # High score if many blocks deviate, or if global noise is suspiciously uniform
    uniformity_score = 0
    if global_std < 2.0:
        uniformity_score = 30  # Suspiciously uniform noise = possible synthetic

    anomaly_score = flagged_ratio * 60 + uniformity_score
    score = max(0, min(100, anomaly_score * 100))

    # Create heatmap from block deviations
    heatmap = np.zeros((h, w), dtype=np.float64)
    for b in blocks:
        z = b["z_score"] if "z_score" in b else 0
        intensity = min(255, z / sigma_threshold * 127)
        heatmap[b["y"]:b["y"] + block_size, b["x"]:b["x"] + block_size] = intensity

    heatmap = np.clip(heatmap, 0, 255).astype(np.uint8)
    heatmap = cv2.GaussianBlur(heatmap, (7, 7), 0)

    details = {
        "global_noise_mean": round(float(global_mean), 4),
        "global_noise_std": round(float(global_std), 4),
        "blocks_flagged": len(flagged_blocks),
        "total_blocks": total_blocks,
        "flagged_ratio": round(flagged_ratio, 4),
        "bg_residual_std": round(bg_residual_std, 4),
        "text_residual_std": round(text_residual_std, 4),
        "uniformity_flag": uniformity_score > 0,
        "flagged_details": flagged_blocks[:20],
    }

    return heatmap, details, score


def _wavelet_denoise_residual(gray: np.ndarray) -> np.ndarray:
    """Extract noise residual using wavelet denoising.

    Uses Daubechies-4 wavelet with soft thresholding to separate
    noise from signal. The residual = original - denoised = noise.
    """
    try:
        import pywt

        # Normalize to float
        img_float = gray.astype(np.float64) / 255.0

        # Multi-level wavelet decomposition
        levels = min(3, pywt.dwtmaxlev(len(gray), "db4"))
        coeffs = pywt.wavedec2(img_float, settings.NOISE_WAVELET, level=levels)

        # Soft thresholding on detail coefficients
        sigma = _estimate_noise_sigma(coeffs)
        threshold = sigma * np.sqrt(2 * np.log(gray.size))

        denoised_coeffs = [coeffs[0]]  # Keep approximation
        for detail_level in coeffs[1:]:
            denoised_level = []
            for subband in detail_level:
                denoised_subband = pywt.threshold(subband, threshold, mode="soft")
                denoised_level.append(denoised_subband)
            denoised_coeffs.append(denoised_level)

        # Reconstruct denoised image
        denoised = pywt.waverec2(denoised_coeffs, settings.NOISE_WAVELET)
        denoised = np.clip(denoised[:gray.shape[0], :gray.shape[1]] * 255, 0, 255)

        # Residual = original - denoised
        residual = gray.astype(np.float64) - denoised
        return residual

    except ImportError:
        # Fallback: high-pass filter if PyWavelets not available
        blurred = cv2.GaussianBlur(gray, (21, 21), 0)
        return gray.astype(np.float64) - blurred.astype(np.float64)


def _estimate_noise_sigma(coeffs: list) -> float:
    """Estimate noise sigma from wavelet HH subband using MAD."""
    # Use the finest level HH subband
    hh = coeffs[-1][-1]
    # Median Absolute Deviation estimator
    sigma = np.median(np.abs(hh)) / 0.6745
    return max(float(sigma), 1e-6)


def _extract_text_mask(gray: np.ndarray) -> np.ndarray:
    """Extract text regions using adaptive thresholding."""
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 5
    )
    # Dilate to connect character strokes
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    text_mask = cv2.dilate(binary, kernel, iterations=2)
    return text_mask
