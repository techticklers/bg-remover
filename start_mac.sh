#!/usr/bin/env bash
set -e

echo "==================================================="
echo "   Bulk Background Remover - macOS Launcher"
echo "==================================================="
echo ""

if [ ! -d "venv" ]; then
    echo "[WARNING] Virtual environment 'venv' not found."
    echo "Running './setup_mac.sh' first..."
    ./setup_mac.sh
fi

source venv/bin/activate

echo "[INFO] Starting Streamlit application on http://127.0.0.1:8501..."
echo "[INFO] Press Ctrl+C anytime to stop."
echo ""

streamlit run app.py --server.address=127.0.0.1 --server.port=8501 --browser.gatherUsageStats=false
