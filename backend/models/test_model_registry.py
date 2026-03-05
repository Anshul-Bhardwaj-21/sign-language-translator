#!/usr/bin/env python3
"""
Unit Tests for Model Registry

Tests the model registry functionality including:
- Model registration with metadata
- Model tagging and stage transitions
- Model loading by version and stage
- Model rollback
- Metadata retrieval

Requirements:
- 32.1: Test semantic version assignment
- 32.2: Test model metadata storage and retrieval
- 32.3: Test deployment status tagging
- 32.9: Test model retrieval by version and tag

Phase: MVP

Usage:
    # Run all tests
    pytest test_model_registry.py -v
    
    # Run specific test
    pytest test_model_registry.py::test_register_model -v

Author: AI-Powered Meeting Platform Team
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import mlflow
import torch
import torch.nn as nn

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from models.model_registry import ModelRegistry


class DummyModel(nn.Module):
    """Dummy PyTorch model for testing."""
    
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(10, 5)
    
    def forward(self, x):
        return self.fc(x)


class TestModelRegistry(unittest.TestCase):
    """Test cases for ModelRegistry class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are shared across all tests."""
        # Use in-memory SQLite for testing
        cls.tracking_uri = "sqlite:///:memory:"
        cls.test_counter = 0
    
    def setUp(self):
        """Set up test fixtures before each test."""
        # Create temporary directory for artifacts
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize registry with test tracking URI
        self.registry = ModelRegistry(tracking_uri=self.tracking_uri)
        
        # Create a unique model name for each test to avoid conflicts
        TestModelRegistry.test_counter += 1
        self.test_model_name = f"test-sign-language-model-{TestModelRegistry.test_counter}"
        
        # Create a dummy model for testing
        self.dummy_model = DummyModel()
    
    def tearDown(self):
        """Clean up after each test."""
        # Clean up temporary directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_run_with_model(self) -> str:
        """
        Helper method to create a test MLflow run with a logged model.
        
        Returns:
            Run ID of the created run
        """
        with mlflow.start_run() as run:
            # Log dummy model
            mlflow.pytorch.log_model(self.dummy_model, "model")
            
            # Log some metrics
            mlflow.log_metrics({
                "accuracy": 0.87,
                "f1_score": 0.85,
                "precision": 0.86,
                "recall": 0.84
            })
            
            # Log parameters
            mlflow.log_params({
                "learning_rate": 0.001,
                "batch_size": 32,
                "epochs": 100
            })
            
            run_id = run.info.run_id
        
        return run_id
    
    def test_initialization(self):
        """Test ModelRegistry initialization."""
        # Test with explicit tracking URI
        registry = ModelRegistry(tracking_uri=self.tracking_uri)
        self.assertEqual(registry.tracking_uri, self.tracking_uri)
        self.assertIsNotNone(registry.client)
    
    def test_register_model(self):
        """
        Test model registration with metadata.
        
        Requirements:
        - 32.1: Test semantic version assignment
        - 32.2: Test model metadata storage
        """
        # Create test run with model
        run_id = self._create_test_run_with_model()
        model_uri = f"runs:/{run_id}/model"
        
        # Register model with metadata
        metadata = {
            "accuracy": 0.87,
            "f1_score": 0.85,
            "training_date": "2024-01-15",
            "input_shape": "(60, 126)",
            "num_classes": 25
        }
        
        model_version = self.registry.register_model(
            model_uri=model_uri,
            model_name=self.test_model_name,
            metadata=metadata,
            description="Test model for unit testing"
        )
        
        # Verify version assignment (Requirement 32.1)
        self.assertIsNotNone(model_version)
        self.assertEqual(str(model_version.version), "1")  # First version
        self.assertEqual(model_version.name, self.test_model_name)
        
        # Verify metadata storage (Requirement 32.2)
        retrieved_metadata = self.registry.get_model_metadata(
            self.test_model_name,
            int(model_version.version)
        )
        
        self.assertIn('tags', retrieved_metadata)
        self.assertEqual(retrieved_metadata['tags']['accuracy'], "0.87")
        self.assertEqual(retrieved_metadata['tags']['f1_score'], "0.85")
        self.assertEqual(retrieved_metadata['tags']['num_classes'], "25")
    
    def test_register_multiple_versions(self):
        """
        Test registering multiple versions of the same model.
        
        Requirements:
        - 32.1: Test semantic version auto-increment
        """
        # Register first version
        run_id1 = self._create_test_run_with_model()
        model_version1 = self.registry.register_model(
            model_uri=f"runs:/{run_id1}/model",
            model_name=self.test_model_name,
            metadata={"accuracy": 0.85}
        )
        
        # Register second version
        run_id2 = self._create_test_run_with_model()
        model_version2 = self.registry.register_model(
            model_uri=f"runs:/{run_id2}/model",
            model_name=self.test_model_name,
            metadata={"accuracy": 0.87}
        )
        
        # Register third version
        run_id3 = self._create_test_run_with_model()
        model_version3 = self.registry.register_model(
            model_uri=f"runs:/{run_id3}/model",
            model_name=self.test_model_name,
            metadata={"accuracy": 0.90}
        )
        
        # Verify version numbers increment correctly
        self.assertEqual(str(model_version1.version), "1")
        self.assertEqual(str(model_version2.version), "2")
        self.assertEqual(str(model_version3.version), "3")
    
    def test_tag_model(self):
        """
        Test adding tags to model versions.
        
        Requirements:
        - 32.3: Test deployment status tagging
        """
        # Register model
        run_id = self._create_test_run_with_model()
        model_version = self.registry.register_model(
            model_uri=f"runs:/{run_id}/model",
            model_name=self.test_model_name
        )
        
        # Add tags
        self.registry.tag_model(
            model_name=self.test_model_name,
            version=int(model_version.version),
            tag="production",
            value="true"
        )
        
        self.registry.tag_model(
            model_name=self.test_model_name,
            version=int(model_version.version),
            tag="validated",
            value="true"
        )
        
        # Verify tags
        metadata = self.registry.get_model_metadata(
            self.test_model_name,
            int(model_version.version)
        )
        
        self.assertIn('tags', metadata)
        self.assertEqual(metadata['tags']['production'], "true")
        self.assertEqual(metadata['tags']['validated'], "true")
    
    def test_transition_model_stage(self):
        """
        Test transitioning model to different stages.
        
        Requirements:
        - 32.3: Test deployment status (production, staging, experimental)
        """
        # Register model
        run_id = self._create_test_run_with_model()
        model_version = self.registry.register_model(
            model_uri=f"runs:/{run_id}/model",
            model_name=self.test_model_name
        )
        
        version_num = int(model_version.version)
        
        # Transition to Staging
        self.registry.transition_model_stage(
            model_name=self.test_model_name,
            version=version_num,
            stage=ModelRegistry.STAGE_STAGING
        )
        
        # Verify stage
        model_version = self.registry.get_model_version(
            self.test_model_name,
            version_num
        )
        self.assertEqual(model_version.current_stage, ModelRegistry.STAGE_STAGING)
        
        # Transition to Production
        self.registry.transition_model_stage(
            model_name=self.test_model_name,
            version=version_num,
            stage=ModelRegistry.STAGE_PRODUCTION
        )
        
        # Verify stage
        model_version = self.registry.get_model_version(
            self.test_model_name,
            version_num
        )
        self.assertEqual(model_version.current_stage, ModelRegistry.STAGE_PRODUCTION)
    
    def test_get_model_version(self):
        """
        Test retrieving specific model version.
        
        Requirements:
        - 32.9: Test model retrieval by version
        """
        # Register model
        run_id = self._create_test_run_with_model()
        registered_version = self.registry.register_model(
            model_uri=f"runs:/{run_id}/model",
            model_name=self.test_model_name
        )
        
        # Retrieve model version
        retrieved_version = self.registry.get_model_version(
            self.test_model_name,
            int(registered_version.version)
        )
        
        # Verify
        self.assertEqual(retrieved_version.version, registered_version.version)
        self.assertEqual(retrieved_version.name, self.test_model_name)
        self.assertEqual(retrieved_version.run_id, registered_version.run_id)
    
    def test_get_latest_model_version(self):
        """
        Test retrieving latest model version.
        
        Requirements:
        - 32.9: Test model retrieval
        """
        # Register multiple versions
        for i in range(3):
            run_id = self._create_test_run_with_model()
            self.registry.register_model(
                model_uri=f"runs:/{run_id}/model",
                model_name=self.test_model_name,
                metadata={"accuracy": 0.85 + i * 0.02}
            )
        
        # Get latest version
        latest_version = self.registry.get_latest_model_version(
            self.test_model_name
        )
        
        # Verify it's version 3
        self.assertIsNotNone(latest_version)
        self.assertEqual(str(latest_version.version), "3")
    
    def test_get_latest_model_version_by_stage(self):
        """
        Test retrieving latest model version filtered by stage.
        
        Requirements:
        - 32.9: Test model retrieval by tag/stage
        """
        # Register multiple versions
        versions = []
        for i in range(3):
            run_id = self._create_test_run_with_model()
            version = self.registry.register_model(
                model_uri=f"runs:/{run_id}/model",
                model_name=self.test_model_name
            )
            versions.append(version)
        
        # Transition version 2 to Production
        self.registry.transition_model_stage(
            model_name=self.test_model_name,
            version=2,
            stage=ModelRegistry.STAGE_PRODUCTION
        )
        
        # Get latest production version
        prod_version = self.registry.get_latest_model_version(
            self.test_model_name,
            stage=ModelRegistry.STAGE_PRODUCTION
        )
        
        # Verify it's version 2
        self.assertIsNotNone(prod_version)
        self.assertEqual(str(prod_version.version), "2")
        self.assertEqual(prod_version.current_stage, ModelRegistry.STAGE_PRODUCTION)
    
    def test_get_production_model_version(self):
        """
        Test retrieving production model version.
        
        Requirements:
        - 32.9: Test production model retrieval
        """
        # Register model
        run_id = self._create_test_run_with_model()
        model_version = self.registry.register_model(
            model_uri=f"runs:/{run_id}/model",
            model_name=self.test_model_name
        )
        
        # Transition to Production
        self.registry.transition_model_stage(
            model_name=self.test_model_name,
            version=int(model_version.version),
            stage=ModelRegistry.STAGE_PRODUCTION
        )
        
        # Get production version
        prod_version = self.registry.get_production_model_version(
            self.test_model_name
        )
        
        # Verify
        self.assertIsNotNone(prod_version)
        self.assertEqual(prod_version.version, model_version.version)
        self.assertEqual(prod_version.current_stage, ModelRegistry.STAGE_PRODUCTION)
    
    def test_list_model_versions(self):
        """Test listing all model versions."""
        # Register multiple versions
        for i in range(3):
            run_id = self._create_test_run_with_model()
            self.registry.register_model(
                model_uri=f"runs:/{run_id}/model",
                model_name=self.test_model_name
            )
        
        # List all versions
        versions = self.registry.list_model_versions(self.test_model_name)
        
        # Verify
        self.assertEqual(len(versions), 3)
        # Should be sorted in descending order
        self.assertEqual(str(versions[0].version), "3")
        self.assertEqual(str(versions[1].version), "2")
        self.assertEqual(str(versions[2].version), "1")
    
    def test_list_model_versions_by_stage(self):
        """Test listing model versions filtered by stage."""
        # Register multiple versions
        for i in range(3):
            run_id = self._create_test_run_with_model()
            version = self.registry.register_model(
                model_uri=f"runs:/{run_id}/model",
                model_name=self.test_model_name
            )
            
            # Transition version 2 to Production
            if int(version.version) == 2:
                self.registry.transition_model_stage(
                    model_name=self.test_model_name,
                    version=2,
                    stage=ModelRegistry.STAGE_PRODUCTION
                )
        
        # List production versions
        prod_versions = self.registry.list_model_versions(
            self.test_model_name,
            stage=ModelRegistry.STAGE_PRODUCTION
        )
        
        # Verify
        self.assertEqual(len(prod_versions), 1)
        self.assertEqual(str(prod_versions[0].version), "2")
    
    def test_get_model_metadata(self):
        """
        Test retrieving model metadata.
        
        Requirements:
        - 32.2: Test metadata retrieval
        """
        # Register model with metadata
        run_id = self._create_test_run_with_model()
        metadata = {
            "accuracy": 0.87,
            "f1_score": 0.85,
            "training_date": "2024-01-15",
            "num_classes": 25
        }
        
        model_version = self.registry.register_model(
            model_uri=f"runs:/{run_id}/model",
            model_name=self.test_model_name,
            metadata=metadata,
            description="Test model"
        )
        
        # Retrieve metadata
        retrieved_metadata = self.registry.get_model_metadata(
            self.test_model_name,
            int(model_version.version)
        )
        
        # Verify metadata fields
        self.assertEqual(retrieved_metadata['name'], self.test_model_name)
        self.assertEqual(retrieved_metadata['version'], model_version.version)
        self.assertEqual(retrieved_metadata['description'], "Test model")
        self.assertIn('tags', retrieved_metadata)
        self.assertEqual(retrieved_metadata['tags']['accuracy'], "0.87")
        self.assertEqual(retrieved_metadata['tags']['f1_score'], "0.85")
    
    def test_rollback_to_version(self):
        """
        Test rolling back to a previous model version.
        
        Requirements:
        - 32.5: Test model rollback functionality
        """
        # Register multiple versions
        versions = []
        for i in range(3):
            run_id = self._create_test_run_with_model()
            version = self.registry.register_model(
                model_uri=f"runs:/{run_id}/model",
                model_name=self.test_model_name,
                metadata={"accuracy": 0.85 + i * 0.02}
            )
            versions.append(version)
        
        # Transition version 3 to Production
        self.registry.transition_model_stage(
            model_name=self.test_model_name,
            version=3,
            stage=ModelRegistry.STAGE_PRODUCTION
        )
        
        # Rollback to version 2
        self.registry.rollback_to_version(
            model_name=self.test_model_name,
            version=2,
            target_stage=ModelRegistry.STAGE_PRODUCTION
        )
        
        # Verify version 2 is now in Production
        prod_version = self.registry.get_production_model_version(
            self.test_model_name
        )
        self.assertEqual(str(prod_version.version), "2")
        
        # Verify rollback tag was added
        metadata = self.registry.get_model_metadata(self.test_model_name, 2)
        self.assertIn('rollback_at', metadata['tags'])
    
    def test_compare_model_versions(self):
        """Test comparing two model versions."""
        # Register two versions with different metrics
        run_id1 = self._create_test_run_with_model()
        self.registry.register_model(
            model_uri=f"runs:/{run_id1}/model",
            model_name=self.test_model_name,
            metadata={"accuracy": 0.85, "f1_score": 0.83}
        )
        
        run_id2 = self._create_test_run_with_model()
        self.registry.register_model(
            model_uri=f"runs:/{run_id2}/model",
            model_name=self.test_model_name,
            metadata={"accuracy": 0.90, "f1_score": 0.88}
        )
        
        # Compare versions
        comparison = self.registry.compare_model_versions(
            self.test_model_name,
            version1=1,
            version2=2
        )
        
        # Verify comparison results
        self.assertEqual(comparison['model_name'], self.test_model_name)
        self.assertEqual(comparison['version1'], 1)
        self.assertEqual(comparison['version2'], 2)
        
        # Verify metric comparison
        self.assertIn('metric_comparison', comparison)
        self.assertIn('accuracy', comparison['metric_comparison'])
        
        acc_comparison = comparison['metric_comparison']['accuracy']
        self.assertEqual(acc_comparison['version1'], 0.85)
        self.assertEqual(acc_comparison['version2'], 0.90)
        self.assertAlmostEqual(acc_comparison['difference'], 0.05, places=2)
        self.assertTrue(acc_comparison['improvement'])
    
    def test_load_model_by_version(self):
        """
        Test loading model by version number.
        
        Requirements:
        - 32.9: Test model loading by version
        """
        # Register model
        run_id = self._create_test_run_with_model()
        model_version = self.registry.register_model(
            model_uri=f"runs:/{run_id}/model",
            model_name=self.test_model_name
        )
        
        # Load model
        loaded_model = self.registry.load_model_by_version(
            model_name=self.test_model_name,
            version=int(model_version.version),
            device="cpu"
        )
        
        # Verify model is loaded
        self.assertIsNotNone(loaded_model)
        self.assertIsInstance(loaded_model, nn.Module)
    
    def test_load_model_by_stage(self):
        """
        Test loading model by deployment stage.
        
        Requirements:
        - 32.9: Test model loading by stage
        """
        # Register model
        run_id = self._create_test_run_with_model()
        model_version = self.registry.register_model(
            model_uri=f"runs:/{run_id}/model",
            model_name=self.test_model_name
        )
        
        # Transition to Production
        self.registry.transition_model_stage(
            model_name=self.test_model_name,
            version=int(model_version.version),
            stage=ModelRegistry.STAGE_PRODUCTION
        )
        
        # Load production model
        loaded_model = self.registry.load_model_by_stage(
            model_name=self.test_model_name,
            stage=ModelRegistry.STAGE_PRODUCTION,
            device="cpu"
        )
        
        # Verify model is loaded
        self.assertIsNotNone(loaded_model)
        self.assertIsInstance(loaded_model, nn.Module)
    
    def test_invalid_stage_transition(self):
        """Test that invalid stage transitions raise errors."""
        # Register model
        run_id = self._create_test_run_with_model()
        model_version = self.registry.register_model(
            model_uri=f"runs:/{run_id}/model",
            model_name=self.test_model_name
        )
        
        # Try to transition to invalid stage
        with self.assertRaises(ValueError):
            self.registry.transition_model_stage(
                model_name=self.test_model_name,
                version=int(model_version.version),
                stage="InvalidStage"
            )


if __name__ == '__main__':
    unittest.main()
