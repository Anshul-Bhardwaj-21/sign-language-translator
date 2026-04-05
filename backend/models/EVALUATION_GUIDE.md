# Model Evaluation Guide

This guide explains how to evaluate trained sign language recognition models using the `evaluate_model.py` script.

## Overview

The evaluation script provides comprehensive model assessment including:

1. **Overall test accuracy** - Percentage of correctly classified samples
2. **Per-class metrics** - Precision, recall, and F1 scores for each gesture class
3. **Confusion matrix** - Visual representation of prediction patterns
4. **Top 5 confused pairs** - Most frequently misclassified gesture combinations
5. **Inference latency** - Average, P50, P95, and P99 latency measurements
6. **Model size** - Size in megabytes and parameter count

## Requirements

The evaluation script validates against these requirements:

- **Requirement 30.9**: Reports per-class precision, recall, and F1 scores
- **Requirement 30.10**: MVP accuracy target ≥85%
- **Requirement 31.1**: Calculates overall accuracy on held-out test set
- **Requirement 31.2**: Calculates per-class F1 scores to handle class imbalance
- **Requirement 31.3**: Generates confusion matrix visualization
- **Requirement 31.4**: Identifies top 5 most confused gesture pairs
- **Requirement 31.5**: Calculates average inference latency on test samples
- **Requirement 31.8**: Saves all evaluation metrics in JSON format

## Prerequisites

1. **Trained model checkpoint** - Must have a trained model saved in `backend/models/checkpoints/`
2. **Test dataset** - Preprocessed test data in `backend/storage/datasets/v1.0.0/processed/`
3. **Test split file** - List of test samples in `backend/storage/datasets/v1.0.0/splits/test.txt`

## Basic Usage

### Evaluate Best Model

```bash
# Evaluate the best model checkpoint (default)
python backend/models/evaluate_model.py
```

This will:
- Load `backend/models/checkpoints/best_model.pth`
- Run inference on the test set
- Calculate all metrics
- Save results to `backend/models/evaluation/`

### Evaluate Specific Checkpoint

```bash
# Evaluate a specific epoch checkpoint
python backend/models/evaluate_model.py --checkpoint backend/models/checkpoints/checkpoint_epoch_50.pth
```

### Custom Output Directory

```bash
# Save results to a custom directory
python backend/models/evaluate_model.py --output-dir my_evaluation_results
```

## Command Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--checkpoint` | `backend/models/checkpoints/best_model.pth` | Path to model checkpoint |
| `--data-dir` | `backend/storage/datasets/v1.0.0/processed` | Path to processed dataset |
| `--test-split` | `backend/storage/datasets/v1.0.0/splits/test.txt` | Path to test split file |
| `--output-dir` | `backend/models/evaluation` | Directory to save results |
| `--device` | `auto` | Device to use (`auto`, `cuda`, or `cpu`) |
| `--batch-size` | `32` | Batch size for evaluation |
| `--num-workers` | `4` | Number of data loading workers |

## Output Files

The evaluation script generates the following files in the output directory:

### 1. Evaluation Metrics JSON

**File**: `evaluation_metrics_YYYYMMDD_HHMMSS.json`

Contains all calculated metrics in JSON format:

```json
{
  "overall_accuracy": 0.87,
  "per_class_metrics": {
    "hello": {
      "precision": 0.92,
      "recall": 0.89,
      "f1_score": 0.90,
      "support": 45
    },
    ...
  },
  "macro_avg": {
    "precision": 0.88,
    "recall": 0.86,
    "f1_score": 0.87
  },
  "weighted_avg": {
    "precision": 0.89,
    "recall": 0.87,
    "f1_score": 0.88
  },
  "inference_latency_ms": {
    "mean": 15.3,
    "std": 2.1,
    "min": 12.5,
    "max": 25.8,
    "p50": 14.9,
    "p95": 19.2,
    "p99": 22.1
  },
  "model_size": {
    "size_mb": 48.5,
    "total_parameters": 12750000,
    "trainable_parameters": 12750000
  },
  "confusion_matrix": [[...], ...],
  "confusion_matrix_normalized": [[...], ...],
  "top_5_confused_pairs": [
    {
      "true_class": "hello",
      "predicted_class": "goodbye",
      "count": 5,
      "percentage": 11.1
    },
    ...
  ],
  "metadata": {
    "evaluation_date": "2024-03-04T15:30:00",
    "num_test_samples": 450,
    "num_classes": 10,
    "class_names": ["hello", "goodbye", ...],
    "device": "cuda"
  }
}
```

### 2. Confusion Matrix Visualization

**File**: `confusion_matrix_YYYYMMDD_HHMMSS.png`

A heatmap visualization showing:
- Normalized confusion matrix (values 0-1)
- True classes on Y-axis
- Predicted classes on X-axis
- Color intensity indicates prediction frequency

## Interpreting Results

### Overall Accuracy

- **Target (MVP)**: ≥85%
- **Target (Production)**: ≥95%

If accuracy is below target, consider:
- Collecting more training data
- Adjusting model architecture
- Tuning hyperparameters
- Improving data augmentation

### Per-Class Metrics

**Precision**: Of all predictions for this class, how many were correct?
- Low precision = Many false positives

**Recall**: Of all actual instances of this class, how many were detected?
- Low recall = Many false negatives

**F1 Score**: Harmonic mean of precision and recall
- Balanced metric for overall class performance

### Confusion Matrix

Diagonal elements (top-left to bottom-right) represent correct predictions.
Off-diagonal elements represent misclassifications.

Look for:
- **Dark diagonal**: Good performance
- **Bright off-diagonal cells**: Frequently confused pairs
- **Bright rows**: Classes with low recall (missed detections)
- **Bright columns**: Classes with low precision (false alarms)

### Top 5 Confused Pairs

Identifies the most problematic gesture combinations. Use this to:
- Understand which gestures are visually similar
- Collect more distinguishing training samples
- Consider merging very similar gestures
- Add targeted data augmentation

### Inference Latency

- **Mean**: Average latency across all samples
- **P95**: 95% of samples complete within this time
- **P99**: 99% of samples complete within this time

**Target**: P95 ≤ 200ms (Requirement 33.4)

If latency is too high:
- Use GPU acceleration
- Reduce model size
- Optimize preprocessing
- Use batch inference

## Example Workflow

### 1. Train Model

```bash
python backend/models/train_model.py --epochs 100 --batch-size 32
```

### 2. Evaluate Model

```bash
python backend/models/evaluate_model.py
```

### 3. Review Results

Check the console output for summary:

```
============================================================
EVALUATION SUMMARY
============================================================
Overall Accuracy: 87.50%
Macro F1 Score: 0.8723
Weighted F1 Score: 0.8745
Average Inference Latency: 15.30 ms
P95 Inference Latency: 19.20 ms
Model Size: 48.50 MB
============================================================
✓ Model meets MVP accuracy requirement (≥85%)
✓ Model meets inference latency requirement (P95 ≤200ms)
============================================================
```

### 4. Analyze Confusion Matrix

Open the generated PNG file to visualize prediction patterns.

### 5. Investigate Confused Pairs

Review the top 5 confused pairs in the JSON file or console output:

```
Top 5 Most Confused Gesture Pairs:
  1. hello -> goodbye: 5 samples (11.1%)
  2. yes -> no: 4 samples (9.5%)
  3. thank_you -> please: 3 samples (7.2%)
  4. help -> sorry: 3 samples (6.8%)
  5. understand -> help: 2 samples (5.1%)
```

### 6. Iterate

Based on results:
- If accuracy is low: Retrain with more data or different hyperparameters
- If specific classes perform poorly: Collect more samples for those classes
- If latency is high: Optimize model or use GPU
- If confused pairs are problematic: Add targeted augmentation

## Testing the Evaluation Script

Run the test script to verify functionality:

```bash
python backend/models/test_evaluation.py
```

This creates a mock model and dataset to test all evaluation features.

## Troubleshooting

### Error: Checkpoint not found

```
Checkpoint not found: backend/models/checkpoints/best_model.pth
Please train a model first using train_model.py
```

**Solution**: Train a model first:
```bash
python backend/models/train_model.py
```

### Error: Test split file not found

```
FileNotFoundError: backend/storage/datasets/v1.0.0/splits/test.txt
```

**Solution**: Ensure dataset is properly set up with train/val/test splits.

### Low Accuracy

If model accuracy is below target:

1. **Check training accuracy**: If training accuracy is also low, model is underfitting
   - Increase model capacity
   - Train for more epochs
   - Reduce regularization

2. **Check training accuracy**: If training accuracy is high but test is low, model is overfitting
   - Add more training data
   - Increase regularization (dropout)
   - Use data augmentation

3. **Check data quality**: Ensure test data is properly preprocessed and labeled

### High Latency

If inference latency exceeds 200ms:

1. **Use GPU**: Add `--device cuda` if GPU is available
2. **Reduce batch size**: Try `--batch-size 1` for single-sample latency
3. **Optimize model**: Consider model pruning or quantization
4. **Profile code**: Identify bottlenecks in preprocessing or inference

## Integration with MLflow

The evaluation metrics can be logged to MLflow for experiment tracking:

```python
import mlflow

# Load evaluation results
with open('evaluation_metrics.json', 'r') as f:
    metrics = json.load(f)

# Log to MLflow
with mlflow.start_run():
    mlflow.log_metric("test_accuracy", metrics['overall_accuracy'])
    mlflow.log_metric("test_f1_macro", metrics['macro_avg']['f1_score'])
    mlflow.log_metric("inference_latency_p95", metrics['inference_latency_ms']['p95'])
    mlflow.log_artifact("confusion_matrix.png")
```

## Next Steps

After evaluation:

1. **If model meets requirements**: Deploy to inference service
2. **If model needs improvement**: Iterate on training
3. **Document results**: Add metrics to model registry
4. **Compare models**: Evaluate multiple checkpoints to find best
5. **Production testing**: Test on real meeting data

## Related Documentation

- [Training Guide](TRAINING_GUIDE.md) - How to train models
- [Model Architecture](MODEL_ARCHITECTURE.md) - Model design details
- [Preprocessing Guide](../storage/datasets/PREPROCESSING_GUIDE.md) - Data preprocessing
- [Design Document](../../.kiro/specs/advanced-meeting-features/design.md) - System design

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the requirements document
3. Examine the evaluation script source code
4. Contact the ML engineering team
