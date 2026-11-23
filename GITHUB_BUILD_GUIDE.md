# Triggering the Windows Installer Cloud Build from macOS

This guide explains how to automatically build **`BulkBackgroundRemover_Setup.exe`** using GitHub Actions with a Windows runner.

You do **not** need a Windows machine to build the installer. GitHub's cloud Windows runner compiles the Python environment, packages Streamlit and rembg via PyInstaller, bundles the U2Net model weights, and compiles the Inno Setup installer.

---

## Step 1: Initialize Git and Connect to GitHub

From your project directory on macOS:

```bash
# 1. Review status of tracked files
git status

# 2. Add files and commit
git add .
git commit -m "Add GitHub Actions workflow for automated Windows installer build"

# 3. Create or set your GitHub remote repository (if not already done)
# Replace with your actual GitHub username and repository name:
git remote add origin https://github.com/YOUR_USERNAME/Bulk-Background-Remover.git
git branch -M main
```

---

## Step 2: Push to GitHub to Start the Build

Push your code to GitHub:
```bash
git push -u origin main
```

The GitHub Actions workflow defined in [`.github/workflows/build-windows-installer.yml`](.github/workflows/build-windows-installer.yml) triggers automatically on push.

---

## Step 3: Track the Build in Your Browser

1. Open your repository on GitHub (`https://github.com/YOUR_USERNAME/Bulk-Background-Remover`).
2. Click the **Actions** tab at the top.
3. You will see the running workflow: **"Build Windows Desktop Installer"**.
4. The workflow will:
   - Spin up a fresh `windows-latest` VM.
   - Install Python 3.11 and Inno Setup via Chocolatey.
   - Install all required libraries (`streamlit`, `rembg`, `onnxruntime`, `pillow`).
   - Download the official `u2net.onnx` model weights into `models/u2net.onnx`.
   - Bundle everything into a standalone package with PyInstaller.
   - Compile `BulkBackgroundRemover_Setup.exe` using Inno Setup.

---

## Step 4: Download the Installer for Your Inventory Staff

1. When the run finishes (green checkmark, usually ~3–5 minutes), click on the completed run.
2. Scroll to the bottom to the **Artifacts** section.
3. Click on **`BulkBackgroundRemover_Setup`** to download the zip file.
4. Unzip to get **`BulkBackgroundRemover_Setup.exe`**.

---

## Step 5: What Your Inventory Staff Experiences on Windows 10/11

1. **One-Click Installation**: The user double-clicks `BulkBackgroundRemover_Setup.exe`.
2. **Desktop Shortcut**: An icon named **"Bulk Background Remover"** is created on their desktop.
3. **Zero Configuration**:
   - No Python or terminal required.
   - No internet required during daily work (model is pre-bundled).
   - Double-clicking the shortcut launches the app and opens the dashboard at `http://localhost:8501`.
   - Single-instance protection prevents multiple background servers from colliding.
   - Fully uninstallable via Windows "Add or remove programs".
