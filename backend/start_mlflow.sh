#!/bin/bash
# Start MLflow Tracking Server
# Requirements: 51.9 - Setup MLflow experiment tracking

set -e

echo "=========================================="
echo "Starting MLflow Tracking Server"
echo "=========================================="

# Change to backend directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Warning: Virtual environment not found at ./venv"
    echo "Using system Python..."
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if MLflow is installed
if ! python -c "import mlflow" 2>/dev/null; then
    echo "Error: MLflow is not installed"
    echo "Install with: pip install mlflow>=2.9.0"
    exit 1
fi

# Run setup script to initialize experiments
echo "Initializing MLflow experiments..."
python setup_mlflow.py --init-only

# Start MLflow server
echo ""
echo "Starting MLflow server..."
python setup_mlflow.py --start-server

