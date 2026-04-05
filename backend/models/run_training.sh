#!/bin/bash
# Quick start script for training sign language model
# Usage: ./backend/models/run_training.sh

set -e

echo "=========================================="
echo "Sign Language Model Training"
echo "=========================================="
echo ""

# Check if preprocessed data exists
if [ ! -d "backend/storage/datasets/v1.0.0/processed" ]; then
    echo "Error: Preprocessed dataset not found!"
    echo "Please run preprocessing first:"
    echo "  python backend/storage/datasets/preprocess_dataset.py"
    exit 1
fi

# Check if split files exist
if [ ! -f "backend/storage/datasets/v1.0.0/splits/train.txt" ]; then
    echo "Error: Dataset split files not found!"
    echo "Please create splits first:"
    echo "  python backend/storage/datasets/create_splits.py"
    exit 1
fi

# Create checkpoints directory
mkdir -p backend/models/checkpoints

# Run training with default configuration
echo "Starting training with default configuration..."
echo "  - Learning rate: 0.001"
echo "  - Batch size: 32"
echo "  - Max epochs: 100"
echo "  - Early stopping: patience=10, min_delta=0.001"
echo ""

python backend/models/train_model.py \
    --data-dir backend/storage/datasets/v1.0.0/processed \
    --splits-dir backend/storage/datasets/v1.0.0/splits \
    --config backend/models/model_config.yaml \
    --learning-rate 0.001 \
    --batch-size 32 \
    --epochs 100 \
    --patience 10 \
    --min-delta 0.001 \
    --checkpoint-dir backend/models/checkpoints \
    --device auto \
    --num-workers 4 \
    --log-level INFO

echo ""
echo "=========================================="
echo "Training completed!"
echo "=========================================="
echo ""
echo "Best model saved to: backend/models/checkpoints/best_model.pth"
echo "Training history: backend/models/checkpoints/training_history.json"
echo "Training log: training.log"
echo ""
echo "Next steps:"
echo "  1. Evaluate model: python backend/models/evaluate_model.py"
echo "  2. Register model: python backend/models/register_model.py"
echo "  3. Deploy model: python backend/models/inference_service.py"
