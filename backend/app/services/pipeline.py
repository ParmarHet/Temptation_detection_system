"""Pipeline orchestrator module.

Provides two analysis modes:
- Fast: ELA + Noise + Metadata + JPEG Ghost + OCR (no copy-move)
- Deep: All 6 techniques including copy-move detection
"""

from __future__ import annotations

import logging
import time
import uuid

import cv2
import numpy as np

from app.config import settings
from app.utils.image_io import load_image, get_image_info

logger = logging.getLogger(__name__)


def run_analysis(image_bytes: bytes, filename: str, deep: bool = False) -> dict:
    """Run tamper detection pipeline on a document image.

    Args:
        image_bytes: raw file bytes (JPG, PNG, or PDF)
        filename: original filename with extension
        deep: if True, include copy-move detection (slower)

    Returns:
        Complete analysis response dict
    """
    analysis_id = str(uuid.uuid4())
    overall_started_at = time.perf_counter()
    logger.info(
        "Pipeline started: analysis_id=%s filename=%s size_bytes=%d deep=%s",
        analysis_id, filename, len(image_bytes), deep,
    )

    # Load image
    load_started_at = time.perf_counter()
    img, image_format = load_image(image_bytes, filename)
    img_info = get_image_info(img)
    logger.info(
        "Image loaded: analysis_id=%s format=%s width=%d height=%d load_seconds=%.3f",
        analysis_id, image_format, img_info["width"], img_info["height"],
        time.perf_counter() - load_started_at,
    )

    # Create output directories
    heatmap_dir = settings.HEATMAP_DIR / analysis_id
    heatmap_dir.mkdir(parents=True, exist_ok=True)

    # Storage for results
    technique_scores = {}
    technique_details = {}
    technique_heatmaps = {}
    technique_heatmap_urls = {}

    # --- Techniques to run ---
    techniques = ["ela", "noise", "metadata", "jpeg_ghost", "ocr"]
    if deep:
        techniques.append("copymove")

    # --- 1. ELA Analysis ---
    if "ela" in techniques:
        try:
            from app.services.ela import compute_ela, create_ela_heatmap
            stage_started_at = time.perf_counter()
            logger.info("Stage started: analysis_id=%s technique=ela", analysis_id)

            ela_heatmap, ela_details, ela_score = compute_ela(img)
            technique_scores["ela"] = ela_score
            technique_details["ela"] = ela_details
            technique_heatmaps["ela"] = ela_heatmap

            overlay = create_ela_heatmap(img, ela_heatmap)
            cv2.imwrite(str(heatmap_dir / "ela.png"), overlay)
            technique_heatmap_urls["ela"] = f"/api/v1/heatmap/{analysis_id}/ela"

            logger.info("Stage finished: analysis_id=%s technique=ela score=%.2f elapsed=%.3f",
                        analysis_id, ela_score, time.perf_counter() - stage_started_at)
        except Exception as e:
            logger.exception("Stage failed: analysis_id=%s technique=ela", analysis_id)
            technique_scores["ela"] = 0
            technique_details["ela"] = {"error": str(e), "skipped": True}

    # --- 2. Noise Analysis ---
    if "noise" in techniques:
        try:
            from app.services.noise import compute_noise_analysis
            stage_started_at = time.perf_counter()
            logger.info("Stage started: analysis_id=%s technique=noise", analysis_id)

            noise_heatmap, noise_details, noise_score = compute_noise_analysis(img)
            technique_scores["noise"] = noise_score
            technique_details["noise"] = noise_details
            technique_heatmaps["noise"] = noise_heatmap

            if noise_heatmap is not None and noise_heatmap.any():
                from app.utils.heatmap import create_overlay
                overlay = create_overlay(img, noise_heatmap)
                cv2.imwrite(str(heatmap_dir / "noise.png"), overlay)
                technique_heatmap_urls["noise"] = f"/api/v1/heatmap/{analysis_id}/noise"

            logger.info("Stage finished: analysis_id=%s technique=noise score=%.2f elapsed=%.3f",
                        analysis_id, noise_score, time.perf_counter() - stage_started_at)
        except Exception as e:
            logger.exception("Stage failed: analysis_id=%s technique=noise", analysis_id)
            technique_scores["noise"] = 0
            technique_details["noise"] = {"error": str(e), "skipped": True}

    # --- 3. Copy-Move Detection (deep only) ---
    if "copymove" in techniques:
        try:
            from app.copy_move_detection import detect as copymove_detect
            import tempfile, os, shutil

            stage_started_at = time.perf_counter()
            logger.info("Stage started: analysis_id=%s technique=copymove", analysis_id)

            temp_input = os.path.join(tempfile.gettempdir(), f"cm_{analysis_id}.png")
            temp_output = os.path.join(tempfile.gettempdir(), f"cm_out_{analysis_id}")
            os.makedirs(temp_output, exist_ok=True)
            cv2.imwrite(temp_input, img)

            result_path = copymove_detect(temp_input, temp_output, block_size=128)

            if result_path and os.path.exists(result_path):
                cm_heatmap = cv2.imread(result_path, cv2.IMREAD_GRAYSCALE)
                if cm_heatmap is None:
                    cm_heatmap = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
            else:
                cm_heatmap = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)

            detected_pixels = int(np.sum(cm_heatmap > 0))
            total_pixels = cm_heatmap.shape[0] * cm_heatmap.shape[1]
            cm_score = min(100, (detected_pixels / total_pixels) * 500)

            technique_scores["copymove"] = cm_score
            technique_details["copymove"] = {
                "matches_found": 1 if detected_pixels > 0 else 0,
                "detected_pixels": detected_pixels,
                "coverage_ratio": round(detected_pixels / total_pixels, 6) if total_pixels > 0 else 0,
            }
            technique_heatmaps["copymove"] = cm_heatmap

            if cm_heatmap is not None and cm_heatmap.any():
                from app.utils.heatmap import create_overlay
                overlay = create_overlay(img, cm_heatmap)
                cv2.imwrite(str(heatmap_dir / "copymove.png"), overlay)
                technique_heatmap_urls["copymove"] = f"/api/v1/heatmap/{analysis_id}/copymove"

            try:
                os.remove(temp_input)
                shutil.rmtree(temp_output, ignore_errors=True)
            except Exception:
                pass

            logger.info("Stage finished: analysis_id=%s technique=copymove score=%.2f elapsed=%.3f",
                        analysis_id, cm_score, time.perf_counter() - stage_started_at)
        except Exception as e:
            logger.exception("Stage failed: analysis_id=%s technique=copymove", analysis_id)
            technique_scores["copymove"] = 0
            technique_details["copymove"] = {"error": str(e), "skipped": True}

    # --- 4. Metadata Analysis ---
    if "metadata" in techniques:
        try:
            from app.services.metadata import compute_metadata_analysis
            stage_started_at = time.perf_counter()
            logger.info("Stage started: analysis_id=%s technique=metadata", analysis_id)

            _, meta_details, meta_score = compute_metadata_analysis(image_bytes, filename)
            technique_scores["metadata"] = meta_score
            technique_details["metadata"] = meta_details

            logger.info("Stage finished: analysis_id=%s technique=metadata score=%.2f elapsed=%.3f",
                        analysis_id, meta_score, time.perf_counter() - stage_started_at)
        except Exception as e:
            logger.exception("Stage failed: analysis_id=%s technique=metadata", analysis_id)
            technique_scores["metadata"] = 0
            technique_details["metadata"] = {"error": str(e), "skipped": True}

    # --- 5. JPEG Ghost Analysis ---
    if "jpeg_ghost" in techniques:
        try:
            from app.services.jpeg_ghost import compute_jpeg_ghost_analysis
            stage_started_at = time.perf_counter()
            logger.info("Stage started: analysis_id=%s technique=jpeg_ghost", analysis_id)

            jg_heatmap, jg_details, jg_score = compute_jpeg_ghost_analysis(
                img, image_bytes=image_bytes, filename=filename
            )
            technique_scores["jpeg_ghost"] = jg_score
            technique_details["jpeg_ghost"] = jg_details
            technique_heatmaps["jpeg_ghost"] = jg_heatmap

            if jg_heatmap is not None:
                from app.utils.heatmap import create_overlay
                overlay = create_overlay(img, jg_heatmap)
                cv2.imwrite(str(heatmap_dir / "jpeg_ghost.png"), overlay)
                technique_heatmap_urls["jpeg_ghost"] = f"/api/v1/heatmap/{analysis_id}/jpeg_ghost"

            logger.info("Stage finished: analysis_id=%s technique=jpeg_ghost score=%.2f elapsed=%.3f",
                        analysis_id, jg_score, time.perf_counter() - stage_started_at)
        except Exception as e:
            logger.exception("Stage failed: analysis_id=%s technique=jpeg_ghost", analysis_id)
            technique_scores["jpeg_ghost"] = 0
            technique_details["jpeg_ghost"] = {"error": str(e), "skipped": True}

    # --- 6. OCR Consistency Check ---
    if "ocr" in techniques:
        try:
            from app.services.ocr_check import compute_ocr_consistency
            stage_started_at = time.perf_counter()
            logger.info("Stage started: analysis_id=%s technique=ocr", analysis_id)

            ocr_heatmap, ocr_details, ocr_score = compute_ocr_consistency(img)
            technique_scores["ocr"] = ocr_score
            technique_details["ocr"] = ocr_details
            technique_heatmaps["ocr"] = ocr_heatmap

            if ocr_heatmap is not None:
                from app.utils.heatmap import create_overlay
                overlay = create_overlay(img, ocr_heatmap)
                cv2.imwrite(str(heatmap_dir / "ocr.png"), overlay)
                technique_heatmap_urls["ocr"] = f"/api/v1/heatmap/{analysis_id}/ocr"

            logger.info("Stage finished: analysis_id=%s technique=ocr score=%.2f elapsed=%.3f",
                        analysis_id, ocr_score, time.perf_counter() - stage_started_at)
        except Exception as e:
            logger.exception("Stage failed: analysis_id=%s technique=ocr", analysis_id)
            technique_scores["ocr"] = 0
            technique_details["ocr"] = {"error": str(e), "skipped": True}

    # --- Fusion ---
    from app.services.fusion import fuse_scores, generate_fused_heatmap, generate_individual_heatmaps

    overall_score, verdict, fusion_details = fuse_scores(technique_scores, technique_details, image_format)

    fused_heatmap_url = generate_fused_heatmap(img, technique_heatmaps, technique_scores, analysis_id, heatmap_dir)
    individual_urls = generate_individual_heatmaps(img, technique_heatmaps, analysis_id, heatmap_dir)
    technique_heatmap_urls.update(individual_urls)

    # Save original image
    cv2.imwrite(str(heatmap_dir / "original.png"), img)

    # Build response
    all_technique_names = ["ela", "noise", "copymove", "metadata", "jpeg_ghost", "ocr"]
    response = {
        "id": analysis_id,
        "filename": filename,
        "file_size": len(image_bytes),
        "image_width": img_info["width"],
        "image_height": img_info["height"],
        "format": image_format,
        "overall_score": round(overall_score, 2),
        "verdict": verdict,
        "deep_analysis": deep,
        "techniques": {
            name: {
                "score": round(technique_scores.get(name, 0), 2),
                "details": technique_details.get(name, {}),
                "heatmap_url": technique_heatmap_urls.get(name),
                "skipped": technique_details.get(name, {}).get("skipped", False),
            }
            for name in all_technique_names
        },
        "fusion": fusion_details,
        "fused_heatmap_url": fused_heatmap_url,
        "original_image_url": f"/api/v1/heatmap/{analysis_id}/original",
    }

    total_elapsed = time.perf_counter() - overall_started_at
    logger.info("Pipeline completed: analysis_id=%s total_seconds=%.3f deep=%s techniques=%s",
                analysis_id, total_elapsed, deep, ",".join(sorted(technique_scores.keys())))

    return response
