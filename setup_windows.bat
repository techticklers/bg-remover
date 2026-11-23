@echo off
setlocal enabledelayedexpansion
title Bulk Background Remover - Setup

echo ===================================================
echo   Bulk Background Remover - Windows Setup Script
echo ===================================================
echo.

:: Check for Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please download and install Python 3.11 from:
    echo   https://www.python.org/downloads/
    echo.
    echo Make sure to check the box: "Add python.exe to PATH"
    pause
    exit /b 1
)

echo [INFO] Python found:
python --version

:: Create virtual environment
if not exist "venv" (
    echo [INFO] Creating virtual environment 'venv'...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Upgrading pip and installing dependencies from requirements.txt...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Dependency installation encountered an issue.
    pause
    exit /b 1
)

echo.
echo ===================================================
echo [SUCCESS] Windows setup completed successfully!
echo You can now double-click 'start_windows.bat' to run.
echo ===================================================
pause
