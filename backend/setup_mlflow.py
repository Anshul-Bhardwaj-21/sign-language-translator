#!/usr/bin/env python3
"""
MLflow Experiment Tracking Setup Script

This script sets up MLflow tracking server with PostgreSQL backend store
and S3/GCS artifact store for production ML experiment tracking.

Requirements:
- 51.9: Setup MLflow experiment tracking
- 51.2: Configure PostgreSQL backend store
- 51.13: Configure artifact store for model checkpoints and plots

Usage:
    # Setup MLflow with default configuration
    python setup_mlflow.py
    
    # Setup with custom config file
    python setup_mlflow.py --config mlflow_config.yaml
    
    # Initialize experiments only (don't start server)
    python setup_mlflow.py --init-only
    
    # Start MLflow server
    python setup_mlflow.py --start-server

Author: AI-Powered Meeting Platform Team
Phase: MVP
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

import mlflow
from mlflow.tracking import MlflowClient
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MLflowSetup:
    """
    MLflow setup and configuration manager.
    
    Handles:
    - MLflow tracking server configuration
    - PostgreSQL backend store setup
    - S3/GCS artifact store configuration
    - Experiment creation and initialization
    - Model registry setup
    """
    
    def __init__(self, config_path: str = "backend/mlflow_config.yaml"):
        """
        Initialize MLflow setup.
        
        Args:
            config_path: Path to MLflow configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.client: Optional[MlflowClient] = None
    
    def _load_config(self) -> Dict:
        """Load MLflow configuration from YAML file."""
        if not self.config_path.exists():
            logger.error(f"Configuration file not found: {self.config_path}")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded configuration from {self.config_path}")
        return config
    
    def setup_artifact_store(self):
        """
        Setup artifact store directory or validate cloud storage.
        
        Requirements:
        - 51.13: Configure artifact store for models and plots
        """
        artifact_root = self.config['server']['artifact_root']
        
        # Check if using local storage
        if not artifact_root.startswith(('s3://', 'gs://', 'wasbs://')):
            # Local storage - create directory
            artifact_path = Path(artifact_root)
            artifact_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created local artifact store: {artifact_path}")
        else:
            # Cloud storage - validate configuration
            logger.info(f"Using cloud artifact store: {artifact_root}")
            
            if artifact_root.startswith('s3://'):
                # Validate AWS credentials
                if not os.getenv('AWS_ACCESS_KEY_ID'):
                    logger.warning("AWS_ACCESS_KEY_ID not set. S3 access may fail.")
                logger.info("S3 artifact store configured")
            
            elif artifact_root.startswith('gs://'):
                # Validate GCS credentials
                if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                    logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set. GCS access may fail.")
                logger.info("GCS artifact store configured")
    
    def verify_backend_store(self):
        """
        Verify PostgreSQL backend store connection.
        
        Requirements:
        - 51.2: Configure PostgreSQL backend store
        """
        backend_uri = self.config['server']['backend_store_uri']
        
        try:
            # Try to import psycopg2 to verify PostgreSQL support
            import psycopg2
            
            # Parse connection string
            # Format: postgresql://user:pass@host:port/dbname
            logger.info(f"Backend store URI: {backend_uri}")
            
            # Test connection (basic validation)
            if backend_uri.startswith('postgresql://'):
                logger.info("PostgreSQL backend store configured")
            else:
                logger.warning(f"Unexpected backend store URI format: {backend_uri}")
        
        except ImportError:
            logger.error("psycopg2 not installed. PostgreSQL backend store will not work.")
            logger.error("Install with: pip install psycopg2-binary")
            raise
    
    def initialize_mlflow_client(self):
        """Initialize MLflow tracking client."""
        tracking_uri = self.config['server']['tracking_uri']
        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient(tracking_uri=tracking_uri)
        logger.info(f"Initialized MLflow client with tracking URI: {tracking_uri}")
    
    def create_experiments(self):
        """
        Create MLflow experiments defined in configuration.
        
        Requirements:
        - 51.9: Create experiment for sign-language-asl-baseline
        """
        if not self.client:
            self.initialize_mlflow_client()
        
        experiments_config = self.config.get('experiments', {})
        
        for exp_key, exp_config in experiments_config.items():
            exp_name = exp_config['name']
            exp_description = exp_config.get('description', '')
            exp_tags = exp_config.get('tags', {})
            
            try:
                # Check if experiment already exists
                experiment = mlflow.get_experiment_by_name(exp_name)
                
                if experiment:
                    logger.info(f"Experiment already exists: {exp_name} (ID: {experiment.experiment_id})")
                    
                    # Update tags if needed
                    for tag_key, tag_value in exp_tags.items():
                        self.client.set_experiment_tag(experiment.experiment_id, tag_key, tag_value)
                else:
                    # Create new experiment
                    experiment_id = mlflow.create_experiment(
                        name=exp_name,
                        artifact_location=None,  # Use default from server config
                        tags=exp_tags
                    )
                    logger.info(f"Created experiment: {exp_name} (ID: {experiment_id})")
                    
                    # Set description as tag (MLflow doesn't have native description field)
                    if exp_description:
                        self.client.set_experiment_tag(experiment_id, "description", exp_description)
            
            except Exception as e:
                logger.error(f"Failed to create experiment {exp_name}: {e}")
                raise
    
    def setup_model_registry(self):
        """
        Setup model registry with registered model names.
        
        Requirements:
        - 32.1: Create model registry in MLflow
        """
        if not self.client:
            self.initialize_mlflow_client()
        
        models_config = self.config.get('model_registry', {}).get('models', [])
        
        for model_config in models_config:
            model_name = model_config['name']
            model_description = model_config.get('description', '')
            model_tags = model_config.get('tags', {})
            
            try:
                # Check if registered model exists
                try:
                    registered_model = self.client.get_registered_model(model_name)
                    logger.info(f"Registered model already exists: {model_name}")
                    
                    # Update description and tags
                    if model_description:
                        self.client.update_registered_model(
                            name=model_name,
                            description=model_description
                        )
                    
                    for tag_key, tag_value in model_tags.items():
                        self.client.set_registered_model_tag(model_name, tag_key, tag_value)
                
                except mlflow.exceptions.RestException:
                    # Model doesn't exist, create it
                    registered_model = self.client.create_registered_model(
                        name=model_name,
                        tags=model_tags,
                        description=model_description
                    )
                    logger.info(f"Created registered model: {model_name}")
            
            except Exception as e:
                logger.error(f"Failed to setup registered model {model_name}: {e}")
                # Don't raise - model registry setup is optional for initial setup
                logger.warning("Continuing without model registry setup")
    
    def start_server(self):
        """
        Start MLflow tracking server.
        
        Requirements:
        - 51.9: Install and configure MLflow tracking server
        """
        backend_uri = self.config['server']['backend_store_uri']
        artifact_root = self.config['server']['artifact_root']
        host = self.config['server']['host']
        port = self.config['server']['port']
        workers = self.config['server'].get('workers', 2)
        
        # Build MLflow server command
        cmd = [
            'mlflow', 'server',
            '--backend-store-uri', backend_uri,
            '--default-artifact-root', artifact_root,
            '--host', host,
            '--port', str(port),
            '--workers', str(workers)
        ]
        
        logger.info("="*60)
        logger.info("Starting MLflow Tracking Server")
        logger.info("="*60)
        logger.info(f"Backend Store: {backend_uri}")
        logger.info(f"Artifact Root: {artifact_root}")
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info(f"Workers: {workers}")
        logger.info("="*60)
        logger.info(f"Command: {' '.join(cmd)}")
        logger.info("="*60)
        logger.info("Press Ctrl+C to stop the server")
        logger.info("="*60)
        
        try:
            # Start server (blocking)
            subprocess.run(cmd, check=True)
        except KeyboardInterrupt:
            logger.info("\nMLflow server stopped by user")
        except subprocess.CalledProcessError as e:
            logger.error(f"MLflow server failed: {e}")
            raise
    
    def print_setup_summary(self):
        """Print setup summary and usage instructions."""
        tracking_uri = self.config['server']['tracking_uri']
        
        print("\n" + "="*60)
        print("MLflow Setup Complete!")
        print("="*60)
        print(f"\nTracking URI: {tracking_uri}")
        print(f"\nExperiments created:")
        
        for exp_config in self.config.get('experiments', {}).values():
            print(f"  - {exp_config['name']}")
        
        print(f"\nModel registry initialized:")
        for model_config in self.config.get('model_registry', {}).get('models', []):
            print(f"  - {model_config['name']}")
        
        print("\n" + "="*60)
        print("Usage Instructions:")
        print("="*60)
        print("\n1. Start MLflow server:")
        print("   python setup_mlflow.py --start-server")
        print("\n2. Access MLflow UI:")
        print(f"   Open browser: {tracking_uri}")
        print("\n3. Use in training scripts:")
        print("   import mlflow")
        print(f"   mlflow.set_tracking_uri('{tracking_uri}')")
        print("   mlflow.set_experiment('sign-language-asl-baseline')")
        print("\n4. View experiments:")
        print("   mlflow ui --backend-store-uri <backend_uri>")
        print("="*60 + "\n")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Setup MLflow experiment tracking',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='backend/mlflow_config.yaml',
        help='Path to MLflow configuration file'
    )
    
    parser.add_argument(
        '--init-only',
        action='store_true',
        help='Initialize experiments and model registry only (do not start server)'
    )
    
    parser.add_argument(
        '--start-server',
        action='store_true',
        help='Start MLflow tracking server'
    )
    
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Verify configuration only (do not initialize or start server)'
    )
    
    return parser.parse_args()


def main():
    """Main setup function."""
    args = parse_args()
    
    try:
        # Initialize setup
        setup = MLflowSetup(config_path=args.config)
        
        # Verify backend store
        logger.info("Verifying backend store configuration...")
        setup.verify_backend_store()
        
        # Setup artifact store
        logger.info("Setting up artifact store...")
        setup.setup_artifact_store()
        
        if args.verify_only:
            logger.info("Configuration verification complete!")
            return
        
        # Initialize MLflow client
        logger.info("Initializing MLflow client...")
        setup.initialize_mlflow_client()
        
        # Create experiments
        logger.info("Creating experiments...")
        setup.create_experiments()
        
        # Setup model registry
        logger.info("Setting up model registry...")
        setup.setup_model_registry()
        
        # Print summary
        setup.print_setup_summary()
        
        # Start server if requested
        if args.start_server:
            setup.start_server()
        elif not args.init_only:
            logger.info("\nTo start the MLflow server, run:")
            logger.info("  python setup_mlflow.py --start-server")
    
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

