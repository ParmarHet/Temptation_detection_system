from __future__ import annotations

import io
from pathlib import Path
from typing import Tuple, Optional

import cv2
import numpy as np
from PIL import Image


def load_image(file_bytes: bytes, filename: str) -> Tuple[np.ndarray, str]:
    """Load image from bytes, handling JPG, PNG, and PDF.

    Returns:
        (image_as_numpy_bgr, detected_format)
    """
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        return _load_pdf(file_bytes)

    pil_image = Image.open(io.BytesIO(file_bytes))
    if pil_image.mode == "RGBA":
        pil_image = pil_image.convert("RGB")
    elif pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")

    img_array = np.array(pil_image)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    fmt = suffix.lstrip(".")
    return img_bgr, fmt


def _load_pdf(file_bytes: bytes) -> Tuple[np.ndarray, str]:
    """Convert first page of PDF to numpy array using PyMuPDF."""
    import fitz

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page = doc[0]
    mat = fitz.Matrix(2.0, 2.0)  # 2x upscale for quality
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    doc.close()

    pil_image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img_array = np.array(pil_image)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    return img_bgr, "pdf"


def get_image_info(img: np.ndarray) -> dict:
    """Return basic image metadata."""
    h, w = img.shape[:2]
    channels = img.shape[2] if len(img.shape) == 3 else 1
    return {
        "width": w,
        "height": h,
        "channels": channels,
        "total_pixels": h * w,
    }


def to_grayscale(img: np.ndarray) -> np.ndarray:
    """Convert BGR image to grayscale."""
    if len(img.shape) == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def to_rgb(img: np.ndarray) -> np.ndarray:
    """Convert BGR image to RGB."""
    if len(img.shape) == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
