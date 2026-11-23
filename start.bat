@echo off
setlocal enabledelayedexpansion
title Bulk Background Remover

echo ===================================================
echo     Bulk Background Remover - Windows Launcher
echo ===================================================
echo.

:: Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.11 from python.org and check "Add Python to PATH".
    pause
    exit /b 1
)

:: Check if virtual environment exists, if not create it
if not exist "venv" (
    echo [INFO] Virtual environment not found. Creating 'venv'...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [INFO] Installing required dependencies...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install requirements.
        pause
        exit /b 1
    )
    echo [SUCCESS] Environment created and dependencies installed successfully!
    echo.
) else (
    call venv\Scripts\activate.bat
)

echo [INFO] Starting Streamlit application on http://127.0.0.1:8501 ...
echo [INFO] Close this command window anytime to stop the server.
echo.

streamlit run app.py --server.address=127.0.0.1 --server.port=8501 --browser.gatherUsageStats=false

pause
