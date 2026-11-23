"""
Desktop Application Entrypoint for PyInstaller.
1. Ensures single-instance execution via local socket lock.
2. Directs U2Net model weights, Streamlit, and temp files to a writable user directory:
   %USERPROFILE%\\.u2net\\u2net.onnx.
3. Automatically copies pre-bundled offline u2net.onnx if present in the installer bundle.
4. Spawns Streamlit headless on 127.0.0.1:8501 and automatically opens the default web browser.
"""

import os
import sys
import time
import socket
import shutil
import webbrowser
import subprocess
from pathlib import Path

# Port and address configuration
PORT = 8501
HOST = "127.0.0.1"
LOCK_PORT = 49152  # Local socket port for single-instance guard

def ensure_single_instance():
    """
    Prevents multiple application instances from running concurrently.
    Binds a non-reusable local socket.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((HOST, LOCK_PORT))
        return s  # Hold reference so socket remains open
    except socket.error:
        print("[WARNING] Another instance of Bulk Background Remover is already running.")
        webbrowser.open(f"http://{HOST}:{PORT}")
        sys.exit(0)

def configure_offline_models():
    """
    Sets U2NET_HOME and copies pre-bundled model weights if present.
    Ensures 100% offline immediate operation upon install.
    """
    # Standard U2Net cache directory in user profile
    u2net_dir = Path.home() / ".u2net"
    u2net_dir.mkdir(parents=True, exist_ok=True)
    target_model = u2net_dir / "u2net.onnx"

    os.environ["U2NET_HOME"] = str(u2net_dir)

    # Check if bundled model exists in PyInstaller runtime or app directory
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    bundled_model_candidates = [
        base_dir / "models" / "u2net.onnx",
        base_dir / "u2net.onnx",
        Path(__file__).parent / "models" / "u2net.onnx"
    ]

    if not target_model.exists():
        for candidate in bundled_model_candidates:
            if candidate.exists():
                try:
                    shutil.copy2(candidate, target_model)
                    print(f"[INFO] Installed pre-bundled offline AI model to {target_model}")
                    break
                except Exception as e:
                    print(f"[WARNING] Could not copy bundled model: {e}")

def wait_for_server(host, port, timeout=25):
    """Waits until the Streamlit HTTP server starts listening."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            time.sleep(0.5)
    return False

def main():
    lock_socket = ensure_single_instance()
    configure_offline_models()

    # Determine script path depending on frozen PyInstaller state
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
        app_script = base_path / "app.py"
    else:
        base_path = Path(__file__).parent
        app_script = base_path / "app.py"

    # Launch Streamlit process
    streamlit_cmd = [
        sys.executable,
        "-m", "streamlit", "run",
        str(app_script),
        f"--server.address={HOST}",
        f"--server.port={PORT}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]

    proc = subprocess.Popen(streamlit_cmd)

    # Wait for server and open browser
    if wait_for_server(HOST, PORT):
        webbrowser.open(f"http://{HOST}:{PORT}")

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()

if __name__ == "__main__":
    main()
