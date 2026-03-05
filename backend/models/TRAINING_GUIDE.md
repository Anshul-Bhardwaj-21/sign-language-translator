# Sign Language Model Training Guide

This guide explains how to train the CNN+LSTM sign language recognition model using the `train_model.py` script.

## Overview

The training script implements a comprehensive training pipeline with:

- **Data Loading**: Loads preprocessed hand landmark sequences from `.npy` files
- **Train/Val/Test Split**: 70/15/15 split as specified in requirements
- **Optimizer**: Adam optimizer with learning rate 0.001
- **Loss Function**: CrossEntropyLoss for multi-class classification
- **Early Stopping**: Patience=10 epochs, min_delta=0.001
- **Checkpointing**: Saves best model based on validation accuracy
- **Logging**: Comprehensive training progress logging
- **CLI Interface**: Flexible command-line configuration

## Requirements

**Validated Requirements:**
- ✅ 30.3: Uses CrossEntropyLoss for classification
- ✅ 30.5: Implements 70/15/15 train/val/test split
- ✅ 30.6: Implements early stopping (patience=10, min_delta=0.001)
- ✅ 30.7: Saves best model checkpoint

## Prerequisites

1. **Preprocessed Dataset**: Run the preprocessing pipeline first
   ```bash
   python backend/storage/datasets/preprocess_dataset.py
   ```

2. **Dataset Splits**: Ensure train/val/test split files exist
   ```
   backend/storage/datasets/v1.0.0/splits/
   ├── train.txt
   ├── val.txt
   └── test.txt
   ```

3. **Python Dependencies**: Install required packages
   ```bash
   pip install torch numpy pyyaml
   ```

## Quick Start

### Basic Training

Train with default configuration (recommended for MVP):

```bash
python backend/models/train_model.py
```

This uses:
- Learning rate: 0.001
- Batch size: 32
- Epochs: 100 (with early stopping)
- Early stopping patience: 10
- Device: Auto-detect (CUDA if available, else CPU)

### Custom Hyperparameters

Train with custom settings:

```bash
python backend/models/train_model.py \
    --learning-rate 0.0005 \
    --batch-size 64 \
    --epochs 150 \
    --patience 15
```

### Resume Training

Resume from a saved checkpoint:

```bash
python backend/models/train_model.py \
    --resume backend/models/checkpoints/checkpoint_epoch_50.pth
```

## Command-Line Arguments

### Data Arguments

- `--data-dir`: Path to processed dataset directory
  - Default: `backend/storage/datasets/v1.0.0/processed`
  
- `--splits-dir`: Path to dataset splits directory
  - Default: `backend/storage/datasets/v1.0.0/splits`

### Model Arguments

- `--config`: Path to model configuration YAML file
  - Default: `backend/models/model_config.yaml`
  
- `--num-classes`: Number of gesture classes (overrides config)
  - Default: Auto-detected from dataset

### Training Arguments

- `--learning-rate`: Learning rate for Adam optimizer
  - Default: `0.001` (Requirement 30.5)
  - Range: `0.0001` to `0.01`
  
- `--batch-size`: Batch size for training
  - Default: `32`
  - Recommended: 16-64 depending on GPU memory
  
- `--epochs`: Maximum number of training epochs
  - Default: `100`
  - Note: Early stopping may terminate training earlier
  
- `--patience`: Early stopping patience (epochs without improvement)
  - Default: `10` (Requirement 30.6)
  
- `--min-delta`: Early stopping minimum improvement threshold
  - Default: `0.001` (Requirement 30.6)

### Checkpoint Arguments

- `--checkpoint-dir`: Directory to save model checkpoints
  - Default: `backend/models/checkpoints`
  
- `--resume`: Path to checkpoint file to resume training from
  - Default: `None` (start from scratch)
  
- `--save-best-only`: Only save checkpoints when validation improves
  - Default: `True`

### Hardware Arguments

- `--device`: Device to train on
  - Choices: `auto`, `cuda`, `cpu`
  - Default: `auto` (uses CUDA if available)
  
- `--num-workers`: Number of data loading workers
  - Default: `4`
  - Increase for faster data loading (if CPU allows)

### Logging Arguments

- `--log-level`: Logging verbosity level
  - Choices: `DEBUG`, `INFO`, `WARNING`, `ERROR`
  - Default: `INFO`

## Training Output

### Console Output

During training, you'll see:

```
2024-01-15 10:30:00 - __main__ - INFO - ============================================================
2024-01-15 10:30:00 - __main__ - INFO - Starting Training
2024-01-15 10:30:00 - __main__ - INFO - ============================================================
2024-01-15 10:30:00 - __main__ - INFO - Device: cuda
2024-01-15 10:30:00 - __main__ - INFO - Number of epochs: 100
2024-01-15 10:30:00 - __main__ - INFO - Training samples: 3500
2024-01-15 10:30:00 - __main__ - INFO - Validation samples: 750
2024-01-15 10:30:00 - __main__ - INFO - Batch size: 32
2024-01-15 10:30:00 - __main__ - INFO - ============================================================

Epoch 1 [10/110] Loss: 3.8542 Acc: 12.50%
Epoch 1 [20/110] Loss: 3.7123 Acc: 15.63%
...

============================================================
Epoch 1/100 Summary:
  Train Loss: 3.5234 | Train Acc: 18.45%
  Val Loss: 3.4123 | Val Acc: 20.12%
  Time: 45.23s
============================================================
```

### Saved Files

The training script creates the following files:

1. **Checkpoints** (in `checkpoint_dir`):
   - `best_model.pth`: Best model based on validation accuracy
   - `checkpoint_epoch_N.pth`: Checkpoint after epoch N (if not save_best_only)

2. **Training History** (in `checkpoint_dir`):
   - `training_history.json`: Complete training metrics history

3. **Logs**:
   - `training.log`: Detailed training log file

### Checkpoint Structure

Each checkpoint contains:

```python
{
    'epoch': 42,
    'model_state_dict': {...},  # Model weights
    'optimizer_state_dict': {...},  # Optimizer state
    'best_val_acc': 87.5,  # Best validation accuracy
    'history': {  # Training history
        'train_loss': [...],
        'train_acc': [...],
        'val_loss': [...],
        'val_acc': [...]
    },
    'model_config': {...}  # Model architecture config
}
```

## Training History

The `training_history.json` file contains:

```json
{
  "train_loss": [3.5234, 3.2145, 2.9876, ...],
  "train_acc": [18.45, 25.67, 32.89, ...],
  "val_loss": [3.4123, 3.1234, 2.8765, ...],
  "val_acc": [20.12, 28.34, 35.67, ...],
  "learning_rates": [0.001, 0.001, 0.001, ...]
}
```

Use this for plotting training curves and analysis.

## Early Stopping

The early stopping mechanism monitors validation accuracy and stops training when:

1. Validation accuracy doesn't improve by at least `min_delta` (0.001)
2. For `patience` consecutive epochs (10)

Example output:

```
Epoch 45/100 Summary:
  Train Loss: 0.4523 | Train Acc: 87.23%
  Val Loss: 0.5234 | Val Acc: 85.67%
  Time: 42.15s
No improvement for 10/10 epochs (best: 86.45% at epoch 35)
Early stopping triggered after 10 epochs without improvement
```

## Best Practices

### 1. Monitor Training Progress

Watch for:
- **Overfitting**: Train accuracy much higher than validation accuracy
  - Solution: Increase dropout, add regularization, or get more data
- **Underfitting**: Both train and validation accuracy are low
  - Solution: Increase model capacity, train longer, or adjust learning rate
- **Slow convergence**: Loss decreasing very slowly
  - Solution: Increase learning rate or adjust architecture

### 2. Hyperparameter Tuning

Start with defaults, then experiment:

```bash
# Baseline (default)
python backend/models/train_model.py

# Higher learning rate for faster convergence
python backend/models/train_model.py --learning-rate 0.002

# Larger batch size for more stable gradients
python backend/models/train_model.py --batch-size 64

# More patience for complex datasets
python backend/models/train_model.py --patience 15
```

### 3. GPU Training

For faster training with GPU:

```bash
# Ensure CUDA is available
python -c "import torch; print(torch.cuda.is_available())"

# Train with GPU
python backend/models/train_model.py --device cuda

# Use larger batch size with GPU
python backend/models/train_model.py --device cuda --batch-size 64
```

### 4. Reproducibility

For reproducible results:
- The script sets random seeds automatically (seed=42)
- Use the same hyperparameters
- Use the same dataset version
- Use the same hardware (CPU vs GPU can give slightly different results)

## Troubleshooting

### Out of Memory (OOM) Error

```
RuntimeError: CUDA out of memory
```

**Solutions:**
- Reduce batch size: `--batch-size 16`
- Use CPU: `--device cpu`
- Close other GPU applications

### Dataset Not Found

```
FileNotFoundError: Sample not found: backend/storage/datasets/...
```

**Solutions:**
- Run preprocessing first: `python backend/storage/datasets/preprocess_dataset.py`
- Check dataset paths in split files
- Verify processed data exists

### Low Accuracy

If model accuracy is below 85% (MVP requirement):

1. **Check data quality**: Ensure preprocessing worked correctly
2. **Increase training time**: Remove early stopping or increase patience
3. **Adjust learning rate**: Try 0.0005 or 0.002
4. **Check class balance**: Ensure all classes have enough samples
5. **Review augmentation**: May need more diverse training data

### Training Too Slow

**Solutions:**
- Use GPU: `--device cuda`
- Increase batch size: `--batch-size 64`
- Increase num_workers: `--num-workers 8`
- Reduce logging frequency (edit script)

## Next Steps

After training:

1. **Evaluate Model**: Run evaluation script to get detailed metrics
   ```bash
   python backend/models/evaluate_model.py \
       --checkpoint backend/models/checkpoints/best_model.pth
   ```

2. **Register Model**: Add to model registry for deployment
   ```bash
   python backend/models/register_model.py \
       --checkpoint backend/models/checkpoints/best_model.pth \
       --version 1.0.0
   ```

3. **Deploy Model**: Use in inference service
   ```bash
   python backend/models/inference_service.py \
       --model-path backend/models/checkpoints/best_model.pth
   ```

## Example Training Session

Complete example from start to finish:

```bash
# 1. Preprocess dataset (if not done)
python backend/storage/datasets/preprocess_dataset.py

# 2. Train model with default settings
python backend/models/train_model.py

# 3. Monitor training (in another terminal)
tail -f training.log

# 4. After training completes, check best model
ls -lh backend/models/checkpoints/best_model.pth

# 5. View training history
cat backend/models/checkpoints/training_history.json | python -m json.tool
```

## Configuration File

The script uses `model_config.yaml` for default settings. You can modify this file to change defaults without using command-line arguments.

Key sections:
- `model`: Architecture configuration
- `training`: Training hyperparameters
- `data`: Dataset paths and augmentation
- `evaluation`: Metrics and requirements

See `model_config.yaml` for full configuration options.

## Support

For issues or questions:
1. Check this guide first
2. Review training logs: `training.log`
3. Check model configuration: `model_config.yaml`
4. Verify dataset: `backend/storage/datasets/README.md`

## References

- Requirements: `.kiro/specs/advanced-meeting-features/requirements.md`
- Design: `.kiro/specs/advanced-meeting-features/design.md`
- Model Architecture: `backend/models/sign_language_model.py`
- Preprocessing: `backend/storage/datasets/PREPROCESSING_GUIDE.md`
