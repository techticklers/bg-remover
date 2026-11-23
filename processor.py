"""
Core image processing pipeline for background removal, auto-centering,
and canvas fitting.
"""

from typing import Tuple, Optional
from PIL import Image
import numpy as np


def process_image(
    input_path_or_bytes,
    rembg_session,
    canvas_size: Tuple[int, int] = (2000, 2000),
    padding_percent: float = 0.10,
    export_format: str = "both",  # "transparent", "white", "both"
    jpg_quality: int = 95
) -> dict:
    """
    Takes an image, removes background with rembg, crops to the foreground subject's
    bounding box, and centers it on a fixed canvas with specified padding.
    
    Returns a dict with:
      - 'transparent': PIL.Image (RGBA) or None
      - 'white': PIL.Image (RGB) or None
      - 'bbox': tuple of bounding box (left, upper, right, lower)
    """
    from rembg import remove

    # 1. Open image cleanly and handle orientation/modes
    if isinstance(input_path_or_bytes, (str, bytes)):
        img = Image.open(input_path_or_bytes)
    else:
        # File-like object (e.g. UploadedFile)
        img = Image.open(input_path_or_bytes)

    # Convert to RGBA for clean alpha handling
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # 2. Background removal using rembg session
    cutout = remove(img, session=rembg_session)

    # 3. Compute bounding box of foreground (non-transparent pixels)
    # cutout.getbbox() extracts bounding box of non-zero alpha
    alpha = cutout.split()[-1]
    bbox = alpha.getbbox()

    if bbox is None:
        # Image was completely transparent or removal removed everything
        # Fallback to entire image
        cropped = cutout
    else:
        cropped = cutout.crop(bbox)

    crop_w, crop_h = cropped.size

    # 4. Calculate target subject dimensions inside canvas considering padding
    target_canvas_w, target_canvas_h = canvas_size
    max_w = int(target_canvas_w * (1.0 - 2 * padding_percent))
    max_h = int(target_canvas_h * (1.0 - 2 * padding_percent))

    if max_w <= 0 or max_h <= 0:
        max_w, max_h = target_canvas_w, target_canvas_h

    # Calculate scale factor preserving aspect ratio
    scale = min(max_w / max(crop_w, 1), max_h / max(crop_h, 1))
    new_w = max(1, int(crop_w * scale))
    new_h = max(1, int(crop_h * scale))

    # Resize cropped foreground
    # Using Resampling.LANCZOS for highest quality downscaling/upscaling
    resized_crop = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Calculate centered position (paste coordinates)
    paste_x = (target_canvas_w - new_w) // 2
    paste_y = (target_canvas_h - new_h) // 2

    results = {
        "transparent": None,
        "white": None,
        "bbox": bbox
    }

    # 5. Build Transparent PNG canvas
    if export_format in ("transparent", "both"):
        trans_canvas = Image.new("RGBA", (target_canvas_w, target_canvas_h), (0, 0, 0, 0))
        trans_canvas.paste(resized_crop, (paste_x, paste_y), mask=resized_crop)
        results["transparent"] = trans_canvas

    # 6. Build White Background JPG canvas
    if export_format in ("white", "both"):
        white_canvas = Image.new("RGB", (target_canvas_w, target_canvas_h), (255, 255, 255))
        # Paste with alpha mask to blend smoothly against white
        white_canvas.paste(resized_crop, (paste_x, paste_y), mask=resized_crop)
        results["white"] = white_canvas

    return results
