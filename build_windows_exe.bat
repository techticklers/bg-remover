@echo off
setlocal enabledelayedexpansion
title Build Windows Desktop App (PyInstaller)

echo ===================================================
echo   Building Bulk Background Remover Windows App
echo ===================================================
echo.

:: 1. Ensure venv is activated
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment 'venv' not found.
    echo Please run 'setup_windows.bat' first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

:: 2. Ensure PyInstaller is installed
echo [INFO] Installing PyInstaller...
pip install pyinstaller

:: 3. Run PyInstaller with Spec file
echo [INFO] Running PyInstaller build...
pyinstaller --noconfirm --clean BulkBackgroundRemover.spec

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo ===================================================
echo [SUCCESS] Windows App built successfully!
echo Binary output location: dist\BulkBackgroundRemover\
echo ===================================================
echo You can now compile the installer using Inno Setup (installer.iss)
pause
