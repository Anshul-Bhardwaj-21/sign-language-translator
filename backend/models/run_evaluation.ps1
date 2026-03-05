# PowerShell script to run model evaluation
# Usage: .\run_evaluation.ps1 [checkpoint_path]

param(
    [string]$Checkpoint = "backend/models/checkpoints/best_model.pth"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Sign Language Model Evaluation" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if checkpoint exists
if (-not (Test-Path $Checkpoint)) {
    Write-Host "Error: Checkpoint not found: $Checkpoint" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please train a model first:"
    Write-Host "  .\backend\models\run_training.ps1"
    Write-Host ""
    exit 1
}

Write-Host "Checkpoint: $Checkpoint"
Write-Host ""

# Check if test data exists
$TestSplit = "backend/storage/datasets/v1.0.0/splits/test.txt"
if (-not (Test-Path $TestSplit)) {
    Write-Host "Error: Test split file not found: $TestSplit" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please ensure dataset is properly set up."
    Write-Host ""
    exit 1
}

# Run evaluation
Write-Host "Running evaluation..." -ForegroundColor Yellow
Write-Host ""

python backend/models/evaluate_model.py `
    --checkpoint $Checkpoint `
    --data-dir backend/storage/datasets/v1.0.0/processed `
    --test-split $TestSplit `
    --output-dir backend/models/evaluation `
    --device auto `
    --batch-size 32 `
    --num-workers 4

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "Evaluation complete!" -ForegroundColor Green
    Write-Host "Results saved to: backend/models/evaluation/" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Evaluation failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
