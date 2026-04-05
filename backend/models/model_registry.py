#!/usr/bin/env python3
"""
Model Registry Module

This module implements the model registry layer (Layer 4) for managing trained
sign language recognition models using MLflow Model Registry.

Features:
- Model registration with semantic versioning
- Model metadata management (version, training date, performance metrics)
- Model tagging (production, staging, experimental)
- Model loading by version or tag
- Model rollback capabilities
- A/B testing support

Requirements:
- 32.1: Assign semantic version numbers to all trained models
- 32.2: Store model metadata (version, training date, input shape, output labels, performance metrics)
- 32.3: Tag models with deployment status (production, staging, experimental)
- 32.9: Provide API endpoints for retrieving models by version or tag

Phase: MVP

Usage:
    from models.model_registry import ModelRegistry
    
    # Initialize registry
    registry = ModelRegistry(tracking_uri="http://localhost:5000")
    
    # Register a model
    model_version = registry.register_model(
        model_uri="runs:/abc123/model",
        model_name="sign-language-asl",
        metadata={
            "accuracy": 0.87,
            "f1_score": 0.85,
            "training_date": "2024-01-15"
        }
    )
    
    # Tag model for deployment
    registry.tag_model(
        model_name="sign-language-asl",
        version=1,
        tag="production"
    )
    
    # Load model by tag
    model = registry.load_model_by_tag(
        model_name="sign-language-asl",
        tag="production"
    )

Author: AI-Powered Meeting Platform Team
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import mlflow
from mlflow.tracking import MlflowClient
from mlflow.exceptions import MlflowException
import torch
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Model Registry for managing sign language recognition models.
    
    Provides functionality for:
    - Registering trained models with metadata
    - Tagging models with deployment status
    - Loading models by version or tag
    - Managing model lifecycle (staging, production, archived)
    - Tracking model performance metrics
    
    Requirements:
    - 32.1: Semantic version numbers for all models
    - 32.2: Model metadata storage
    - 32.3: Deployment status tagging
    - 32.9: API for retrieving models by version or tag
    """
    
    # Deployment stages (Requirement 32.3)
    STAGE_NONE = "None"
    STAGE_STAGING = "Staging"
    STAGE_PRODUCTION = "Production"
    STAGE_ARCHIVED = "Archived"
    
    # Valid deployment stages
    VALID_STAGES = [STAGE_NONE, STAGE_STAGING, STAGE_PRODUCTION, STAGE_ARCHIVED]
    
    def __init__(
        self,
        tracking_uri: Optional[str] = None,
        config_path: str = "backend/mlflow_config.yaml"
    ):
        """
        Initialize Model Registry.
        
        Args:
            tracking_uri: MLflow tracking server URI (if None, loads from config)
            config_path: Path to MLflow configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Set tracking URI
        if tracking_uri is None:
            tracking_uri = self.config.get('server', {}).get('tracking_uri', 'http://localhost:5000')
        
        self.tracking_uri = tracking_uri
        mlflow.set_tracking_uri(tracking_uri)
        
        # Initialize MLflow client
        self.client = MlflowClient(tracking_uri=tracking_uri)
        
        logger.info(f"Initialized Model Registry with tracking URI: {tracking_uri}")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load MLflow configuration from YAML file."""
        config_path = Path(config_path)
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        else:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return {}
    
    def register_model(
        self,
        model_uri: str,
        model_name: str,
        metadata: Optional[Dict] = None,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> mlflow.entities.model_registry.ModelVersion:
        """
        Register a trained model in the model registry.
        
        Args:
            model_uri: URI of the model to register (e.g., "runs:/run_id/model")
            model_name: Name of the registered model
            metadata: Model metadata (accuracy, f1_score, training_date, etc.)
            description: Model version description
            tags: Additional tags for the model version
        
        Returns:
            ModelVersion object with version number and metadata
        
        Requirements:
            - 32.1: Assigns semantic version number automatically
            - 32.2: Stores model metadata
        
        Example:
            >>> registry = ModelRegistry()
            >>> model_version = registry.register_model(
            ...     model_uri="runs:/abc123/model",
            ...     model_name="sign-language-asl",
            ...     metadata={
            ...         "accuracy": 0.87,
            ...         "f1_score": 0.85,
            ...         "training_date": "2024-01-15",
            ...         "input_shape": "(60, 126)",
            ...         "num_classes": 25
            ...     }
            ... )
            >>> print(f"Registered model version: {model_version.version}")
        """
        try:
            # Register model (MLflow auto-increments version number - Requirement 32.1)
            logger.info(f"Registering model: {model_name} from {model_uri}")
            model_version = mlflow.register_model(model_uri, model_name)
            
            logger.info(
                f"Registered {model_name} version {model_version.version} "
                f"(run_id: {model_version.run_id})"
            )
            
            # Update description if provided
            if description:
                self.client.update_model_version(
                    name=model_name,
                    version=model_version.version,
                    description=description
                )
            
            # Add metadata as tags (Requirement 32.2)
            if metadata:
                self._add_metadata_tags(model_name, model_version.version, metadata)
            
            # Add custom tags
            if tags:
                for tag_key, tag_value in tags.items():
                    self.client.set_model_version_tag(
                        name=model_name,
                        version=model_version.version,
                        key=tag_key,
                        value=str(tag_value)
                    )
            
            # Add registration timestamp
            self.client.set_model_version_tag(
                name=model_name,
                version=model_version.version,
                key="registered_at",
                value=datetime.now().isoformat()
            )
            
            return model_version
        
        except MlflowException as e:
            logger.error(f"Failed to register model: {e}")
            raise
    
    def _add_metadata_tags(
        self,
        model_name: str,
        version: int,
        metadata: Dict
    ):
        """
        Add metadata as tags to model version.
        
        Args:
            model_name: Name of the registered model
            version: Model version number
            metadata: Dictionary of metadata to add as tags
        
        Requirements:
            - 32.2: Store model metadata including performance metrics
        """
        # Standard metadata fields
        metadata_fields = [
            'accuracy', 'precision', 'recall', 'f1_score',
            'training_date', 'input_shape', 'output_labels',
            'num_classes', 'sequence_length', 'model_size_mb',
            'inference_latency_ms', 'dataset_version', 'dataset_hash'
        ]
        
        for key, value in metadata.items():
            # Convert value to string for MLflow tags
            tag_value = str(value)
            
            try:
                self.client.set_model_version_tag(
                    name=model_name,
                    version=version,
                    key=key,
                    value=tag_value
                )
                logger.debug(f"Added metadata tag: {key}={tag_value}")
            except Exception as e:
                logger.warning(f"Failed to add metadata tag {key}: {e}")
    
    def tag_model(
        self,
        model_name: str,
        version: int,
        tag: str,
        value: str = "true"
    ):
        """
        Add a tag to a model version.
        
        Args:
            model_name: Name of the registered model
            version: Model version number
            tag: Tag key
            value: Tag value (default: "true")
        
        Requirements:
            - 32.3: Tag models with deployment status
        
        Example:
            >>> registry.tag_model("sign-language-asl", 1, "production")
            >>> registry.tag_model("sign-language-asl", 2, "experimental")
        """
        try:
            self.client.set_model_version_tag(
                name=model_name,
                version=version,
                key=tag,
                value=value
            )
            logger.info(f"Tagged {model_name} v{version} with {tag}={value}")
        except MlflowException as e:
            logger.error(f"Failed to tag model: {e}")
            raise
    
    def transition_model_stage(
        self,
        model_name: str,
        version: int,
        stage: str,
        archive_existing_versions: bool = False
    ):
        """
        Transition a model version to a new stage.
        
        Args:
            model_name: Name of the registered model
            version: Model version number
            stage: Target stage (None, Staging, Production, Archived)
            archive_existing_versions: Archive existing versions in target stage
        
        Requirements:
            - 32.3: Tag models with deployment status (production, staging, experimental)
            - 32.9: Support model deployment and rollback
        
        Example:
            >>> # Deploy to production
            >>> registry.transition_model_stage(
            ...     "sign-language-asl", 3, "Production",
            ...     archive_existing_versions=True
            ... )
        """
        if stage not in self.VALID_STAGES:
            raise ValueError(
                f"Invalid stage: {stage}. Must be one of {self.VALID_STAGES}"
            )
        
        try:
            self.client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage,
                archive_existing_versions=archive_existing_versions
            )
            
            logger.info(
                f"Transitioned {model_name} v{version} to {stage} "
                f"(archive_existing={archive_existing_versions})"
            )
            
            # Add transition timestamp
            self.client.set_model_version_tag(
                name=model_name,
                version=version,
                key=f"transitioned_to_{stage.lower()}_at",
                value=datetime.now().isoformat()
            )
        
        except MlflowException as e:
            logger.error(f"Failed to transition model stage: {e}")
            raise
    
    def get_model_version(
        self,
        model_name: str,
        version: int
    ) -> mlflow.entities.model_registry.ModelVersion:
        """
        Get a specific model version.
        
        Args:
            model_name: Name of the registered model
            version: Model version number
        
        Returns:
            ModelVersion object
        
        Requirements:
            - 32.9: Provide API for retrieving models by version
        """
        try:
            model_version = self.client.get_model_version(
                name=model_name,
                version=version
            )
            return model_version
        except MlflowException as e:
            logger.error(f"Failed to get model version: {e}")
            raise
    
    def get_latest_model_version(
        self,
        model_name: str,
        stage: Optional[str] = None
    ) -> Optional[mlflow.entities.model_registry.ModelVersion]:
        """
        Get the latest model version, optionally filtered by stage.
        
        Args:
            model_name: Name of the registered model
            stage: Filter by stage (None, Staging, Production, Archived)
        
        Returns:
            Latest ModelVersion object or None if not found
        
        Requirements:
            - 32.9: Provide API for retrieving models by tag/stage
        """
        try:
            # Get all versions
            versions = self.client.search_model_versions(f"name='{model_name}'")
            
            if not versions:
                logger.warning(f"No versions found for model: {model_name}")
                return None
            
            # Filter by stage if specified
            if stage:
                versions = [v for v in versions if v.current_stage == stage]
                
                if not versions:
                    logger.warning(
                        f"No versions found for model {model_name} in stage {stage}"
                    )
                    return None
            
            # Sort by version number (descending) and return latest
            versions.sort(key=lambda v: int(v.version), reverse=True)
            return versions[0]
        
        except MlflowException as e:
            logger.error(f"Failed to get latest model version: {e}")
            raise
    
    def get_production_model_version(
        self,
        model_name: str
    ) -> Optional[mlflow.entities.model_registry.ModelVersion]:
        """
        Get the production model version.
        
        Args:
            model_name: Name of the registered model
        
        Returns:
            Production ModelVersion object or None if not found
        
        Requirements:
            - 32.9: Provide API for retrieving production models
        """
        return self.get_latest_model_version(model_name, stage=self.STAGE_PRODUCTION)
    
    def load_model_by_version(
        self,
        model_name: str,
        version: int,
        device: str = "cpu"
    ) -> torch.nn.Module:
        """
        Load a model by version number.
        
        Args:
            model_name: Name of the registered model
            version: Model version number
            device: Device to load model on ('cpu' or 'cuda')
        
        Returns:
            Loaded PyTorch model
        
        Requirements:
            - 32.9: Provide API for retrieving models by version
        
        Example:
            >>> model = registry.load_model_by_version("sign-language-asl", 3)
        """
        try:
            model_uri = f"models:/{model_name}/{version}"
            logger.info(f"Loading model from: {model_uri}")
            
            # Load model using MLflow
            model = mlflow.pytorch.load_model(model_uri, map_location=device)
            
            logger.info(f"Loaded {model_name} v{version} on {device}")
            return model
        
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def load_model_by_stage(
        self,
        model_name: str,
        stage: str = "Production",
        device: str = "cpu"
    ) -> torch.nn.Module:
        """
        Load a model by deployment stage.
        
        Args:
            model_name: Name of the registered model
            stage: Deployment stage (Staging, Production, Archived)
            device: Device to load model on ('cpu' or 'cuda')
        
        Returns:
            Loaded PyTorch model
        
        Requirements:
            - 32.9: Provide API for retrieving models by tag/stage
        
        Example:
            >>> model = registry.load_model_by_stage("sign-language-asl", "Production")
        """
        try:
            model_uri = f"models:/{model_name}/{stage}"
            logger.info(f"Loading model from: {model_uri}")
            
            # Load model using MLflow
            model = mlflow.pytorch.load_model(model_uri, map_location=device)
            
            logger.info(f"Loaded {model_name} ({stage}) on {device}")
            return model
        
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def list_model_versions(
        self,
        model_name: str,
        stage: Optional[str] = None
    ) -> List[mlflow.entities.model_registry.ModelVersion]:
        """
        List all versions of a registered model.
        
        Args:
            model_name: Name of the registered model
            stage: Filter by stage (optional)
        
        Returns:
            List of ModelVersion objects
        """
        try:
            # Search for model versions
            filter_string = f"name='{model_name}'"
            versions = self.client.search_model_versions(filter_string)
            
            # Filter by stage if specified
            if stage:
                versions = [v for v in versions if v.current_stage == stage]
            
            # Sort by version number (descending)
            versions.sort(key=lambda v: int(v.version), reverse=True)
            
            logger.info(f"Found {len(versions)} versions for {model_name}")
            return versions
        
        except MlflowException as e:
            logger.error(f"Failed to list model versions: {e}")
            raise
    
    def get_model_metadata(
        self,
        model_name: str,
        version: int
    ) -> Dict:
        """
        Get metadata for a model version.
        
        Args:
            model_name: Name of the registered model
            version: Model version number
        
        Returns:
            Dictionary of model metadata
        
        Requirements:
            - 32.2: Retrieve stored model metadata
        """
        try:
            model_version = self.get_model_version(model_name, version)
            
            # Extract metadata from tags
            metadata = {
                'name': model_name,
                'version': model_version.version,
                'run_id': model_version.run_id,
                'current_stage': model_version.current_stage,
                'creation_timestamp': model_version.creation_timestamp,
                'last_updated_timestamp': model_version.last_updated_timestamp,
                'description': model_version.description,
                'source': model_version.source,
                'status': model_version.status
            }
            
            # Add tags as metadata
            if model_version.tags:
                metadata['tags'] = model_version.tags
            
            return metadata
        
        except MlflowException as e:
            logger.error(f"Failed to get model metadata: {e}")
            raise
    
    def delete_model_version(
        self,
        model_name: str,
        version: int
    ):
        """
        Delete a model version.
        
        Args:
            model_name: Name of the registered model
            version: Model version number
        
        Warning:
            This operation is irreversible. Use with caution.
        """
        try:
            self.client.delete_model_version(
                name=model_name,
                version=version
            )
            logger.info(f"Deleted {model_name} v{version}")
        except MlflowException as e:
            logger.error(f"Failed to delete model version: {e}")
            raise
    
    def rollback_to_version(
        self,
        model_name: str,
        version: int,
        target_stage: str = "Production"
    ):
        """
        Rollback to a previous model version by promoting it to target stage.
        
        Args:
            model_name: Name of the registered model
            version: Model version number to rollback to
            target_stage: Target deployment stage (default: Production)
        
        Requirements:
            - 32.5: Support rollback to previous model versions within 5 minutes
        
        Example:
            >>> # Rollback to version 2 in production
            >>> registry.rollback_to_version("sign-language-asl", 2, "Production")
        """
        try:
            logger.info(f"Rolling back {model_name} to version {version}")
            
            # Transition target version to specified stage
            self.transition_model_stage(
                model_name=model_name,
                version=version,
                stage=target_stage,
                archive_existing_versions=True
            )
            
            # Add rollback tag
            self.tag_model(
                model_name=model_name,
                version=version,
                tag="rollback_at",
                value=datetime.now().isoformat()
            )
            
            logger.info(f"Successfully rolled back to {model_name} v{version}")
        
        except Exception as e:
            logger.error(f"Failed to rollback model: {e}")
            raise
    
    def compare_model_versions(
        self,
        model_name: str,
        version1: int,
        version2: int
    ) -> Dict:
        """
        Compare two model versions.
        
        Args:
            model_name: Name of the registered model
            version1: First model version number
            version2: Second model version number
        
        Returns:
            Dictionary with comparison results
        """
        try:
            # Get metadata for both versions
            metadata1 = self.get_model_metadata(model_name, version1)
            metadata2 = self.get_model_metadata(model_name, version2)
            
            comparison = {
                'model_name': model_name,
                'version1': version1,
                'version2': version2,
                'metadata1': metadata1,
                'metadata2': metadata2
            }
            
            # Compare performance metrics if available
            metrics_to_compare = ['accuracy', 'f1_score', 'precision', 'recall']
            metric_comparison = {}
            
            for metric in metrics_to_compare:
                val1 = metadata1.get('tags', {}).get(metric)
                val2 = metadata2.get('tags', {}).get(metric)
                
                if val1 and val2:
                    try:
                        val1_float = float(val1)
                        val2_float = float(val2)
                        diff = val2_float - val1_float
                        metric_comparison[metric] = {
                            'version1': val1_float,
                            'version2': val2_float,
                            'difference': diff,
                            'improvement': diff > 0
                        }
                    except ValueError:
                        pass
            
            comparison['metric_comparison'] = metric_comparison
            
            return comparison
        
        except Exception as e:
            logger.error(f"Failed to compare model versions: {e}")
            raise


def main():
    """Example usage of ModelRegistry."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Model Registry CLI')
    parser.add_argument('--list', type=str, help='List versions for model')
    parser.add_argument('--metadata', type=str, nargs=2, metavar=('MODEL', 'VERSION'),
                       help='Get metadata for model version')
    parser.add_argument('--production', type=str, help='Get production version for model')
    
    args = parser.parse_args()
    
    # Initialize registry
    registry = ModelRegistry()
    
    if args.list:
        versions = registry.list_model_versions(args.list)
        print(f"\nModel versions for {args.list}:")
        for v in versions:
            print(f"  v{v.version} - {v.current_stage} (run: {v.run_id})")
    
    elif args.metadata:
        model_name, version = args.metadata
        metadata = registry.get_model_metadata(model_name, int(version))
        print(f"\nMetadata for {model_name} v{version}:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
    
    elif args.production:
        version = registry.get_production_model_version(args.production)
        if version:
            print(f"\nProduction version for {args.production}: v{version.version}")
        else:
            print(f"\nNo production version found for {args.production}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
