# MLflow Quick Start Guide

Quick reference for getting MLflow up and running.

## Prerequisites

- Python 3.8+
- PostgreSQL database running (via docker-compose)
- MLflow installed (`pip install mlflow>=2.9.0`)

## Quick Start Commands

### Start Everything with Docker

```bash
# Start all services (PostgreSQL, Redis, MLflow, Backend, Frontend)
docker-compose up -d

# View MLflow UI
open http://localhost:5000
```

### Local Development

#### Linux/Mac

```bash
# Initialize and start MLflow server
bash backend/start_mlflow.sh
```

#### Windows

```powershell
# Initialize and start MLflow server
powershell backend/start_mlflow.ps1
```

#### Manual Steps

```bash
# 1. Initialize experiments
python backend/setup_mlflow.py --init-only

# 2. Start server
python backend/setup_mlflow.py --start-server

# 3. Access UI
# Open browser: http://localhost:5000
```

## Verify Setup

```bash
# Check MLflow is accessible
curl http://localhost:5000/health

# List experiments
python -c "
import mlflow
mlflow.set_tracking_uri('http://localhost:5000')
experiments = mlflow.search_experiments()
for exp in experiments:
    print(f'{exp.name}: {exp.experiment_id}')
"
```

## Common Tasks

### View Experiments

```bash
# Open MLflow UI
open http://localhost:5000

# Or use CLI
mlflow experiments list --tracking-uri http://localhost:5000
```

### Run Training with MLflow

```bash
# Train model (will log to MLflow automatically)
python backend/models/train_model.py

# View results in UI
open http://localhost:5000
```

### Register Model

```python
import mlflow

mlflow.set_tracking_uri("http://localhost:5000")

# Register model from run
model_uri = "runs:/abc123/model"
mlflow.register_model(model_uri, "sign-language-asl")
```

### Load Model

```python
import mlflow.pytorch

# Load latest production model
model = mlflow.pytorch.load_model("models:/sign-language-asl/Production")
```

## Configuration Files

- `backend/mlflow_config.yaml` - Main configuration
- `backend/setup_mlflow.py` - Setup script
- `docker-compose.yml` - Docker service definition

## Troubleshooting

### Server won't start

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs mlflow
```

### Can't connect to tracking server

```bash
# Verify server is running
curl http://localhost:5000/health

# Check tracking URI
python -c "import mlflow; print(mlflow.get_tracking_uri())"
```

### Experiments not showing

```bash
# Re-initialize experiments
python backend/setup_mlflow.py --init-only
```

## Next Steps

1. Read full documentation: `backend/MLFLOW_SETUP_GUIDE.md`
2. Train your first model: `python backend/models/train_model.py`
3. View results in UI: `http://localhost:5000`
4. Register model for deployment

## Key URLs

- **MLflow UI**: http://localhost:5000
- **API Docs**: http://localhost:5000/api/2.0/mlflow/docs
- **Health Check**: http://localhost:5000/health

## Requirements Satisfied

✅ 51.9 - Setup MLflow experiment tracking  
✅ PostgreSQL backend store configured  
✅ Artifact store configured (local/S3/GCS)  
✅ Experiment created: sign-language-asl-baseline  
✅ Model registry initialized  
✅ Documentation complete  

