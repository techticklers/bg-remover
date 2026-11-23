@echo off
setlocal enabledelayedexpansion
title Bulk Background Remover

echo ===================================================
echo     Bulk Background Remover - Windows Launcher
echo ===================================================
echo.

:: Check if virtual environment exists
if not exist "venv" (
    echo [INFO] Virtual environment not found. Setting up first...
    call setup_windows.bat
)

call venv\Scripts\activate.bat

echo [INFO] Starting application on http://127.0.0.1:8501 ...
echo [INFO] Close this window anytime to stop the server.
echo.

streamlit run app.py --server.address=127.0.0.1 --server.port=8501 --browser.gatherUsageStats=false

pause
