# Start MLflow Tracking Server (PowerShell)
# Requirements: 51.9 - Setup MLflow experiment tracking

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting MLflow Tracking Server" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Change to backend directory
Set-Location $PSScriptRoot

# Check if virtual environment exists
if (-Not (Test-Path "venv")) {
    Write-Host "Warning: Virtual environment not found at ./venv" -ForegroundColor Yellow
    Write-Host "Using system Python..." -ForegroundColor Yellow
}

# Activate virtual environment if it exists
if (Test-Path "venv/Scripts/Activate.ps1") {
    & "venv/Scripts/Activate.ps1"
}

# Check if MLflow is installed
try {
    python -c "import mlflow" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "MLflow import failed"
    }
} catch {
    Write-Host "Error: MLflow is not installed" -ForegroundColor Red
    Write-Host "Install with: pip install mlflow>=2.9.0" -ForegroundColor Yellow
    exit 1
}

# Run setup script to initialize experiments
Write-Host ""
Write-Host "Initializing MLflow experiments..." -ForegroundColor Green
python setup_mlflow.py --init-only

# Start MLflow server
Write-Host ""
Write-Host "Starting MLflow server..." -ForegroundColor Green
python setup_mlflow.py --start-server

