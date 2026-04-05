# Model Registry Guide

## Overview

The Model Registry module provides a comprehensive system for managing trained sign language recognition models using MLflow Model Registry. It implements Layer 4 of the 7-layer ML architecture.

## Features

- **Model Registration**: Register trained models with automatic semantic versioning
- **Metadata Management**: Store and retrieve model metadata (accuracy, training date, performance metrics)
- **Deployment Tagging**: Tag models with deployment status (production, staging, experimental, archived)
- **Version Control**: Load models by version number or deployment stage
- **Rollback Support**: Quickly rollback to previous model versions
- **Model Comparison**: Compare performance metrics between model versions

## Requirements Implemented

- **32.1**: Semantic version numbers assigned automatically to all trained models
- **32.2**: Model metadata storage (version, training date, input shape, output labels, performance metrics)
- **32.3**: Deployment status tagging (production, staging, experimental, archived)
- **32.9**: API endpoints for retrieving models by version or tag

## Installation

The model registry requires MLflow:

```bash
pip install mlflow>=2.9.0
```

## Quick Start

### 1. Initialize the Registry

```python
from models.model_registry import ModelRegistry

# Initialize with default tracking URI from config
registry = ModelRegistry()

# Or specify tracking URI explicitly
registry = ModelRegistry(tracking_uri="http://localhost:5000")
```

### 2. Register a Model

After training a model and logging it to MLflow:

```python
# Register model from MLflow run
model_version = registry.register_model(
    model_uri="runs:/abc123def456/model",
    model_name="sign-language-asl",
    metadata={
        "accuracy": 0.87,
        "f1_score": 0.85,
        "precision": 0.86,
        "recall": 0.84,
        "training_date": "2024-01-15",
        "input_shape": "(60, 126)",
        "num_classes": 25,
        "dataset_version": "v1.0.0"
    },
    description="CNN+LSTM baseline model for ASL recognition"
)

print(f"Registered model version: {model_version.version}")
```

### 3. Tag Model for Deployment

```python
# Transition to staging for testing
registry.transition_model_stage(
    model_name="sign-language-asl",
    version=1,
    stage="Staging"
)

# After validation, promote to production
registry.transition_model_stage(
    model_name="sign-language-asl",
    version=1,
    stage="Production",
    archive_existing_versions=True  # Archive previous production models
)
```

### 4. Load Model for Inference

```python
# Load production model
model = registry.load_model_by_stage(
    model_name="sign-language-asl",
    stage="Production",
    device="cuda"  # or "cpu"
)

# Or load specific version
model = registry.load_model_by_version(
    model_name="sign-language-asl",
    version=3,
    device="cuda"
)
```

## Common Workflows

### Training and Registration Workflow

```python
import mlflow
from models.model_registry import ModelRegistry

# 1. Train model with MLflow tracking
with mlflow.start_run() as run:
    # Train your model
    model = train_sign_language_model()
    
    # Log model and metrics
    mlflow.pytorch.log_model(model, "model")
    mlflow.log_metrics({
        "accuracy": 0.87,
        "f1_score": 0.85
    })
    
    run_id = run.info.run_id

# 2. Register model
registry = ModelRegistry()
model_version = registry.register_model(
    model_uri=f"runs:/{run_id}/model",
    model_name="sign-language-asl",
    metadata={
        "accuracy": 0.87,
        "f1_score": 0.85,
        "training_date": datetime.now().isoformat()
    }
)

# 3. Tag for staging
registry.transition_model_stage(
    model_name="sign-language-asl",
    version=int(model_version.version),
    stage="Staging"
)
```

### Model Deployment Workflow

```python
from models.model_registry import ModelRegistry

registry = ModelRegistry()

# 1. Get staging model for validation
staging_model = registry.load_model_by_stage(
    model_name="sign-language-asl",
    stage="Staging"
)

# 2. Validate model performance
validation_accuracy = validate_model(staging_model)

# 3. If validation passes, promote to production
if validation_accuracy >= 0.85:
    staging_version = registry.get_latest_model_version(
        model_name="sign-language-asl",
        stage="Staging"
    )
    
    registry.transition_model_stage(
        model_name="sign-language-asl",
        version=int(staging_version.version),
        stage="Production",
        archive_existing_versions=True
    )
    
    print(f"Deployed version {staging_version.version} to production")
```

### Model Rollback Workflow

```python
from models.model_registry import ModelRegistry

registry = ModelRegistry()

# If production model has issues, rollback to previous version
registry.rollback_to_version(
    model_name="sign-language-asl",
    version=2,  # Previous stable version
    target_stage="Production"
)

print("Rolled back to version 2")
```

### Model Comparison Workflow

```python
from models.model_registry import ModelRegistry

registry = ModelRegistry()

# Compare two model versions
comparison = registry.compare_model_versions(
    model_name="sign-language-asl",
    version1=2,
    version2=3
)

# Print comparison results
print(f"Model: {comparison['model_name']}")
print(f"\nVersion {comparison['version1']} vs Version {comparison['version2']}")
print("\nMetric Comparison:")

for metric, values in comparison['metric_comparison'].items():
    print(f"  {metric}:")
    print(f"    v{comparison['version1']}: {values['version1']:.4f}")
    print(f"    v{comparison['version2']}: {values['version2']:.4f}")
    print(f"    Difference: {values['difference']:+.4f}")
    print(f"    Improvement: {values['improvement']}")
```

## API Reference

### ModelRegistry Class

#### `__init__(tracking_uri=None, config_path="backend/mlflow_config.yaml")`

Initialize the model registry.

**Parameters:**
- `tracking_uri` (str, optional): MLflow tracking server URI
- `config_path` (str): Path to MLflow configuration file

#### `register_model(model_uri, model_name, metadata=None, description=None, tags=None)`

Register a trained model in the registry.

**Parameters:**
- `model_uri` (str): URI of the model (e.g., "runs:/run_id/model")
- `model_name` (str): Name of the registered model
- `metadata` (dict, optional): Model metadata (accuracy, f1_score, etc.)
- `description` (str, optional): Model version description
- `tags` (dict, optional): Additional tags

**Returns:**
- `ModelVersion`: Registered model version object

#### `transition_model_stage(model_name, version, stage, archive_existing_versions=False)`

Transition a model version to a new deployment stage.

**Parameters:**
- `model_name` (str): Name of the registered model
- `version` (int): Model version number
- `stage` (str): Target stage ("None", "Staging", "Production", "Archived")
- `archive_existing_versions` (bool): Archive existing versions in target stage

#### `load_model_by_version(model_name, version, device="cpu")`

Load a model by version number.

**Parameters:**
- `model_name` (str): Name of the registered model
- `version` (int): Model version number
- `device` (str): Device to load model on ("cpu" or "cuda")

**Returns:**
- `torch.nn.Module`: Loaded PyTorch model

#### `load_model_by_stage(model_name, stage="Production", device="cpu")`

Load a model by deployment stage.

**Parameters:**
- `model_name` (str): Name of the registered model
- `stage` (str): Deployment stage
- `device` (str): Device to load model on

**Returns:**
- `torch.nn.Module`: Loaded PyTorch model

#### `get_model_metadata(model_name, version)`

Get metadata for a model version.

**Parameters:**
- `model_name` (str): Name of the registered model
- `version` (int): Model version number

**Returns:**
- `dict`: Model metadata dictionary

#### `rollback_to_version(model_name, version, target_stage="Production")`

Rollback to a previous model version.

**Parameters:**
- `model_name` (str): Name of the registered model
- `version` (int): Version to rollback to
- `target_stage` (str): Target deployment stage

#### `compare_model_versions(model_name, version1, version2)`

Compare two model versions.

**Parameters:**
- `model_name` (str): Name of the registered model
- `version1` (int): First version number
- `version2` (int): Second version number

**Returns:**
- `dict`: Comparison results with metric differences

## CLI Usage

The model registry includes a CLI for common operations:

```bash
# List all versions of a model
python backend/models/model_registry.py --list sign-language-asl

# Get metadata for a specific version
python backend/models/model_registry.py --metadata sign-language-asl 3

# Get production version
python backend/models/model_registry.py --production sign-language-asl
```

## Integration with Training Script

The model registry integrates seamlessly with the training script:

```python
# In train_model.py
import mlflow
from models.model_registry import ModelRegistry

# After training completes
with mlflow.start_run() as run:
    # ... training code ...
    
    # Log model
    mlflow.pytorch.log_model(model, "model")
    
    # Register model
    registry = ModelRegistry()
    model_version = registry.register_model(
        model_uri=f"runs:/{run.info.run_id}/model",
        model_name="sign-language-asl",
        metadata={
            "accuracy": test_accuracy,
            "f1_score": test_f1,
            "training_date": datetime.now().isoformat(),
            "dataset_version": dataset_version
        }
    )
    
    # Tag as experimental initially
    registry.tag_model(
        model_name="sign-language-asl",
        version=int(model_version.version),
        tag="experimental"
    )
```

## Best Practices

### 1. Metadata Standards

Always include these metadata fields when registering models:

```python
metadata = {
    "accuracy": 0.87,           # Test set accuracy
    "f1_score": 0.85,           # F1 score
    "precision": 0.86,          # Precision
    "recall": 0.84,             # Recall
    "training_date": "2024-01-15",  # ISO format date
    "input_shape": "(60, 126)", # Model input shape
    "num_classes": 25,          # Number of output classes
    "dataset_version": "v1.0.0", # Dataset version used
    "dataset_hash": "abc123",   # Dataset hash for reproducibility
    "model_size_mb": 50.2,      # Model size in MB
    "inference_latency_ms": 180 # Average inference latency
}
```

### 2. Deployment Stages

Follow this progression for model deployment:

1. **None**: Newly registered models (default)
2. **Staging**: Models being tested and validated
3. **Production**: Models deployed to production
4. **Archived**: Old models kept for reference

### 3. Version Naming

MLflow automatically assigns incremental version numbers (1, 2, 3, ...). Use tags for additional context:

```python
registry.tag_model(model_name, version, "baseline", "true")
registry.tag_model(model_name, version, "experiment_id", "exp-123")
```

### 4. Rollback Strategy

Always test rollback procedures:

```python
# Before deploying new version, note current production version
current_prod = registry.get_production_model_version("sign-language-asl")
print(f"Current production: v{current_prod.version}")

# Deploy new version
registry.transition_model_stage("sign-language-asl", 5, "Production")

# If issues occur, rollback
registry.rollback_to_version("sign-language-asl", int(current_prod.version))
```

## Troubleshooting

### Issue: Model not found

```python
# Check if model is registered
versions = registry.list_model_versions("sign-language-asl")
if not versions:
    print("Model not registered yet")
```

### Issue: No production model

```python
# Check production model
prod_version = registry.get_production_model_version("sign-language-asl")
if prod_version is None:
    print("No production model found. Transition a model to Production stage.")
```

### Issue: Version conflicts

```python
# List all versions and their stages
versions = registry.list_model_versions("sign-language-asl")
for v in versions:
    print(f"Version {v.version}: {v.current_stage}")
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest backend/models/test_model_registry.py -v

# Run specific test
pytest backend/models/test_model_registry.py::TestModelRegistry::test_register_model -v
```

## Related Documentation

- [MLflow Setup Guide](../MLFLOW_SETUP_GUIDE.md)
- [Training Guide](TRAINING_GUIDE.md)
- [Evaluation Guide](EVALUATION_GUIDE.md)
- [MLflow Model Registry Documentation](https://mlflow.org/docs/latest/model-registry.html)

## Phase

MVP (Phase 1)

## Author

AI-Powered Meeting Platform Team
