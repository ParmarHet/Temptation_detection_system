from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np


def normalize_heatmap(heatmap: np.ndarray) -> np.ndarray:
    """Normalize heatmap to 0-255 uint8 range."""
    hmin = heatmap.min()
    hmax = heatmap.max()
    if hmax - hmin < 1e-6:
        return np.zeros_like(heatmap, dtype=np.uint8)
    normalized = ((heatmap - hmin) / (hmax - hmin) * 255).astype(np.uint8)
    return normalized


def apply_colormap(heatmap: np.ndarray, colormap: int = cv2.COLORMAP_JET) -> np.ndarray:
    """Apply OpenCV colormap to single-channel heatmap."""
    return cv2.applyColorMap(heatmap, colormap)


def create_overlay(
    original: np.ndarray,
    heatmap: np.ndarray,
    alpha: float = 0.55,
    colormap: int = cv2.COLORMAP_JET,
) -> np.ndarray:
    """Overlay colored heatmap on original image.

    Args:
        original: BGR image (uint8)
        heatmap: single-channel heatmap (uint8, 0-255)
        alpha: blend factor (0=original, 1=heatmap)
        colormap: OpenCV colormap

    Returns:
        Blended BGR image
    """
    h, w = original.shape[:2]
    resized_heatmap = cv2.resize(heatmap, (w, h), interpolation=cv2.INTER_LINEAR)

    # Enhance contrast of heatmap before applying colormap
    enhanced = cv2.normalize(resized_heatmap, None, 0, 255, cv2.NORM_MINMAX)

    colored = cv2.applyColorMap(enhanced, colormap)

    # Create mask where heatmap has actual signal
    mask = (resized_heatmap > 10).astype(np.uint8) * 255

    # Only blend where heatmap has signal, keep original elsewhere
    mask_3ch = cv2.merge([mask, mask, mask])
    blended = original.copy()
    foreground = cv2.addWeighted(original, 1 - alpha, colored, alpha, 0)
    blended[mask_3ch > 0] = foreground[mask_3ch > 0]

    return blended


def create_fused_overlay(
    original: np.ndarray,
    heatmaps: dict[str, np.ndarray],
    scores: dict[str, float],
    alpha: float = 0.6,
) -> np.ndarray:
    """Create a multi-signal fused overlay with color-coded regions.

    Color mapping:
        - Red: ELA suspicious regions
        - Blue: Copy-move matches
        - Green: Noise anomalies
        - Yellow: OCR inconsistencies
        - Cyan: Metadata flags (if spatial)

    Args:
        original: BGR image
        heatmaps: dict of technique_name -> heatmap (uint8)
        scores: dict of technique_name -> score (0-100)
        alpha: blend factor

    Returns:
        Fused overlay BGR image
    """
    h, w = original.shape[:2]
    overlay = np.zeros((h, w, 3), dtype=np.float32)

    color_map = {
        "ela": (0, 0, 255),        # Red in BGR
        "copymove": (255, 100, 0),  # Blue in BGR
        "noise": (0, 200, 0),       # Green in BGR
        "ocr": (0, 220, 220),       # Yellow in BGR
        "jpeg_ghost": (255, 150, 0), # Cyan in BGR
        "metadata": (128, 0, 255),  # Purple in BGR
    }

    for name, heatmap in heatmaps.items():
        if heatmap is None:
            continue
        score = scores.get(name, 0)
        if score < 5:
            continue

        resized = cv2.resize(heatmap, (w, h), interpolation=cv2.INTER_LINEAR)

        # Normalize heatmap to full range for better visibility
        enhanced = cv2.normalize(resized, None, 0, 255, cv2.NORM_MINMAX)

        color = color_map.get(name, (255, 255, 255))

        # Use lower threshold and boost intensity
        mask = (enhanced > 15).astype(np.float32)

        # Boost the contribution - use sqrt to enhance weaker signals
        intensity = np.sqrt(enhanced / 255.0) * mask

        mask_3ch = np.stack([mask] * 3, axis=-1)
        intensity_3ch = np.stack([intensity] * 3, axis=-1)

        color_3ch = np.array(color, dtype=np.float32).reshape(1, 1, 3)
        contribution = mask_3ch * color_3ch * intensity_3ch * 0.8
        overlay += contribution

    overlay = np.clip(overlay, 0, 255).astype(np.uint8)

    # Create mask for where we have overlay signal
    overlay_mask = np.any(overlay > 10, axis=2).astype(np.uint8) * 255

    # Blend only where we have signal
    result = original.copy()
    blended = cv2.addWeighted(original, 1 - alpha, overlay, alpha, 0)
    result[overlay_mask > 0] = blended[overlay_mask > 0]

    return result


def save_heatmap(heatmap: np.ndarray, path: Path) -> Path:
    """Save heatmap image to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), heatmap)
    return path


def create_comparison_grid(
    original: np.ndarray,
    heatmaps: dict[str, np.ndarray],
    max_cols: int = 3,
) -> np.ndarray:
    """Create a grid comparing original with individual technique heatmaps.

    Returns a single concatenated image grid.
    """
    h, w = original.shape[:2]
    cells = [("Original", original)]

    color_labels = {
        "ela": "ELA",
        "noise": "Noise",
        "copymove": "Copy-Move",
        "ocr": "OCR",
        "jpeg_ghost": "JPEG Ghost",
        "metadata": "Metadata",
    }

    for name, hm in heatmaps.items():
        if hm is not None:
            overlay = create_overlay(original, hm)
            cells.append((color_labels.get(name, name), overlay))

    n_cells = len(cells)
    cols = min(n_cells, max_cols)
    rows = (n_cells + cols - 1) // cols

    pad_h = 30  # Space for labels
    canvas = np.ones((rows * (h + pad_h), cols * w, 3), dtype=np.uint8) * 40

    for idx, (label, cell) in enumerate(cells):
        r, c = divmod(idx, cols)
        y = r * (h + pad_h) + pad_h
        x = c * w
        resized = cv2.resize(cell, (w, h))
        canvas[y:y + h, x:x + w] = resized

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(canvas, label, (x + 5, r * (h + pad_h) + 20), font, 0.6, (255, 255, 255), 1)

    return canvas
