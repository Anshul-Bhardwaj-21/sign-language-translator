# Quick start script for training sign language model (PowerShell)
# Usage: .\backend\models\run_training.ps1

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Sign Language Model Training" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if preprocessed data exists
if (-not (Test-Path "backend\storage\datasets\v1.0.0\processed")) {
    Write-Host "Error: Preprocessed dataset not found!" -ForegroundColor Red
    Write-Host "Please run preprocessing first:"
    Write-Host "  python backend\storage\datasets\preprocess_dataset.py"
    exit 1
}

# Check if split files exist
if (-not (Test-Path "backend\storage\datasets\v1.0.0\splits\train.txt")) {
    Write-Host "Error: Dataset split files not found!" -ForegroundColor Red
    Write-Host "Please create splits first:"
    Write-Host "  python backend\storage\datasets\create_splits.py"
    exit 1
}

# Create checkpoints directory
New-Item -ItemType Directory -Force -Path "backend\models\checkpoints" | Out-Null

# Run training with default configuration
Write-Host "Starting training with default configuration..." -ForegroundColor Green
Write-Host "  - Learning rate: 0.001"
Write-Host "  - Batch size: 32"
Write-Host "  - Max epochs: 100"
Write-Host "  - Early stopping: patience=10, min_delta=0.001"
Write-Host ""

python backend\models\train_model.py `
    --data-dir backend\storage\datasets\v1.0.0\processed `
    --splits-dir backend\storage\datasets\v1.0.0\splits `
    --config backend\models\model_config.yaml `
    --learning-rate 0.001 `
    --batch-size 32 `
    --epochs 100 `
    --patience 10 `
    --min-delta 0.001 `
    --checkpoint-dir backend\models\checkpoints `
    --device auto `
    --num-workers 4 `
    --log-level INFO

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Training completed!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Best model saved to: backend\models\checkpoints\best_model.pth"
Write-Host "Training history: backend\models\checkpoints\training_history.json"
Write-Host "Training log: training.log"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Evaluate model: python backend\models\evaluate_model.py"
Write-Host "  2. Register model: python backend\models\register_model.py"
Write-Host "  3. Deploy model: python backend\models\inference_service.py"
