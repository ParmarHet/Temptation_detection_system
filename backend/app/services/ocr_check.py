"""OCR-Based Text Consistency Check technique module.

Runs OCR on the document and checks per-line/field for:
- Font size and stroke-width variance
- Baseline alignment consistency
- Character spacing/kerning uniformity
- Edge sharpness/anti-aliasing consistency

Document-specific technique with high forensic value.
"""

from __future__ import annotations

from typing import Tuple, List, Optional

import cv2
import numpy as np

from app.config import settings


def compute_ocr_consistency(
    img: np.ndarray,
    languages: list = None,
) -> Tuple[Optional[np.ndarray], dict, float]:
    """Run OCR and analyze text consistency for tampering indicators.

    Args:
        img: BGR image (uint8)
        languages: OCR languages (default from config)

    Returns:
        (heatmap_or_None, details_dict, score)
    """
    languages = languages or settings.OCR_LANGUAGES

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    h, w = gray.shape

    # Preprocess for OCR
    preprocessed = _preprocess_for_ocr(gray)

    # Run OCR with Tesseract
    ocr_results = _run_tesseract(preprocessed, languages)

    if not ocr_results or len(ocr_results) < 2:
        return None, {
            "score": 0,
            "words_flagged": 0,
            "lines_flagged": 0,
            "flagged_regions": [],
            "skipped": True,
            "skip_reason": "Insufficient text detected for analysis",
        }, 0

    # Group words into lines
    lines = _group_into_lines(ocr_results)

    # Analyze each line for anomalies
    flagged_regions = []
    line_anomalies = []

    for line_idx, line_words in enumerate(lines):
        if len(line_words) < 2:
            continue

        # Check font size consistency
        font_anomalies = _check_font_size_consistency(line_words, line_idx)

        # Check baseline alignment
        baseline_anomalies = _check_baseline_alignment(line_words, line_idx)

        # Check kerning (character spacing)
        kerning_anomalies = _check_kerning_consistency(line_words, line_idx)

        # Check edge sharpness consistency
        sharpness_anomalies = _check_sharpness_consistency(
            gray, line_words, line_idx
        )

        # Check stroke width consistency
        stroke_anomalies = _check_stroke_width_consistency(
            preprocessed, line_words, line_idx
        )

        line_flags = font_anomalies + baseline_anomalies + kerning_anomalies + sharpness_anomalies + stroke_anomalies
        if line_flags:
            line_anomalies.append({
                "line_index": line_idx,
                "num_flags": len(line_flags),
                "flags": line_flags,
            })
            flagged_regions.extend(line_flags)

    # Score calculation
    total_words = len(ocr_results)
    flagged_words = len(set(
        r["word"] for f in flagged_regions for r in [f] if "word_index" in f
    ))
    flagged_ratio = flagged_words / max(total_words, 1)

    # Line-level flagging
    flagged_lines = len(line_anomalies)
    line_ratio = flagged_lines / max(len(lines), 1)

    # Combined score
    word_score = flagged_ratio * 50
    line_score = line_ratio * 30
    severity_score = sum(
        f.get("severity_weight", 1) for f in flagged_regions
    ) / max(len(flagged_regions), 1) * 20

    score = min(100, (word_score + line_score + severity_score) * 100)

    # Create heatmap highlighting flagged regions
    heatmap = None
    if flagged_regions:
        heatmap = np.zeros((h, w), dtype=np.uint8)
        for region in flagged_regions:
            bbox = region.get("bbox")
            if bbox:
                x, y, bw, bh = bbox
                intensity = min(255, int(region.get("severity_weight", 1) * 80))
                heatmap[y:y + bh, x:x + bw] = intensity
        heatmap = cv2.GaussianBlur(heatmap, (7, 7), 0)

    details = {
        "words_flagged": flagged_words,
        "lines_flagged": flagged_lines,
        "total_words": total_words,
        "total_lines": len(lines),
        "flagged_regions": flagged_regions[:30],
        "line_anomalies": line_anomalies[:20],
    }

    return heatmap, details, score


def _preprocess_for_ocr(gray: np.ndarray) -> np.ndarray:
    """Preprocess image for robust OCR.

    Pipeline: CLAHE → Denoise → Adaptive Threshold → Deskew
    """
    # CLAHE for local contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Bilateral filter (preserves edges better than Gaussian)
    denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)

    # Adaptive threshold
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 5
    )

    # Deskew
    deskewed = _deskew(binary)

    return deskewed


def _deskew(image: np.ndarray) -> np.ndarray:
    """Correct image skew using minAreaRect."""
    coords = np.column_stack(np.where(image < 128))
    if len(coords) < 50:
        return image

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) < 0.5:
        return image  # Nearly straight, skip

    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    mat = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, mat, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated


def _run_tesseract(
    preprocessed: np.ndarray, languages: list
) -> List[dict]:
    """Run Tesseract OCR and return word-level results."""
    try:
        import pytesseract

        lang = "+".join(languages)

        # Get word-level data
        data = pytesseract.image_to_data(
            preprocessed,
            lang=lang,
            config="--psm 6",
            output_type=pytesseract.Output.DICT,
        )

        results = []
        n_boxes = len(data["text"])
        for i in range(n_boxes):
            text = data["text"][i].strip()
            conf = int(data["conf"][i])
            if not text or conf < 30:
                continue

            results.append({
                "word": text,
                "confidence": conf,
                "bbox": [
                    data["left"][i],
                    data["top"][i],
                    data["width"][i],
                    data["height"][i],
                ],
                "block_num": data["block_num"][i],
                "line_num": data["line_num"][i],
                "word_num": data["word_num"][i],
                "height": data["height"][i],
                "width": data["width"][i],
            })

        return results

    except ImportError:
        return []
    except Exception:
        return []


def _group_into_lines(ocr_results: List[dict]) -> List[List[dict]]:
    """Group OCR results into lines based on block and line numbers."""
    lines_dict = {}
    for r in ocr_results:
        key = (r["block_num"], r["line_num"])
        if key not in lines_dict:
            lines_dict[key] = []
        lines_dict[key].append(r)

    # Sort by line position (top to bottom)
    lines = sorted(lines_dict.values(), key=lambda words: words[0]["bbox"][1])
    return lines


def _check_font_size_consistency(
    line_words: List[dict], line_idx: int
) -> List[dict]:
    """Check if font sizes are consistent within a line."""
    if len(line_words) < 2:
        return []

    heights = [w["height"] for w in line_words]
    mean_h = np.mean(heights)
    std_h = np.std(heights)

    if mean_h < 5:
        return []

    flags = []
    for i, word in enumerate(line_words):
        z_score = abs(word["height"] - mean_h) / max(std_h, 1)
        if z_score > settings.OCR_ZSCORE_THRESHOLD:
            flags.append({
                "type": "font_size_inconsistency",
                "line_index": line_idx,
                "word_index": i,
                "word": word["word"],
                "bbox": word["bbox"],
                "z_score": round(float(z_score), 4),
                "expected_height": round(float(mean_h), 2),
                "actual_height": word["height"],
                "severity_weight": min(3, int(z_score)),
            })

    return flags


def _check_baseline_alignment(
    line_words: List[dict], line_idx: int
) -> List[dict]:
    """Check if all words in a line sit on the same baseline."""
    if len(line_words) < 3:
        return []

    # Baseline = bottom of bounding box
    baselines = [w["bbox"][1] + w["bbox"][3] for w in line_words]
    mean_bl = np.mean(baselines)
    std_bl = np.std(baselines)

    if std_bl < 1:
        return []  # Perfect alignment, skip

    flags = []
    for i, word in enumerate(line_words):
        deviation = abs(baselines[i] - mean_bl)
        if deviation > max(std_bl * 2, 3):  # At least 3px deviation
            flags.append({
                "type": "baseline_shift",
                "line_index": line_idx,
                "word_index": i,
                "word": word["word"],
                "bbox": word["bbox"],
                "deviation_px": round(float(deviation), 2),
                "expected_baseline": round(float(mean_bl), 2),
                "actual_baseline": round(float(baselines[i]), 2),
                "severity_weight": min(3, int(deviation / max(std_bl, 1))),
            })

    return flags


def _check_kerning_consistency(
    line_words: List[dict], line_idx: int
) -> List[dict]:
    """Check if inter-character spacing is consistent within a line."""
    if len(line_words) < 3:
        return []

    # Compute gaps between consecutive words
    gaps = []
    sorted_words = sorted(line_words, key=lambda w: w["bbox"][0])
    for i in range(1, len(sorted_words)):
        prev_end = sorted_words[i - 1]["bbox"][0] + sorted_words[i - 1]["bbox"][2]
        curr_start = sorted_words[i]["bbox"][0]
        gap = curr_start - prev_end
        gaps.append((i, gap))

    if not gaps:
        return []

    gap_values = [g[1] for g in gaps]
    mean_gap = np.mean(gap_values)
    std_gap = np.std(gap_values)

    flags = []
    for idx, gap in gaps:
        if std_gap > 0 and abs(gap - mean_gap) > max(std_gap * 2, 5):
            flags.append({
                "type": "kerning_inconsistency",
                "line_index": line_idx,
                "word_index": idx,
                "word": sorted_words[idx]["word"],
                "bbox": sorted_words[idx]["bbox"],
                "gap": round(float(gap), 2),
                "expected_gap": round(float(mean_gap), 2),
                "severity_weight": 1,
            })

    return flags


def _check_sharpness_consistency(
    gray: np.ndarray,
    line_words: List[dict],
    line_idx: int,
) -> List[dict]:
    """Check if edge sharpness is consistent across words in a line.

    Pasted-in text from a different source often has different
    anti-aliasing characteristics than the original text.
    """
    if len(line_words) < 3:
        return []

    sharpness_values = []
    for word in line_words:
        x, y, w, h = word["bbox"]
        # Ensure bounds are valid
        x = max(0, x)
        y = max(0, y)
        w = min(w, gray.shape[1] - x)
        h = min(h, gray.shape[0] - y)
        if w <= 0 or h <= 0:
            continue

        roi = gray[y:y + h, x:x + w]
        if roi.size == 0:
            continue

        # Laplacian variance as sharpness measure
        laplacian = cv2.Laplacian(roi, cv2.CV_64F)
        sharpness = float(laplacian.var())
        sharpness_values.append((word, sharpness))

    if len(sharpness_values) < 3:
        return []

    values = [s[1] for s in sharpness_values]
    mean_s = np.mean(values)
    std_s = np.std(values)

    flags = []
    for word, sharpness in sharpness_values:
        z_score = abs(sharpness - mean_s) / max(std_s, 1)
        if z_score > settings.OCR_ZSCORE_THRESHOLD:
            flags.append({
                "type": "sharpness_inconsistency",
                "line_index": line_idx,
                "word": word["word"],
                "bbox": word["bbox"],
                "sharpness": round(sharpness, 4),
                "expected_sharpness": round(float(mean_s), 4),
                "z_score": round(float(z_score), 4),
                "severity_weight": min(3, int(z_score)),
            })

    return flags


def _check_stroke_width_consistency(
    preprocessed: np.ndarray,
    line_words: List[dict],
    line_idx: int,
) -> List[dict]:
    """Check if stroke width is consistent across characters.

    Different rendering pipelines produce different stroke widths,
    which can indicate paste-in editing.
    """
    if len(line_words) < 3:
        return []

    stroke_widths = []
    for word in line_words:
        x, y, w, h = word["bbox"]
        x = max(0, x)
        y = max(0, y)
        w = min(w, preprocessed.shape[1] - x)
        h = min(h, preprocessed.shape[0] - y)
        if w <= 0 or h <= 0:
            continue

        roi = preprocessed[y:y + h, x:x + w]
        if roi.size == 0:
            continue

        # Distance transform on binary text → average distance = stroke width proxy
        _, binary = cv2.threshold(roi, 127, 255, cv2.THRESH_BINARY_INV)
        dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
        mean_stroke = float(np.mean(dist[dist > 0])) if np.any(dist > 0) else 0
        stroke_widths.append((word, mean_stroke))

    if len(stroke_widths) < 3:
        return []

    values = [s[1] for s in stroke_widths]
    mean_sw = np.mean(values)
    std_sw = np.std(values)

    flags = []
    for word, sw in stroke_widths:
        z_score = abs(sw - mean_sw) / max(std_sw, 1)
        if z_score > settings.OCR_ZSCORE_THRESHOLD:
            flags.append({
                "type": "stroke_width_inconsistency",
                "line_index": line_idx,
                "word": word["word"],
                "bbox": word["bbox"],
                "stroke_width": round(sw, 4),
                "expected_stroke_width": round(float(mean_sw), 4),
                "z_score": round(float(z_score), 4),
                "severity_weight": min(3, int(z_score)),
            })

    return flags
