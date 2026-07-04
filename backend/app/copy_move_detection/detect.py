"""Copy-Move Detection entry point.

Based on the implementation from:
https://github.com/ashishpatel26/image-copy-move-detection
"""

from pathlib import Path
from app.copy_move_detection.image_object import ImageObject


def detect(input_path, output_path, block_size=32):
    """
    Detects copy-move forgery in an image.

    :param input_path: path to input image
    :param output_path: path to output folder
    :param block_size: the block size of the image pointer (eg. 32, 64, 128)
        The smaller the block size, the more accurate the result is, but takes more time.
    :return: path to the result image
    """

    input_path = Path(input_path)
    filename = input_path.name
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Source file did not exist: {input_path}")
    elif not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)

    single_image = ImageObject(input_path, filename, output_path, block_size)
    image_result_path = single_image.run()

    return image_result_path
