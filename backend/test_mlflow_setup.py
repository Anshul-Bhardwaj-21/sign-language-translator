#!/usr/bin/env python3
"""
MLflow Setup Verification Script

This script verifies that MLflow is properly configured and accessible.

Usage:
    python test_mlflow_setup.py
"""

import logging
import sys
from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "backend/mlflow_config.yaml"):
    """Load MLflow configuration."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def test_tracking_uri(tracking_uri: str) -> bool:
    """Test connection to MLflow tracking server."""
    try:
        mlflow.set_tracking_uri(tracking_uri)
        client = MlflowClient(tracking_uri=tracking_uri)
        
        # Try to list experiments
        experiments = client.search_experiments()
        logger.info(f"✓ Connected to MLflow tracking server: {tracking_uri}")
        logger.info(f"  Found {len(experiments)} experiments")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to connect to tracking server: {e}")
        return False


def test_experiments(client: MlflowClient, expected_experiments: list) -> bool:
    """Test that expected experiments exist."""
    try:
        experiments = {exp.name: exp for exp in client.search_experiments()}
        
        all_found = True
        for exp_name in expected_experiments:
            if exp_name in experiments:
                exp = experiments[exp_name]
                logger.info(f"✓ Experiment exists: {exp_name} (ID: {exp.experiment_id})")
            else:
                logger.error(f"✗ Experiment not found: {exp_name}")
                all_found = False
        
        return all_found
    except Exception as e:
        logger.error(f"✗ Failed to check experiments: {e}")
        return False


def test_model_registry(client: MlflowClient, expected_models: list) -> bool:
    """Test that model registry is accessible."""
    try:
        registered_models = client.search_registered_models()
        model_names = {model.name for model in registered_models}
        
        logger.info(f"✓ Model registry accessible")
        logger.info(f"  Found {len(registered_models)} registered models")
        
        for model_name in expected_models:
            if model_name in model_names:
                logger.info(f"  ✓ Model registered: {model_name}")
            else:
                logger.info(f"  ℹ Model not yet registered: {model_name} (will be created during training)")
        
        return True
    except Exception as e:
        logger.error(f"✗ Failed to access model registry: {e}")
        logger.error("  Note: Model registry requires PostgreSQL backend store")
        return False


def test_artifact_store(artifact_root: str) -> bool:
    """Test that artifact store is accessible."""
    try:
        # Check if local path
        if not artifact_root.startswith(('s3://', 'gs://', 'wasbs://')):
            artifact_path = Path(artifact_root)
            if artifact_path.exists():
                logger.info(f"✓ Local artifact store exists: {artifact_root}")
                return True
            else:
                logger.warning(f"⚠ Local artifact store does not exist: {artifact_root}")
                logger.info("  It will be created when first artifact is logged")
                return True
        else:
            logger.info(f"✓ Cloud artifact store configured: {artifact_root}")
            logger.info("  Note: Cloud storage access will be tested during first artifact upload")
            return True
    except Exception as e:
        logger.error(f"✗ Failed to check artifact store: {e}")
        return False


def test_logging_capability(client: MlflowClient, experiment_name: str) -> bool:
    """Test that we can create a run and log data."""
    try:
        # Get experiment
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if not experiment:
            logger.error(f"✗ Experiment not found: {experiment_name}")
            return False
        
        # Create a test run
        with mlflow.start_run(experiment_id=experiment.experiment_id, run_name="test-run"):
            # Log parameters
            mlflow.log_param("test_param", "test_value")
            
            # Log metrics
            mlflow.log_metric("test_metric", 0.95)
            
            # Get run info
            run = mlflow.active_run()
            run_id = run.info.run_id
        
        # Verify run was created
        run_info = client.get_run(run_id)
        logger.info(f"✓ Successfully created test run: {run_id}")
        
        # Delete test run
        client.delete_run(run_id)
        logger.info(f"✓ Successfully deleted test run")
        
        return True
    except Exception as e:
        logger.error(f"✗ Failed to test logging capability: {e}")
        return False


def main():
    """Run all MLflow setup verification tests."""
    logger.info("="*60)
    logger.info("MLflow Setup Verification")
    logger.info("="*60)
    
    # Load configuration
    try:
        config = load_config()
        logger.info("✓ Loaded configuration from mlflow_config.yaml")
    except Exception as e:
        logger.error(f"✗ Failed to load configuration: {e}")
        sys.exit(1)
    
    # Extract configuration
    tracking_uri = config['server']['tracking_uri']
    artifact_root = config['server']['artifact_root']
    expected_experiments = [exp['name'] for exp in config['experiments'].values()]
    expected_models = [model['name'] for model in config['model_registry']['models']]
    
    # Run tests
    results = []
    
    logger.info("\n" + "="*60)
    logger.info("Test 1: Tracking Server Connection")
    logger.info("="*60)
    results.append(test_tracking_uri(tracking_uri))
    
    if results[-1]:
        client = MlflowClient(tracking_uri=tracking_uri)
        
        logger.info("\n" + "="*60)
        logger.info("Test 2: Experiments")
        logger.info("="*60)
        results.append(test_experiments(client, expected_experiments))
        
        logger.info("\n" + "="*60)
        logger.info("Test 3: Model Registry")
        logger.info("="*60)
        results.append(test_model_registry(client, expected_models))
        
        logger.info("\n" + "="*60)
        logger.info("Test 4: Artifact Store")
        logger.info("="*60)
        results.append(test_artifact_store(artifact_root))
        
        logger.info("\n" + "="*60)
        logger.info("Test 5: Logging Capability")
        logger.info("="*60)
        results.append(test_logging_capability(client, expected_experiments[0]))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("Verification Summary")
    logger.info("="*60)
    
    passed = sum(results)
    total = len(results)
    
    logger.info(f"Tests passed: {passed}/{total}")
    
    if all(results):
        logger.info("\n✓ All tests passed! MLflow is properly configured.")
        logger.info(f"\nMLflow UI: {tracking_uri}")
        logger.info("\nNext steps:")
        logger.info("  1. Train a model: python backend/models/train_model.py")
        logger.info("  2. View results: open http://localhost:5000")
        sys.exit(0)
    else:
        logger.error("\n✗ Some tests failed. Please check the errors above.")
        logger.error("\nTroubleshooting:")
        logger.error("  1. Ensure PostgreSQL is running: docker-compose ps postgres")
        logger.error("  2. Initialize MLflow: python backend/setup_mlflow.py --init-only")
        logger.error("  3. Start MLflow server: python backend/setup_mlflow.py --start-server")
        sys.exit(1)


if __name__ == '__main__':
    main()

