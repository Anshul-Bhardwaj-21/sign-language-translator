# Start Sign Language Inference Service
# Usage: .\start_inference_service.ps1 [-Reload]

param(
    [switch]$Reload
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Sign Language Inference Service Startup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if MediaPipe model exists
$MediaPipeModel = "backend\storage\datasets\hand_landmarker.task"
if (-not (Test-Path $MediaPipeModel)) {
    Write-Host "⚠️  MediaPipe hand landmarker model not found" -ForegroundColor Yellow
    Write-Host "Downloading model..."
    python backend\storage\datasets\download_mediapipe_model.py
    Write-Host ""
}

# Check if MLflow is running
Write-Host "Checking MLflow connection..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ MLflow is running" -ForegroundColor Green
} catch {
    Write-Host "⚠️  MLflow is not running" -ForegroundColor Yellow
    Write-Host "Please start MLflow first:"
    Write-Host "  .\backend\start_mlflow.ps1"
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

# Set environment variables
$env:MLFLOW_TRACKING_URI = "http://localhost:5000"
$env:MODEL_NAME = "sign-language-asl"
$env:CONFIDENCE_THRESHOLD = "0.7"

Write-Host ""
Write-Host "Configuration:"
Write-Host "  MLflow URI: $env:MLFLOW_TRACKING_URI"
Write-Host "  Model Name: $env:MODEL_NAME"
Write-Host "  Confidence Threshold: $env:CONFIDENCE_THRESHOLD"
Write-Host ""

# Check for reload flag
$ReloadFlag = ""
if ($Reload) {
    $ReloadFlag = "--reload"
    Write-Host "Starting with auto-reload enabled..." -ForegroundColor Yellow
} else {
    Write-Host "Starting in production mode..." -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting inference service on port 8001" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Start the service
Set-Location backend
python inference_service.py --host 0.0.0.0 --port 8001 $ReloadFlag
