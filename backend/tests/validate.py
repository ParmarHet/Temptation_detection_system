"""Validation script for the tamper detection pipeline.

Run this script against your test documents to produce a comparison table.
Place clean documents in test_documents/clean/ and tampered in test_documents/tampered/.

Usage:
    python -m tests.validate
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.pipeline import run_analysis


def validate():
    base_dir = Path(__file__).resolve().parent.parent / "test_documents"
    clean_dir = base_dir / "clean"
    tampered_dir = base_dir / "tampered"

    results = []

    # Process clean documents
    for img_path in sorted(clean_dir.glob("*")):
        if img_path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".pdf"):
            continue
        print(f"Analyzing clean: {img_path.name}...")
        try:
            result = _run_analysis(img_path)
            results.append({
                "filename": img_path.name,
                "category": "clean",
                "overall_score": result["overall_score"],
                "verdict": result["verdict"],
                **{f"{tech}_score": round(data["score"], 1)
                   for tech, data in result["techniques"].items()},
            })
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                "filename": img_path.name,
                "category": "clean",
                "overall_score": -1,
                "verdict": "error",
            })

    # Process tampered documents
    for img_path in sorted(tampered_dir.glob("*")):
        if img_path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".pdf"):
            continue
        print(f"Analyzing tampered: {img_path.name}...")
        try:
            result = _run_analysis(img_path)
            results.append({
                "filename": img_path.name,
                "category": "tampered",
                "overall_score": result["overall_score"],
                "verdict": result["verdict"],
                **{f"{tech}_score": round(data["score"], 1)
                   for tech, data in result["techniques"].items()},
            })
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                "filename": img_path.name,
                "category": "tampered",
                "overall_score": -1,
                "verdict": "error",
            })

    # Print table
    print("\n" + "=" * 100)
    print("VALIDATION RESULTS")
    print("=" * 100)

    header = f"{'File':<30} {'Category':<10} {'Score':<8} {'Verdict':<18} {'ELA':<8} {'Noise':<8} {'Clone':<8} {'Meta':<8} {'JPEG':<8} {'OCR':<8}"
    print(header)
    print("-" * 100)

    for r in results:
        row = (
            f"{r['filename']:<30} "
            f"{r['category']:<10} "
            f"{r['overall_score']:<8} "
            f"{r['verdict']:<18} "
            f"{r.get('ela_score', 'N/A'):<8} "
            f"{r.get('noise_score', 'N/A'):<8} "
            f"{r.get('copymove_score', 'N/A'):<8} "
            f"{r.get('metadata_score', 'N/A'):<8} "
            f"{r.get('jpeg_ghost_score', 'N/A'):<8} "
            f"{r.get('ocr_score', 'N/A'):<8}"
        )
        print(row)

    print("=" * 100)

    # Summary
    clean_scores = [r["overall_score"] for r in results if r["category"] == "clean" and r["overall_score"] >= 0]
    tampered_scores = [r["overall_score"] for r in results if r["category"] == "tampered" and r["overall_score"] >= 0]

    if clean_scores:
        print(f"\nClean documents: {len(clean_scores)} images, avg score: {sum(clean_scores)/len(clean_scores):.1f}")
    if tampered_scores:
        print(f"Tampered documents: {len(tampered_scores)} images, avg score: {sum(tampered_scores)/len(tampered_scores):.1f}")

    # Save CSV
    csv_path = base_dir / "validation_results.csv"
    if results:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\nResults saved to: {csv_path}")


def _run_analysis(img_path: Path) -> dict:
    """Run analysis on a single image file."""
    with open(img_path, "rb") as f:
        contents = f.read()
    return run_analysis(contents, img_path.name)


if __name__ == "__main__":
    validate()
