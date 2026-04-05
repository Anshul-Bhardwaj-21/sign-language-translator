#!/bin/bash

# Bash script to run backend in development mode

echo "Starting Sign Language Video Call Backend..."
echo "============================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check Python version
echo "Python version: $(python3 --version)"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv .venv
    echo "Virtual environment created!"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q fastapi uvicorn websockets python-multipart pydantic opencv-python numpy

echo ""
echo "Backend server starting on http://localhost:8001"
echo "Press Ctrl+C to stop"
echo ""

# Run server
python backend/simple_server.py
