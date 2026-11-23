# Bulk Background Remover Studio

A cross-platform, production-grade, 100% offline bulk product photo background removal and centering application for high-volume batches (500 to 5,000+ images).

- **Development OS**: macOS
- **Target Production OS**: Windows 10 / Windows 11
- **Target Python Version**: Python 3.11 (Python 3.9 - 3.12 compatible)
- **AI Core**: `rembg` (U2Net) + ONNX Runtime CPU (default) / NVIDIA CUDA (optional)
- **Localhost URL**: `http://127.0.0.1:8501`

---

## 🌟 Key Upgrades & Features

1. **Hardware Detection & Optional GPU Acceleration**:
   - **CPU Mode (Default)**: Guaranteed cross-platform stability out of the box.
   - **GPU Mode (NVIDIA CUDA)**: Automatic detection of `CUDAExecutionProvider`. If GPU is requested on non-CUDA machines (such as macOS or PCs without NVIDIA drivers), it falls back seamlessly to CPU with an informative dashboard notification.
2. **Professional Dark Theme Dashboard**:
   - High-contrast, theme-resilient styling for dark mode readability.
   - Header bar with dynamic OS and architecture pill.
   - Live telemetry: elapsed time, real-time item ETA, completion count, and failure counters.
   - Expandable error viewer with detailed failure logs.
   - One-click native OS button to open the output folder in Windows Explorer or macOS Finder.
3. **Settings-Aware Batch Resumption**:
   - Stores configuration state (`canvas_dim`, `padding_pct`, `export_format`) in `batch_status.json`.
   - Skips already-processed files across runs, and resets queue if canvas settings change to prevent mixed aspect ratios.
   - Concurrent atomic directory lock (`.batch_worker.lock`) prevents multiple jobs from corrupting output directories.
4. **Windows Desktop Installer Workflow**:
   - Standalone desktop build workflow via PyInstaller (`build_windows_exe.bat` + `BulkBackgroundRemover.spec`).
   - Single-instance execution guard (`desktop_launcher.py`) that brings the running instance to focus instead of launching multiple servers.
   - Inno Setup installer script (`installer.iss`) to produce a Windows installer with a Desktop shortcut.

---

## 💻 Quick Start Launchers

### macOS Launchers
1. **Initial Setup**:
   ```bash
   ./setup_mac.sh
   ```
2. **Launch Application**:
   ```bash
   ./start_mac.sh
   ```
   Open `http://127.0.0.1:8501` in your browser.

### Windows 10/11 Batch Launchers (Non-Technical Operators)
1. **Initial Setup**: Double-click `setup_windows.bat` (creates isolated `venv` and installs packages).
2. **Launch Application**: Double-click `start_windows.bat` (activates `venv` and starts Streamlit).

---

## 📦 Building the Windows Desktop Installer (.exe)

> **Important**: Build and test this workflow on a physical Windows 10/11 PC. Do not attempt to cross-compile Windows executables from macOS.

### Step 1: Build the Standalone Binary with PyInstaller
On your Windows machine with Python 3.11 installed:
1. Run `setup_windows.bat` to create the environment.
2. Double-click **`build_windows_exe.bat`**.
   - This installs PyInstaller and executes `BulkBackgroundRemover.spec`.
   - Output files are generated in `dist\BulkBackgroundRemover\`.

### Step 2: Compile the Windows Installer with Inno Setup
1. Install [Inno Setup 6](https://jrsoftware.org/isdl.php) on Windows.
2. Open **`installer.iss`** in Inno Setup.
3. Click **Compile** (`Ctrl + F9`).
4. The compiled installer (`BulkBackgroundRemover_Setup_v1.2.0.exe`) will be generated.
5. Installing it creates a desktop shortcut **"Bulk Background Remover"** that launches the local server and opens `http://localhost:8501` automatically without terminal windows.

---

## ⚡ NVIDIA GPU Acceleration Guide (Windows Only)

By default, the application runs on ONNX Runtime CPU. To enable optional NVIDIA CUDA acceleration on a Windows PC with an NVIDIA GPU:

### Prerequisites & Compatible Version Matrix
- **Python**: 3.11.x (64-bit)
- **NVIDIA Driver**: 535.xx or newer
- **CUDA Toolkit**: 11.8 or 12.x
- **cuDNN**: 8.9.x (matching CUDA version)
- **ONNX Runtime**: `onnxruntime-gpu==1.19.2`

### Enabling GPU Mode on Windows:
In an activated Windows virtual environment:
```cmd
pip uninstall -y onnxruntime
pip install onnxruntime-gpu==1.19.2
```
*Note: Never install `onnxruntime` and `onnxruntime-gpu` into the same environment simultaneously.*

In the application sidebar under **⚡ Hardware & Acceleration**, select:
- **Auto**: Automatically uses CUDA if available; otherwise falls back to CPU.
- **GPU (CUDA)**: Forces CUDA execution with verified provider status.

---

## 🧪 Automated Testing
Run the test suite on any environment:
```bash
python test_pipeline.py
```
Validates:
1. Hardware detection & graceful GPU fallback.
2. AI session instantiation with specified execution providers.
3. Directory scanning and path overlap safety checks.
4. Non-destructive background removal, centering, and canvas padding.
5. Batch resumption and settings invalidation logic.

---

## 🛡️ License & Commercial Safety
- **rembg**: MIT License
- **U2Net Model**: Apache 2.0 License
- **ONNX Runtime**: MIT License
- **Streamlit**: Apache 2.0 License
- **Pillow**: HPND License
