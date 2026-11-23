#!/usr/bin/env bash
set -e

echo "==================================================="
echo "   Bulk Background Remover - macOS Setup Script"
echo "==================================================="
echo ""

# Find available Python (prefer python3)
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python 3 is not installed or not in your PATH."
    echo "Please install Python 3.11 from python.org or via Homebrew: 'brew install python@3.11'"
    exit 1
fi

echo "[INFO] Using: $($PYTHON_CMD --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment 'venv'..."
    $PYTHON_CMD -m venv venv
fi

echo "[INFO] Activating virtual environment..."
source venv/bin/activate

echo "[INFO] Upgrading pip and installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "==================================================="
echo "[SUCCESS] Environment setup complete on macOS!"
echo "Run './start_mac.sh' to launch the application."
echo "==================================================="
