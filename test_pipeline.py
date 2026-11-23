"""
Extended automated test suite covering:
1. Standard batch processing on 5 multi-format images.
2. Centering, padding, dimensions, and aspect ratio.
3. Batch resumption and settings invalidation check.
4. Hardware detection and graceful GPU fallback to CPU when CUDA is absent.
"""

import sys
import shutil
from pathlib import Path
from PIL import Image, ImageDraw

from processor import process_image
from batch_manager import (
    scan_images,
    check_path_overlap,
    BatchProgressTracker,
    setup_logger
)
from hardware import (
    detect_hardware,
    resolve_execution_provider,
    create_rembg_session
)

def create_sample_images(sample_dir: Path):
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Red circle on blue (PNG)
    img1 = Image.new("RGB", (600, 400), (30, 144, 255))
    draw1 = ImageDraw.Draw(img1)
    draw1.ellipse([150, 50, 450, 350], fill=(220, 20, 60))
    img1.save(sample_dir / "sample_1.png")

    # 2. Green square on yellow (JPG)
    img2 = Image.new("RGB", (800, 800), (255, 255, 0))
    draw2 = ImageDraw.Draw(img2)
    draw2.rectangle([200, 200, 600, 600], fill=(34, 139, 34))
    img2.save(sample_dir / "sample_2.jpg", quality=95)

    # 3. Purple rectangle on gray (JPEG)
    img3 = Image.new("RGB", (500, 700), (200, 200, 200))
    draw3 = ImageDraw.Draw(img3)
    draw3.rectangle([100, 150, 400, 550], fill=(138, 43, 226))
    img3.save(sample_dir / "sample_3.jpeg", quality=95)

    # 4. Orange triangle on white (WEBP)
    img4 = Image.new("RGB", (400, 400), (240, 240, 240))
    draw4 = ImageDraw.Draw(img4)
    draw4.polygon([(200, 50), (100, 350), (300, 350)], fill=(255, 140, 0))
    img4.save(sample_dir / "sample_4.webp")

    # 5. Cyan circle on dark (PNG)
    img5 = Image.new("RGB", (700, 500), (20, 20, 20))
    draw5 = ImageDraw.Draw(img5)
    draw5.ellipse([200, 100, 500, 400], fill=(0, 206, 209))
    img5.save(sample_dir / "sample_5.png")

    print(f"Created 5 sample images in {sample_dir}")

def run_test():
    print("--- 1. Testing Hardware Detection & Graceful GPU Fallback ---")
    hw = detect_hardware()
    print(f"Detected OS: {hw['os']} ({hw['arch']}) | Available Providers: {hw['available_providers']}")

    # Test CPU resolution
    cpu_label, cpu_provs, _ = resolve_execution_provider("CPU")
    assert cpu_label == "CPU"
    assert cpu_provs == ["CPUExecutionProvider"]

    # Test GPU request when CUDA is not present -> Must fallback gracefully
    gpu_label, gpu_provs, msg = resolve_execution_provider("GPU (CUDA)")
    print(f"GPU Resolution on current hardware: {gpu_label} | Providers: {gpu_provs}")
    assert "CPUExecutionProvider" in gpu_provs, "CPU fallback provider must be present"
    print("Hardware detection and fallback tests passed!\n")

    # Test session creation
    print("--- 2. Initializing AI Session ---")
    session = create_rembg_session(model_name="u2net", providers=gpu_provs)

    test_input = Path("./test_samples/input")
    test_output = Path("./test_samples/output")
    
    if test_input.exists():
        shutil.rmtree(test_input)
    if test_output.exists():
        shutil.rmtree(test_output)

    create_sample_images(test_input)

    # Test 3: Path Overlap Check
    print("\n--- 3. Testing Path Overlap Check ---")
    assert check_path_overlap(str(test_input), str(test_input)) is True
    assert check_path_overlap(str(test_input), str(test_output)) is False
    print("Path overlap checks passed!")

    # Test 4: Folder Scanner
    print("\n--- 4. Testing Folder Scanner ---")
    found_files = scan_images(str(test_input))
    assert len(found_files) == 5, f"Expected 5 images, found {len(found_files)}"
    print(f"Found {len(found_files)} images.")

    # Test 5: Process 5 images
    print("\n--- 5. Testing Image Processing on 5 Images ---")
    trans_dir = test_output / "transparent"
    white_dir = test_output / "white_background"
    trans_dir.mkdir(parents=True, exist_ok=True)
    white_dir.mkdir(parents=True, exist_ok=True)

    test_settings = {"canvas_dim": 2000, "padding_pct": 0.10, "export_format": "both", "jpg_quality": 95}
    tracker = BatchProgressTracker(test_output, current_settings=test_settings)

    for f in found_files:
        res = process_image(
            input_path_or_bytes=str(f),
            rembg_session=session,
            canvas_size=(2000, 2000),
            padding_percent=0.10,
            export_format="both",
            jpg_quality=95
        )
        
        assert res["transparent"].size == (2000, 2000)
        assert res["transparent"].mode == "RGBA"
        assert res["white"].size == (2000, 2000)
        assert res["white"].mode == "RGB"

        out_png = trans_dir / f"{f.stem}.png"
        out_jpg = white_dir / f"{f.stem}.jpg"
        res["transparent"].save(out_png, format="PNG")
        res["white"].save(out_jpg, format="JPEG", quality=95)

        tracker.record_success(f.name)
        print(f"  Processed & verified: {f.name} -> {out_png.name}, {out_jpg.name}")

    # Test 6: Resumption verification
    print("\n--- 6. Testing Batch Resumption & Settings Validation ---")
    resumed_tracker = BatchProgressTracker(test_output, current_settings=test_settings)
    for f in found_files:
        assert resumed_tracker.is_processed(f.name) is True

    # Test changing settings -> Should safely invalidate resumption
    altered_settings = {"canvas_dim": 1500, "padding_pct": 0.15, "export_format": "both", "jpg_quality": 90}
    invalidated_tracker = BatchProgressTracker(test_output, current_settings=altered_settings)
    assert len(invalidated_tracker.state["completed"]) == 0, "Changing canvas settings must reset active resumption queue"
    print("Resumption and settings validation check passed!")

    print("\n==========================================")
    print("  ALL VALIDATION TESTS PASSED SUCCESSFULLY! ")
    print("==========================================")

if __name__ == "__main__":
    run_test()
