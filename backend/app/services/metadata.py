"""Metadata / EXIF Forensics technique module.

Extracts and analyzes EXIF/XMP metadata to detect editing software tags,
timestamp inconsistencies, missing fields, and thumbnail mismatches.
Supporting signal — useful for catching careless tampering.
"""

from __future__ import annotations

from typing import Tuple, Optional

import numpy as np


def compute_metadata_analysis(
    image_bytes: bytes,
    filename: str,
) -> Tuple[None, dict, float]:
    """Analyze image metadata for tampering indicators.

    Args:
        image_bytes: raw file bytes
        filename: original filename

    Returns:
        (None, details_dict, score)
        Returns None for heatmap since metadata is non-spatial.
    """
    flags = []
    metadata = {}

    # Extract EXIF using multiple libraries for cross-reference
    exif_data = _extract_exif_pillow(image_bytes)
    exif_read_data = _extract_exifread(image_bytes)

    # Merge results
    metadata.update(exif_data)
    if exif_read_data:
        metadata.update({k: v for k, v in exif_read_data.items() if k not in metadata})

    # Check software tags
    software = metadata.get("Software", "") or metadata.get("software", "")
    if software:
        metadata["software_tag"] = software
        editing_software = [
            "photoshop", "gimp", "canva", "figma", "paint.net",
            "lightroom", "snapseed", "vsco", "afterlight",
        ]
        for sw in editing_software:
            if sw in software.lower():
                flags.append({
                    "type": "software_tag",
                    "severity": "high",
                    "detail": f"Editing software detected: {software}",
                })
                break

    # Check for Make/Model (expected in camera originals)
    make = metadata.get("Make", "") or metadata.get("make", "")
    model = metadata.get("Model", "") or metadata.get("model", "")
    if not make and not model:
        # Could be a scan or edit — not conclusive but worth flagging
        flags.append({
            "type": "missing_make_model",
            "severity": "low",
            "detail": "No camera Make/Model in metadata (could be scan or edit)",
        })
    else:
        metadata["camera_info"] = f"{make} {model}".strip()

    # Check timestamps
    date_original = (
        metadata.get("DateTimeOriginal", "")
        or metadata.get("EXIF DateTimeOriginal", "")
        or metadata.get("date_time_original", "")
    )
    date_modified = (
        metadata.get("DateTime", "")
        or metadata.get("Image DateTime", "")
        or metadata.get("date_time", "")
    )
    if date_original and date_modified:
        if date_original != date_modified:
            flags.append({
                "type": "timestamp_mismatch",
                "severity": "medium",
                "detail": f"Capture date ({date_original}) differs from modify date ({date_modified})",
            })
    elif not date_original and not date_modified:
        flags.append({
            "type": "no_timestamps",
            "severity": "low",
            "detail": "No timestamps found in metadata",
        })

    # Check thumbnail consistency
    thumbnail_consistent = _check_thumbnail_consistency(image_bytes, metadata)
    if thumbnail_consistent is False:
        flags.append({
            "type": "thumbnail_mismatch",
            "severity": "high",
            "detail": "Thumbnail does not match full image (possible edit without updating thumbnail)",
        })

    # Check color profile
    color_profile = metadata.get("ColorSpace", "") or metadata.get("color_space", "")
    if color_profile:
        metadata["color_profile"] = color_profile

    # Check if EXIF is completely absent
    has_exif = bool(metadata)
    if not has_exif:
        flags.append({
            "type": "no_exif",
            "severity": "low",
            "detail": "No EXIF metadata found (metadata may have been stripped)",
        })

    # Score: weighted sum of flag severities
    severity_weights = {"high": 30, "medium": 15, "low": 5}
    total_severity = sum(severity_weights.get(f["severity"], 0) for f in flags)
    score = min(100, total_severity)

    details = {
        "flags": flags,
        "num_flags": len(flags),
        "software_tag": software or None,
        "has_exif": has_exif,
        "camera_info": metadata.get("camera_info"),
        "date_original": date_original or None,
        "date_modified": date_modified or None,
        "metadata_fields_found": len(metadata),
    }

    return None, details, score


def _extract_exif_pillow(image_bytes: bytes) -> dict:
    """Extract EXIF using Pillow."""
    try:
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(image_bytes))
        exif_data = img.getexif()
        if not exif_data:
            return {}

        # Convert tag IDs to names
        from PIL.ExifTags import TAGS
        result = {}
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, str(tag_id))
            if isinstance(value, bytes):
                continue  # Skip binary data
            result[tag_name] = str(value)
        return result
    except Exception:
        return {}


def _extract_exifread(image_bytes: bytes) -> dict:
    """Extract EXIF using exifread (fallback)."""
    try:
        import exifread
        import io

        tags = exifread.process_file(io.BytesIO(image_bytes))
        if not tags:
            return {}

        # Simplify tag names
        result = {}
        for key, value in tags.items():
            # Strip common prefixes
            simple_key = key.split(" ")[-1] if " " in key else key
            result[simple_key] = str(value)
        return result
    except Exception:
        return {}


def _check_thumbnail_consistency(image_bytes: bytes, metadata: dict) -> Optional[bool]:
    """Check if thumbnail matches the full image.

    Returns:
        True if consistent, False if mismatch, None if can't determine.
    """
    try:
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(image_bytes))
        if not hasattr(img, "thumbnail") or img.thumbnail is None:
            return None

        # Compare basic properties
        thumb = img.thumbnail
        if hasattr(thumb, "size") and hasattr(img, "size"):
            # Thumbnail should be a downscaled version
            aspect_ratio_thumb = thumb.size[0] / max(thumb.size[1], 1)
            aspect_ratio_full = img.size[0] / max(img.size[1], 1)
            if abs(aspect_ratio_thumb - aspect_ratio_full) > 0.1:
                return False
        return True
    except Exception:
        return None
