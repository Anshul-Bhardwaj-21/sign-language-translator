#!/bin/bash
# Script to run model evaluation
# Usage: ./run_evaluation.sh [checkpoint_path]

set -e

echo "=========================================="
echo "Sign Language Model Evaluation"
echo "=========================================="
echo ""

# Default checkpoint path
CHECKPOINT="${1:-backend/models/checkpoints/best_model.pth}"

# Check if checkpoint exists
if [ ! -f "$CHECKPOINT" ]; then
    echo "Error: Checkpoint not found: $CHECKPOINT"
    echo ""
    echo "Please train a model first:"
    echo "  ./backend/models/run_training.sh"
    echo ""
    exit 1
fi

echo "Checkpoint: $CHECKPOINT"
echo ""

# Check if test data exists
TEST_SPLIT="backend/storage/datasets/v1.0.0/splits/test.txt"
if [ ! -f "$TEST_SPLIT" ]; then
    echo "Error: Test split file not found: $TEST_SPLIT"
    echo ""
    echo "Please ensure dataset is properly set up."
    echo ""
    exit 1
fi

# Run evaluation
echo "Running evaluation..."
echo ""

python backend/models/evaluate_model.py \
    --checkpoint "$CHECKPOINT" \
    --data-dir backend/storage/datasets/v1.0.0/processed \
    --test-split "$TEST_SPLIT" \
    --output-dir backend/models/evaluation \
    --device auto \
    --batch-size 32 \
    --num-workers 4

echo ""
echo "=========================================="
echo "Evaluation complete!"
echo "Results saved to: backend/models/evaluation/"
echo "=========================================="
