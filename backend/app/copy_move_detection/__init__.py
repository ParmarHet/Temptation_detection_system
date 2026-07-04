"""Copy-Move Detection package.

Based on the implementation from:
https://github.com/ashishpatel26/image-copy-move-detection

Uses PCA + 7 characteristic features for block-based copy-move detection.
"""

from app.copy_move_detection.detect import detect

__all__ = ["detect"]
