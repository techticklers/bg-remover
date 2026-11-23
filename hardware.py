"""
Hardware detection and ONNX Runtime execution provider management.
Supports seamless CPU default, optional NVIDIA CUDA acceleration, and graceful fallback.
"""

import sys
import logging
import platform
from typing import Tuple, List

logger = logging.getLogger("HardwareDetector")

def get_available_providers() -> List[str]:
    """
    Returns list of ONNX Runtime execution providers available in current environment.
    """
    try:
        import onnxruntime as ort
        return ort.get_available_providers()
    except Exception as e:
        logger.warning(f"Error querying ONNX Runtime providers: {e}")
        return ["CPUExecutionProvider"]


def detect_hardware() -> dict:
    """
    Detects system OS, architecture, and available ONNX acceleration providers.
    """
    providers = get_available_providers()
    has_cuda = "CUDAExecutionProvider" in providers
    has_coreml = "CoreMLExecutionProvider" in providers
    has_directml = "DmlExecutionProvider" in providers

    return {
        "os": platform.system(),
        "arch": platform.machine(),
        "python_version": platform.python_version(),
        "available_providers": providers,
        "has_cuda": has_cuda,
        "has_coreml": has_coreml,
        "has_directml": has_directml
    }


def resolve_execution_provider(device_preference: str = "Auto") -> Tuple[str, List[str], str]:
    """
    Resolves the actual ONNX execution providers list based on user preference and hardware.
    
    device_preference: 'Auto', 'CPU', 'GPU (CUDA)'
    
    Returns:
      (active_device_label, providers_list, notification_message)
    """
    available = get_available_providers()
    has_cuda = "CUDAExecutionProvider" in available

    if device_preference == "CPU":
        return ("CPU", ["CPUExecutionProvider"], "Running on CPU (User selected).")

    if device_preference == "GPU (CUDA)":
        if has_cuda:
            # CUDA with CPU fallback
            return ("GPU (NVIDIA CUDA)", ["CUDAExecutionProvider", "CPUExecutionProvider"], "Running with NVIDIA CUDA acceleration.")
        else:
            return (
                "CPU (Fallback)",
                ["CPUExecutionProvider"],
                "⚠️ GPU requested but CUDAExecutionProvider is unavailable. Falling back to CPU. Ensure onnxruntime-gpu, CUDA 11.8/12.x, and cuDNN are installed."
            )

    # Auto mode:
    if has_cuda:
        return ("GPU (NVIDIA CUDA)", ["CUDAExecutionProvider", "CPUExecutionProvider"], "Auto-detected NVIDIA CUDA acceleration.")
    
    return ("CPU", ["CPUExecutionProvider"], "Running on CPU (Default reliable provider).")


def create_rembg_session(model_name: str = "u2net", providers: List[str] = None):
    """
    Creates a rembg Session using the specified ONNX providers.
    Safely falls back to CPU if initialization fails.
    """
    import rembg
    if providers is None:
        providers = ["CPUExecutionProvider"]

    try:
        # rembg.new_session supports providers parameter in recent versions
        return rembg.new_session(model_name=model_name, providers=providers)
    except Exception as e:
        logger.warning(f"Failed to initialize session with {providers}: {e}. Falling back to default CPU session.")
        return rembg.new_session(model_name=model_name, providers=["CPUExecutionProvider"])
