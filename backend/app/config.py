from pathlib import Path
from dataclasses import dataclass


@dataclass
class Settings:
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    RESULTS_DIR: Path = BASE_DIR / "results"
    HEATMAP_DIR: Path = BASE_DIR / "heatmaps"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list = None

    # ELA
    ELA_QUALITY: int = 90
    ELA_GAIN: float = 10.0
    ELA_THRESHOLD: float = 0.15

    # Noise analysis
    NOISE_BLOCK_SIZE: int = 64
    NOISE_SIGMA_THRESHOLD: float = 2.0
    NOISE_WAVELET: str = "db4"

    # Copy-move (PCA-based)
    COPYMOVE_BLOCK_SIZE: int = 32
    COPYMOVE_MIN_FREQUENCY: int = 50
    COPYMOVE_MIN_MAGNITUDE: float = 30.0

    # JPEG Ghost
    JPEG_GHOST_DCT_BINS: int = 64

    # OCR
    OCR_LANGUAGES: list = None
    OCR_PSM_MODES: list = None
    OCR_ZSCORE_THRESHOLD: float = 2.5

    # Fusion weights
    FUSION_WEIGHTS: dict = None

    # Verdict thresholds
    VERDICT_SUSPICIOUS: int = 31
    VERDICT_TAMPERED: int = 61

    def __post_init__(self):
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        self.HEATMAP_DIR.mkdir(parents=True, exist_ok=True)

        if self.CORS_ORIGINS is None:
            self.CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]

        if self.OCR_LANGUAGES is None:
            self.OCR_LANGUAGES = ["en"]

        if self.OCR_PSM_MODES is None:
            self.OCR_PSM_MODES = [6, 11]

        if self.FUSION_WEIGHTS is None:
            self.FUSION_WEIGHTS = {
                "ela": 0.20,
                "noise": 0.25,
                "copymove": 0.20,
                "metadata": 0.10,
                "jpeg_ghost": 0.10,
                "ocr": 0.15,
            }


settings = Settings()
