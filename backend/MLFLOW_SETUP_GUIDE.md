# MLflow Experiment Tracking Setup Guide

This guide explains how to setup and use MLflow for tracking sign language model training experiments.

**Requirements**: 51.9 - Setup MLflow experiment tracking (Layer 7 - Production ML)

## Overview

MLflow is configured with:
- **Backend Store**: PostgreSQL database for experiment metadata
- **Artifact Store**: Local filesystem (or S3/GCS for production) for model files and plots
- **Tracking Server**: Web UI for viewing experiments and comparing results
- **Model Registry**: Versioned storage for trained models

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   MLflow Tracking Server                 │
│                    (Port 5000)                           │
└─────────────────────────────────────────────────────────┘
                    │                    │
                    │                    │
        ┌───────────▼──────────┐  ┌─────▼──────────┐
        │  PostgreSQL          │  │  Artifact Store │
        │  Backend Store       │  │  (Local/S3/GCS) │
        │  - Experiments       │  │  - Models       │
        │  - Runs              │  │  - Plots        │
        │  - Metrics           │  │  - Artifacts    │
        │  - Parameters        │  │                 │
        └──────────────────────┘  └─────────────────┘
```

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# Start all services including MLflow
docker-compose up -d

# Access MLflow UI
open http://localhost:5000
```

### Option 2: Local Development

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Initialize MLflow experiments
python backend/setup_mlflow.py --init-only

# 3. Start MLflow server
python backend/setup_mlflow.py --start-server

# Or use the convenience scripts:
# Linux/Mac:
bash backend/start_mlflow.sh

# Windows:
powershell backend/start_mlflow.ps1
```

## Configuration

MLflow configuration is defined in `backend/mlflow_config.yaml`:

```yaml
server:
  tracking_uri: "http://localhost:5000"
  backend_store_uri: "postgresql://meeting_user:meeting_pass@localhost:5432/meeting_db"
  artifact_root: "./backend/storage/mlflow-artifacts"
  host: "0.0.0.0"
  port: 5000
  workers: 2

experiments:
  sign_language_asl_baseline:
    name: "sign-language-asl-baseline"
    description: "CNN+LSTM baseline model for ASL recognition"
    tags:
      project: "advanced-meeting-features"
      model_type: "cnn-lstm"
      sign_language: "ASL"
      phase: "mvp"
```

### Environment Variables

For production deployment, configure these environment variables:

```bash
# MLflow Server
export MLFLOW_TRACKING_URI="http://mlflow-server:5000"
export MLFLOW_BACKEND_STORE_URI="postgresql://user:pass@host:5432/db"
export MLFLOW_ARTIFACT_ROOT="s3://my-bucket/mlflow-artifacts"

# AWS S3 (if using S3 artifact store)
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Google Cloud Storage (if using GCS artifact store)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

## Usage in Training Scripts

### Basic Usage

```python
import mlflow
import mlflow.pytorch

# Set tracking URI
mlflow.set_tracking_uri("http://localhost:5000")

# Set experiment
mlflow.set_experiment("sign-language-asl-baseline")

# Start a run
with mlflow.start_run(run_name="cnn-lstm-baseline"):
    # Log parameters (Requirement 51.1)
    mlflow.log_params({
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 100,
        "optimizer": "Adam",
        "model_architecture": "CNN+LSTM"
    })
    
    # Log dataset version (Requirement 51.2)
    mlflow.log_param("dataset_hash", "abc123...")
    mlflow.log_param("dataset_version", "v1.0.0")
    
    # Log random seed (Requirement 51.3)
    mlflow.log_param("random_seed", 42)
    
    # Training loop
    for epoch in range(num_epochs):
        train_loss, train_acc = train_epoch()
        val_loss, val_acc = validate()
        
        # Log metrics (Requirement 51.4)
        mlflow.log_metrics({
            "train_loss": train_loss,
            "train_accuracy": train_acc,
            "val_loss": val_loss,
            "val_accuracy": val_acc
        }, step=epoch)
    
    # Log final test metrics
    test_metrics = evaluate_model()
    mlflow.log_metrics({
        "test_accuracy": test_metrics['accuracy'],
        "test_precision": test_metrics['precision'],
        "test_recall": test_metrics['recall'],
        "test_f1_score": test_metrics['f1_score']
    })
    
    # Log artifacts (Requirement 51.13)
    mlflow.log_artifact("confusion_matrix.png")
    mlflow.log_artifact("training_curves.png")
    
    # Log model
    mlflow.pytorch.log_model(model, "model")
```

### Advanced Usage with Model Registry

```python
import mlflow
from mlflow.tracking import MlflowClient

# Train model
with mlflow.start_run() as run:
    # ... training code ...
    mlflow.pytorch.log_model(model, "model")
    run_id = run.info.run_id

# Register model (Requirement 32.1)
model_uri = f"runs:/{run_id}/model"
model_version = mlflow.register_model(
    model_uri=model_uri,
    name="sign-language-asl"
)

# Add metadata (Requirement 32.2, 32.3)
client = MlflowClient()
client.update_model_version(
    name="sign-language-asl",
    version=model_version.version,
    description="CNN+LSTM baseline model trained on v1.0.0 dataset"
)

# Tag for deployment (Requirement 32.9)
client.set_model_version_tag(
    name="sign-language-asl",
    version=model_version.version,
    key="deployment_status",
    value="staging"
)

# Transition to production
client.transition_model_version_stage(
    name="sign-language-asl",
    version=model_version.version,
    stage="Production"
)
```

### Loading Models from Registry

```python
import mlflow.pytorch

# Load latest production model
model = mlflow.pytorch.load_model("models:/sign-language-asl/Production")

# Load specific version
model = mlflow.pytorch.load_model("models:/sign-language-asl/3")
```

## Experiments

### sign-language-asl-baseline

**Purpose**: Track CNN+LSTM baseline model training for American Sign Language recognition (MVP)

**Key Metrics**:
- `test_accuracy`: Must be ≥ 0.85 for MVP (Requirement 30.10)
- `test_f1_score`: Overall F1 score
- `test_precision`: Precision across all classes
- `test_recall`: Recall across all classes

**Required Parameters**:
- `learning_rate`: Adam optimizer learning rate
- `batch_size`: Training batch size
- `epochs`: Number of training epochs
- `dataset_hash`: SHA256 hash of dataset for reproducibility
- `dataset_version`: Semantic version of dataset (e.g., "v1.0.0")
- `random_seed`: Random seed for reproducibility
- `num_classes`: Number of gesture classes (20-50 for MVP)

**Required Artifacts**:
- `model`: PyTorch model checkpoint
- `confusion_matrix.png`: Confusion matrix visualization
- `training_curves.png`: Training/validation loss and accuracy curves
- `model_config.yaml`: Model architecture configuration
- `training_config.yaml`: Training hyperparameters

## Model Registry

### sign-language-asl

**Description**: American Sign Language recognition model for real-time video conferencing

**Stages**:
- `None`: Newly registered models
- `Staging`: Models being tested before production
- `Production`: Models deployed to production inference service
- `Archived`: Old models kept for reference

**Deployment Workflow**:

1. **Train and Register**:
   ```python
   # Train model and log to MLflow
   with mlflow.start_run():
       # ... training ...
       mlflow.pytorch.log_model(model, "model")
   
   # Register model
   mlflow.register_model(model_uri, "sign-language-asl")
   ```

2. **Test in Staging**:
   ```python
   # Transition to staging
   client.transition_model_version_stage(
       name="sign-language-asl",
       version="3",
       stage="Staging"
   )
   
   # Load and test
   model = mlflow.pytorch.load_model("models:/sign-language-asl/Staging")
   # ... run tests ...
   ```

3. **Deploy to Production**:
   ```python
   # Transition to production
   client.transition_model_version_stage(
       name="sign-language-asl",
       version="3",
       stage="Production"
   )
   ```

4. **Rollback if Needed**:
   ```python
   # Revert to previous version
   client.transition_model_version_stage(
       name="sign-language-asl",
       version="2",
       stage="Production"
   )
   ```

## MLflow UI

Access the MLflow UI at `http://localhost:5000`

### Key Features

1. **Experiments View**: Compare runs side-by-side
2. **Run Details**: View parameters, metrics, and artifacts
3. **Model Registry**: Manage model versions and deployments
4. **Metrics Visualization**: Plot training curves and compare experiments
5. **Artifact Browser**: Download models, plots, and other artifacts

### Comparing Experiments

1. Navigate to experiment: `sign-language-asl-baseline`
2. Select multiple runs using checkboxes
3. Click "Compare" button
4. View side-by-side comparison of parameters and metrics
5. Generate plots to visualize metric differences

## Database Schema

MLflow creates these tables in PostgreSQL:

```sql
-- Experiments
CREATE TABLE experiments (
    experiment_id INTEGER PRIMARY KEY,
    name VARCHAR(256) NOT NULL UNIQUE,
    artifact_location VARCHAR(256),
    lifecycle_stage VARCHAR(32)
);

-- Runs
CREATE TABLE runs (
    run_uuid VARCHAR(32) PRIMARY KEY,
    name VARCHAR(250),
    source_type VARCHAR(20),
    source_name VARCHAR(500),
    entry_point_name VARCHAR(50),
    user_id VARCHAR(256),
    status VARCHAR(20),
    start_time BIGINT,
    end_time BIGINT,
    source_version VARCHAR(50),
    lifecycle_stage VARCHAR(20),
    artifact_uri VARCHAR(200),
    experiment_id INTEGER REFERENCES experiments(experiment_id)
);

-- Metrics
CREATE TABLE metrics (
    key VARCHAR(250) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    timestamp BIGINT NOT NULL,
    run_uuid VARCHAR(32) REFERENCES runs(run_uuid),
    step BIGINT DEFAULT 0 NOT NULL,
    is_nan BOOLEAN DEFAULT FALSE NOT NULL
);

-- Parameters
CREATE TABLE params (
    key VARCHAR(250) NOT NULL,
    value VARCHAR(500) NOT NULL,
    run_uuid VARCHAR(32) REFERENCES runs(run_uuid)
);

-- Tags
CREATE TABLE tags (
    key VARCHAR(250) NOT NULL,
    value VARCHAR(5000),
    run_uuid VARCHAR(32) REFERENCES runs(run_uuid)
);

-- Model Registry
CREATE TABLE registered_models (
    name VARCHAR(256) PRIMARY KEY,
    creation_time BIGINT,
    last_updated_time BIGINT,
    description VARCHAR(5000)
);

CREATE TABLE model_versions (
    name VARCHAR(256) REFERENCES registered_models(name),
    version INTEGER NOT NULL,
    creation_time BIGINT,
    last_updated_time BIGINT,
    description VARCHAR(5000),
    user_id VARCHAR(256),
    current_stage VARCHAR(20),
    source VARCHAR(500),
    run_id VARCHAR(32),
    status VARCHAR(20),
    status_message VARCHAR(500),
    PRIMARY KEY (name, version)
);
```

## Troubleshooting

### MLflow Server Won't Start

**Problem**: Server fails to start with database connection error

**Solution**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check database credentials in mlflow_config.yaml
# Verify backend_store_uri matches your PostgreSQL configuration

# Test database connection
psql -h localhost -U meeting_user -d meeting_db
```

### Artifacts Not Saving

**Problem**: Models and plots not appearing in MLflow UI

**Solution**:
```bash
# Check artifact store directory exists and is writable
ls -la backend/storage/mlflow-artifacts

# For S3/GCS, verify credentials are set
echo $AWS_ACCESS_KEY_ID
echo $GOOGLE_APPLICATION_CREDENTIALS

# Check MLflow logs for errors
docker-compose logs mlflow
```

### Experiments Not Appearing

**Problem**: Experiments created in code don't show in UI

**Solution**:
```python
# Verify tracking URI is set correctly
import mlflow
print(mlflow.get_tracking_uri())

# Check experiment was created
experiment = mlflow.get_experiment_by_name("sign-language-asl-baseline")
print(experiment)

# Re-run setup script
python backend/setup_mlflow.py --init-only
```

### Model Registry Errors

**Problem**: Cannot register or load models

**Solution**:
```bash
# Ensure MLflow server is running with model registry support
# (requires PostgreSQL backend store)

# Check registered models
python -c "
import mlflow
client = mlflow.tracking.MlflowClient()
print(client.list_registered_models())
"

# Re-initialize model registry
python backend/setup_mlflow.py --init-only
```

## Best Practices

### 1. Reproducibility (Requirements 51.2, 51.3, 51.10)

Always log:
- Dataset version hash
- Random seeds
- Library versions
- Hardware specifications

```python
import hashlib
import torch
import sys

# Calculate dataset hash
def calculate_dataset_hash(dataset_path):
    hasher = hashlib.sha256()
    # ... hash dataset files ...
    return hasher.hexdigest()

# Log everything needed for reproduction
mlflow.log_params({
    "dataset_hash": calculate_dataset_hash(dataset_path),
    "random_seed": 42,
    "python_version": sys.version,
    "pytorch_version": torch.__version__,
    "cuda_version": torch.version.cuda
})
```

### 2. Experiment Organization

Use descriptive run names and tags:

```python
with mlflow.start_run(run_name=f"cnn-lstm-lr{lr}-bs{bs}-{timestamp}"):
    mlflow.set_tags({
        "model_type": "cnn-lstm",
        "experiment_type": "hyperparameter_tuning",
        "researcher": "john_doe",
        "priority": "high"
    })
```

### 3. Cost Tracking (Requirement 51.15)

Log training costs:

```python
import time

start_time = time.time()
# ... training ...
end_time = time.time()

training_hours = (end_time - start_time) / 3600
gpu_hours = training_hours * num_gpus
estimated_cost = gpu_hours * 0.50  # $0.50/GPU-hour

mlflow.log_metrics({
    "training_duration_hours": training_hours,
    "gpu_hours": gpu_hours,
    "estimated_cost_usd": estimated_cost
})
```

### 4. Model Lineage (Requirement 51.11)

Track model lineage:

```python
# Log parent run ID for fine-tuned models
mlflow.log_param("parent_run_id", parent_run_id)
mlflow.log_param("base_model_version", "v2.1.0")
mlflow.log_param("fine_tuning_dataset", "v1.1.0")
```

## Integration with Training Pipeline

The training script `backend/models/train_model.py` will be updated to integrate with MLflow in Task 5.12.

Example integration:

```python
# In train_model.py
import mlflow
import mlflow.pytorch

def main():
    # Load config
    config = load_config()
    
    # Set MLflow tracking
    mlflow.set_tracking_uri(config['mlflow']['tracking_uri'])
    mlflow.set_experiment(config['mlflow']['experiment_name'])
    
    # Start run
    with mlflow.start_run():
        # Log all hyperparameters
        mlflow.log_params(config['training'])
        
        # Train model
        trainer = ModelTrainer(...)
        trainer.train()
        
        # Log model
        mlflow.pytorch.log_model(model, "model")
```

## Requirements Mapping

This MLflow setup satisfies the following requirements:

- **51.1**: Log all hyperparameters for every training run
- **51.2**: Track dataset version hash for reproducibility
- **51.3**: Set and log random seeds for deterministic training
- **51.4**: Store training curves (loss and accuracy over epochs)
- **51.6**: Link trained models back to originating experiment runs
- **51.9**: Implement MLflow experiment tracking system
- **51.13**: Store experiment artifacts (checkpoints, plots)
- **32.1**: Create model registry in MLflow
- **32.2**: Add model metadata (version, training date, metrics)
- **32.3**: Implement model tagging (production, staging, experimental)
- **32.9**: Implement model loading by version or tag

## Next Steps

1. **Task 5.12**: Integrate MLflow logging into training script
2. **Task 5.14**: Implement model registry functions
3. **Task 5.15**: Implement inference service with model loading from registry
4. **Task 5.17**: Implement drift detection with MLflow metrics

## References

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html)
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)
- [MLflow with PostgreSQL](https://mlflow.org/docs/latest/tracking.html#backend-stores)
- [MLflow with S3](https://mlflow.org/docs/latest/tracking.html#amazon-s3-and-s3-compatible-storage)

