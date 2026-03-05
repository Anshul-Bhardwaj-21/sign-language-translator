#!/usr/bin/env python3
"""
Sign Language Model Training Script

This script implements a comprehensive training pipeline for the CNN+LSTM sign language
recognition model with the following features:

1. Data loading from preprocessed datasets with 70/15/15 train/val/test split
2. Adam optimizer with learning rate 0.001
3. CrossEntropyLoss for classification
4. Early stopping with patience=10, min_delta=0.001
5. Model checkpoint saving (best model only)
6. Training progress logging
7. CLI interface for hyperparameter configuration

Requirements: 30.3, 30.5, 30.6, 30.7
Phase: MVP

Usage:
    # Train with default configuration
    python train_model.py
    
    # Train with custom hyperparameters
    python train_model.py --learning-rate 0.0005 --batch-size 64 --epochs 150
    
    # Resume training from checkpoint
    python train_model.py --resume checkpoints/best_model.pth

Author: AI-Powered Meeting Platform Team
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import mlflow
import mlflow.pytorch
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import yaml
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score
import seaborn as sns

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from models.sign_language_model import CNNLSTMSignLanguageModel, create_model


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SignLanguageDataset(Dataset):
    """
    PyTorch Dataset for loading preprocessed sign language data.
    
    Loads .npy files containing hand landmark sequences and their corresponding labels.
    Each sample is a tensor of shape (sequence_length, num_keypoints * coordinates).
    
    Args:
        data_dir: Path to processed dataset directory
        split_file: Path to split file (train.txt, val.txt, or test.txt)
        sequence_length: Fixed sequence length (default: 60)
        transform: Optional transform to apply to samples
    """
    
    def __init__(
        self,
        data_dir: str,
        split_file: str,
        sequence_length: int = 60,
        transform=None
    ):
        self.data_dir = Path(data_dir)
        self.sequence_length = sequence_length
        self.transform = transform
        
        # Load split file
        with open(split_file, 'r') as f:
            self.samples = [line.strip() for line in f if line.strip()]
        
        # Build class to index mapping
        self.classes = sorted(set(self._get_class_from_path(s) for s in self.samples))
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
        
        logger.info(f"Loaded {len(self.samples)} samples from {split_file}")
        logger.info(f"Found {len(self.classes)} classes: {self.classes}")
    
    def _get_class_from_path(self, sample_path: str) -> str:
        """Extract class name from sample path."""
        # Expected format: class_name/sample_001.npy
        return sample_path.split('/')[0]
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        """
        Load a single sample.
        
        Returns:
            Tuple of (features, label) where:
                features: Tensor of shape (sequence_length, 126)
                label: Integer class index
        """
        sample_path = self.samples[idx]
        full_path = self.data_dir / sample_path
        
        # Load preprocessed features
        try:
            features = np.load(full_path)  # Shape: (seq_len, 126)
        except FileNotFoundError:
            logger.error(f"Sample not found: {full_path}")
            # Return zeros as fallback
            features = np.zeros((self.sequence_length, 126), dtype=np.float32)
        
        # Ensure correct shape
        if features.shape[0] != self.sequence_length:
            # Pad or truncate to fixed length
            if features.shape[0] < self.sequence_length:
                # Pad with zeros
                padding = np.zeros((self.sequence_length - features.shape[0], 126), dtype=np.float32)
                features = np.vstack([features, padding])
            else:
                # Truncate
                features = features[:self.sequence_length]
        
        # Get label
        class_name = self._get_class_from_path(sample_path)
        label = self.class_to_idx[class_name]
        
        # Convert to tensors
        features = torch.from_numpy(features).float()
        
        # Apply transform if provided
        if self.transform:
            features = self.transform(features)
        
        return features, label


class EarlyStopping:
    """
    Early stopping to stop training when validation metric stops improving.
    
    Args:
        patience: Number of epochs to wait before stopping (default: 10)
        min_delta: Minimum change to qualify as improvement (default: 0.001)
        mode: 'min' for loss, 'max' for accuracy (default: 'max')
        verbose: Print messages (default: True)
    
    Requirements:
        - 30.6: Implements early stopping with patience=10, min_delta=0.001
    """
    
    def __init__(
        self,
        patience: int = 10,
        min_delta: float = 0.001,
        mode: str = 'max',
        verbose: bool = True
    ):
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.verbose = verbose
        
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        self.best_epoch = 0
        
        # Set comparison function based on mode
        if mode == 'max':
            self.is_better = lambda new, best: new > best + min_delta
        else:
            self.is_better = lambda new, best: new < best - min_delta
    
    def __call__(self, score: float, epoch: int) -> bool:
        """
        Check if training should stop.
        
        Args:
            score: Current validation metric value
            epoch: Current epoch number
        
        Returns:
            True if training should stop, False otherwise
        """
        if self.best_score is None:
            self.best_score = score
            self.best_epoch = epoch
            return False
        
        if self.is_better(score, self.best_score):
            # Improvement detected
            self.best_score = score
            self.best_epoch = epoch
            self.counter = 0
            if self.verbose:
                logger.info(f"Validation metric improved to {score:.4f}")
        else:
            # No improvement
            self.counter += 1
            if self.verbose:
                logger.info(
                    f"No improvement for {self.counter}/{self.patience} epochs "
                    f"(best: {self.best_score:.4f} at epoch {self.best_epoch})"
                )
            
            if self.counter >= self.patience:
                self.early_stop = True
                if self.verbose:
                    logger.info(f"Early stopping triggered after {self.patience} epochs without improvement")
        
        return self.early_stop


class ModelTrainer:
    """
    Trainer class for sign language recognition model.
    
    Handles training loop, validation, checkpointing, and logging.
    
    Args:
        model: PyTorch model to train
        train_loader: DataLoader for training data
        val_loader: DataLoader for validation data
        criterion: Loss function
        optimizer: Optimizer
        device: Device to train on ('cuda' or 'cpu')
        checkpoint_dir: Directory to save checkpoints
        early_stopping: EarlyStopping instance (optional)
        test_loader: DataLoader for test data (optional)
        class_names: List of class names for confusion matrix
    """
    
    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        criterion: nn.Module,
        optimizer: optim.Optimizer,
        device: str,
        checkpoint_dir: str = 'checkpoints',
        early_stopping: Optional[EarlyStopping] = None,
        test_loader: Optional[DataLoader] = None,
        class_names: Optional[List[str]] = None
    ):
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.test_loader = test_loader
        self.criterion = criterion
        self.optimizer = optimizer
        self.device = device
        self.checkpoint_dir = Path(checkpoint_dir)
        self.early_stopping = early_stopping
        self.class_names = class_names or []
        
        # Create checkpoint directory
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Training history
        self.history = {
            'train_loss': [],
            'train_acc': [],
            'val_loss': [],
            'val_acc': [],
            'learning_rates': []
        }
        
        # Best model tracking
        self.best_val_acc = 0.0
        self.best_epoch = 0
    
    def train_epoch(self, epoch: int) -> Tuple[float, float]:
        """
        Train for one epoch.
        
        Args:
            epoch: Current epoch number
        
        Returns:
            Tuple of (average_loss, accuracy)
        """
        self.model.train()
        
        running_loss = 0.0
        correct = 0
        total = 0
        
        for batch_idx, (features, labels) in enumerate(self.train_loader):
            # Move data to device
            features = features.to(self.device)
            labels = labels.to(self.device)
            
            # Zero gradients
            self.optimizer.zero_grad()
            
            # Forward pass
            outputs = self.model(features)
            loss = self.criterion(outputs, labels)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping (optional, helps with stability)
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            # Update weights
            self.optimizer.step()
            
            # Statistics
            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            
            # Log progress
            if (batch_idx + 1) % 10 == 0:
                logger.info(
                    f"Epoch {epoch} [{batch_idx + 1}/{len(self.train_loader)}] "
                    f"Loss: {loss.item():.4f} "
                    f"Acc: {100.0 * correct / total:.2f}%"
                )
        
        avg_loss = running_loss / len(self.train_loader)
        accuracy = 100.0 * correct / total
        
        return avg_loss, accuracy
    
    def validate(self) -> Tuple[float, float]:
        """
        Validate the model.
        
        Returns:
            Tuple of (average_loss, accuracy)
        """
        self.model.eval()
        
        running_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for features, labels in self.val_loader:
                # Move data to device
                features = features.to(self.device)
                labels = labels.to(self.device)
                
                # Forward pass
                outputs = self.model(features)
                loss = self.criterion(outputs, labels)
                
                # Statistics
                running_loss += loss.item()
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()
        
        avg_loss = running_loss / len(self.val_loader)
        accuracy = 100.0 * correct / total
        
        return avg_loss, accuracy
    
    def evaluate_test_set(self) -> Dict[str, float]:
        """
        Evaluate the model on test set and compute detailed metrics.
        
        Returns:
            Dictionary with test metrics (accuracy, precision, recall, f1)
        """
        if self.test_loader is None:
            logger.warning("No test loader provided, skipping test evaluation")
            return {}
        
        self.model.eval()
        
        all_predictions = []
        all_labels = []
        running_loss = 0.0
        
        with torch.no_grad():
            for features, labels in self.test_loader:
                # Move data to device
                features = features.to(self.device)
                labels = labels.to(self.device)
                
                # Forward pass
                outputs = self.model(features)
                loss = self.criterion(outputs, labels)
                
                # Get predictions
                _, predicted = outputs.max(1)
                
                # Collect predictions and labels
                all_predictions.extend(predicted.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
                running_loss += loss.item()
        
        # Convert to numpy arrays
        all_predictions = np.array(all_predictions)
        all_labels = np.array(all_labels)
        
        # Calculate metrics
        accuracy = 100.0 * (all_predictions == all_labels).sum() / len(all_labels)
        precision = precision_score(all_labels, all_predictions, average='weighted', zero_division=0)
        recall = recall_score(all_labels, all_predictions, average='weighted', zero_division=0)
        f1 = f1_score(all_labels, all_predictions, average='weighted', zero_division=0)
        avg_loss = running_loss / len(self.test_loader)
        
        metrics = {
            'test_loss': avg_loss,
            'test_accuracy': accuracy,
            'test_precision': precision,
            'test_recall': recall,
            'test_f1_score': f1
        }
        
        logger.info("="*60)
        logger.info("Test Set Evaluation:")
        logger.info(f"  Loss: {avg_loss:.4f}")
        logger.info(f"  Accuracy: {accuracy:.2f}%")
        logger.info(f"  Precision: {precision:.4f}")
        logger.info(f"  Recall: {recall:.4f}")
        logger.info(f"  F1 Score: {f1:.4f}")
        logger.info("="*60)
        
        return metrics, all_predictions, all_labels
    
    def plot_confusion_matrix(self, predictions: np.ndarray, labels: np.ndarray, save_path: str):
        """
        Generate and save confusion matrix plot.
        
        Args:
            predictions: Predicted labels
            labels: True labels
            save_path: Path to save the plot
        """
        # Compute confusion matrix
        cm = confusion_matrix(labels, predictions)
        
        # Create figure
        plt.figure(figsize=(12, 10))
        
        # Plot confusion matrix
        sns.heatmap(
            cm,
            annot=True,
            fmt='d',
            cmap='Blues',
            xticklabels=self.class_names if self.class_names else range(len(cm)),
            yticklabels=self.class_names if self.class_names else range(len(cm))
        )
        
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        
        # Save figure
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved confusion matrix: {save_path}")
    
    def plot_training_curves(self, save_path: str):
        """
        Generate and save training curves plot.
        
        Args:
            save_path: Path to save the plot
        """
        epochs = range(1, len(self.history['train_loss']) + 1)
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Plot loss
        ax1.plot(epochs, self.history['train_loss'], 'b-', label='Training Loss', linewidth=2)
        ax1.plot(epochs, self.history['val_loss'], 'r-', label='Validation Loss', linewidth=2)
        ax1.set_title('Training and Validation Loss', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Epoch', fontsize=12)
        ax1.set_ylabel('Loss', fontsize=12)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # Plot accuracy
        ax2.plot(epochs, self.history['train_acc'], 'b-', label='Training Accuracy', linewidth=2)
        ax2.plot(epochs, self.history['val_acc'], 'r-', label='Validation Accuracy', linewidth=2)
        ax2.set_title('Training and Validation Accuracy', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Epoch', fontsize=12)
        ax2.set_ylabel('Accuracy (%)', fontsize=12)
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save figure
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved training curves: {save_path}")
    
    def save_checkpoint(self, epoch: int, is_best: bool = False):
        """
        Save model checkpoint.
        
        Args:
            epoch: Current epoch number
            is_best: Whether this is the best model so far
        
        Requirements:
            - 30.7: Saves model checkpoints after each epoch that improves validation accuracy
        """
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'best_val_acc': self.best_val_acc,
            'history': self.history,
            'model_config': self.model.get_config()
        }
        
        # Save latest checkpoint
        checkpoint_path = self.checkpoint_dir / f'checkpoint_epoch_{epoch}.pth'
        torch.save(checkpoint, checkpoint_path)
        logger.info(f"Saved checkpoint: {checkpoint_path}")
        
        # Save best model
        if is_best:
            best_path = self.checkpoint_dir / 'best_model.pth'
            torch.save(checkpoint, best_path)
            logger.info(f"Saved best model: {best_path}")
    
    def train(self, num_epochs: int, save_best_only: bool = True):
        """
        Train the model for multiple epochs with MLflow logging.
        
        Args:
            num_epochs: Number of epochs to train
            save_best_only: Only save checkpoints when validation improves
        
        Requirements:
            - 30.3: Uses CrossEntropyLoss for classification
            - 30.5: Implements 70/15/15 train/val/test split (handled by data loading)
            - 30.6: Implements early stopping with patience=10, min_delta=0.001
            - 30.7: Saves best model checkpoint
            - 51.4: Logs training curves (loss, accuracy per epoch)
        """
        logger.info("="*60)
        logger.info("Starting Training")
        logger.info("="*60)
        logger.info(f"Device: {self.device}")
        logger.info(f"Number of epochs: {num_epochs}")
        logger.info(f"Training samples: {len(self.train_loader.dataset)}")
        logger.info(f"Validation samples: {len(self.val_loader.dataset)}")
        if self.test_loader:
            logger.info(f"Test samples: {len(self.test_loader.dataset)}")
        logger.info(f"Batch size: {self.train_loader.batch_size}")
        logger.info("="*60)
        
        start_time = time.time()
        
        for epoch in range(1, num_epochs + 1):
            epoch_start = time.time()
            
            # Train
            train_loss, train_acc = self.train_epoch(epoch)
            
            # Validate
            val_loss, val_acc = self.validate()
            
            # Update history
            self.history['train_loss'].append(train_loss)
            self.history['train_acc'].append(train_acc)
            self.history['val_loss'].append(val_loss)
            self.history['val_acc'].append(val_acc)
            self.history['learning_rates'].append(self.optimizer.param_groups[0]['lr'])
            
            # Log metrics to MLflow (Requirement 51.4)
            mlflow.log_metrics({
                'train_loss': train_loss,
                'train_accuracy': train_acc,
                'val_loss': val_loss,
                'val_accuracy': val_acc,
                'learning_rate': self.optimizer.param_groups[0]['lr']
            }, step=epoch)
            
            # Log epoch summary
            epoch_time = time.time() - epoch_start
            logger.info("="*60)
            logger.info(f"Epoch {epoch}/{num_epochs} Summary:")
            logger.info(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
            logger.info(f"  Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")
            logger.info(f"  Time: {epoch_time:.2f}s")
            logger.info("="*60)
            
            # Check if best model
            is_best = val_acc > self.best_val_acc
            if is_best:
                self.best_val_acc = val_acc
                self.best_epoch = epoch
            
            # Save checkpoint
            if not save_best_only or is_best:
                self.save_checkpoint(epoch, is_best)
            
            # Early stopping check
            if self.early_stopping:
                if self.early_stopping(val_acc, epoch):
                    logger.info(f"Early stopping triggered at epoch {epoch}")
                    break
        
        # Training complete
        total_time = time.time() - start_time
        logger.info("="*60)
        logger.info("Training Complete!")
        logger.info(f"Total time: {total_time / 60:.2f} minutes")
        logger.info(f"Best validation accuracy: {self.best_val_acc:.2f}% at epoch {self.best_epoch}")
        logger.info("="*60)
        
        # Log final metrics to MLflow
        mlflow.log_metrics({
            'best_val_accuracy': self.best_val_acc,
            'best_epoch': self.best_epoch,
            'total_training_time_minutes': total_time / 60
        })
        
        # Evaluate on test set if available
        if self.test_loader:
            logger.info("Evaluating on test set...")
            test_metrics, predictions, labels = self.evaluate_test_set()
            
            # Log test metrics to MLflow (Requirement 51.4)
            mlflow.log_metrics(test_metrics)
            
            # Generate and log confusion matrix (Requirement 51.13)
            confusion_matrix_path = self.checkpoint_dir / 'confusion_matrix.png'
            self.plot_confusion_matrix(predictions, labels, str(confusion_matrix_path))
            mlflow.log_artifact(str(confusion_matrix_path))
        
        # Generate and log training curves (Requirement 51.13)
        training_curves_path = self.checkpoint_dir / 'training_curves.png'
        self.plot_training_curves(str(training_curves_path))
        mlflow.log_artifact(str(training_curves_path))
        
        # Save training history
        history_path = self.checkpoint_dir / 'training_history.json'
        with open(history_path, 'w') as f:
            json.dump(self.history, f, indent=2)
        logger.info(f"Saved training history: {history_path}")
        mlflow.log_artifact(str(history_path))


def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def compute_dataset_hash(data_dir: str, splits_dir: str) -> str:
    """
    Compute hash of dataset for reproducibility tracking.
    
    Args:
        data_dir: Path to processed dataset directory
        splits_dir: Path to dataset splits directory
    
    Returns:
        SHA256 hash of dataset version
    
    Requirements:
        - 51.2: Track dataset version hash for reproducibility
    """
    hasher = hashlib.sha256()
    
    # Hash split files
    for split_file in ['train.txt', 'val.txt', 'test.txt']:
        split_path = os.path.join(splits_dir, split_file)
        if os.path.exists(split_path):
            with open(split_path, 'rb') as f:
                hasher.update(f.read())
    
    # Hash dataset directory structure
    data_path = Path(data_dir)
    if data_path.exists():
        # Get sorted list of all files
        all_files = sorted(data_path.rglob('*.npy'))
        for file_path in all_files[:100]:  # Sample first 100 files for efficiency
            hasher.update(str(file_path.relative_to(data_path)).encode())
            hasher.update(str(file_path.stat().st_size).encode())
    
    return hasher.hexdigest()


def load_mlflow_config(config_path: str = 'backend/mlflow_config.yaml') -> Dict:
    """
    Load MLflow configuration from YAML file.
    
    Args:
        config_path: Path to MLflow configuration file
    
    Returns:
        MLflow configuration dictionary
    """
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            mlflow_config = yaml.safe_load(f)
        return mlflow_config
    else:
        logger.warning(f"MLflow config not found: {config_path}, using defaults")
        return {
            'server': {'tracking_uri': 'http://localhost:5000'},
            'experiments': {
                'sign_language_asl_baseline': {
                    'name': 'sign-language-asl-baseline',
                    'description': 'CNN+LSTM baseline model for ASL recognition'
                }
            }
        }


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Train sign language recognition model',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Data arguments
    parser.add_argument(
        '--data-dir',
        type=str,
        default='backend/storage/datasets/v1.0.0/processed',
        help='Path to processed dataset directory'
    )
    parser.add_argument(
        '--splits-dir',
        type=str,
        default='backend/storage/datasets/v1.0.0/splits',
        help='Path to dataset splits directory'
    )
    
    # Model arguments
    parser.add_argument(
        '--config',
        type=str,
        default='backend/models/model_config.yaml',
        help='Path to model configuration file'
    )
    parser.add_argument(
        '--num-classes',
        type=int,
        default=None,
        help='Number of gesture classes (overrides config)'
    )
    
    # Training arguments
    parser.add_argument(
        '--learning-rate',
        type=float,
        default=0.001,
        help='Learning rate for Adam optimizer'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for training'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=100,
        help='Number of training epochs'
    )
    parser.add_argument(
        '--patience',
        type=int,
        default=10,
        help='Early stopping patience'
    )
    parser.add_argument(
        '--min-delta',
        type=float,
        default=0.001,
        help='Early stopping minimum delta'
    )
    
    # Checkpoint arguments
    parser.add_argument(
        '--checkpoint-dir',
        type=str,
        default='backend/models/checkpoints',
        help='Directory to save checkpoints'
    )
    parser.add_argument(
        '--resume',
        type=str,
        default=None,
        help='Path to checkpoint to resume from'
    )
    parser.add_argument(
        '--save-best-only',
        action='store_true',
        default=True,
        help='Only save checkpoints when validation improves'
    )
    
    # Hardware arguments
    parser.add_argument(
        '--device',
        type=str,
        default='auto',
        choices=['auto', 'cuda', 'cpu'],
        help='Device to train on'
    )
    parser.add_argument(
        '--num-workers',
        type=int,
        default=4,
        help='Number of data loading workers'
    )
    
    # Logging arguments
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    return parser.parse_args()


def main():
    """Main training function with MLflow integration."""
    # Parse arguments
    args = parse_args()
    
    # Set logging level
    logger.setLevel(getattr(logging, args.log_level))
    
    # Load configuration
    if os.path.exists(args.config):
        config = load_config(args.config)
        logger.info(f"Loaded configuration from {args.config}")
    else:
        logger.warning(f"Config file not found: {args.config}, using defaults")
        config = {}
    
    # Load MLflow configuration (Requirement 51.9)
    mlflow_config = load_mlflow_config()
    
    # Set MLflow tracking URI (Sub-task 1)
    tracking_uri = mlflow_config.get('server', {}).get('tracking_uri', 'http://localhost:5000')
    mlflow.set_tracking_uri(tracking_uri)
    logger.info(f"MLflow tracking URI: {tracking_uri}")
    
    # Set experiment name (Sub-task 2)
    experiment_config = mlflow_config.get('experiments', {}).get('sign_language_asl_baseline', {})
    experiment_name = experiment_config.get('name', 'sign-language-asl-baseline')
    mlflow.set_experiment(experiment_name)
    logger.info(f"MLflow experiment: {experiment_name}")
    
    # Determine device
    if args.device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    else:
        device = args.device
    logger.info(f"Using device: {device}")
    
    # Set random seeds for reproducibility (Requirement 51.3)
    seed = config.get('reproducibility', {}).get('seed', 42)
    torch.manual_seed(seed)
    np.random.seed(seed)
    if device == 'cuda':
        torch.cuda.manual_seed(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    
    # Create datasets
    logger.info("Loading datasets...")
    train_dataset = SignLanguageDataset(
        data_dir=args.data_dir,
        split_file=os.path.join(args.splits_dir, 'train.txt'),
        sequence_length=config.get('model', {}).get('input', {}).get('sequence_length', 60)
    )
    
    val_dataset = SignLanguageDataset(
        data_dir=args.data_dir,
        split_file=os.path.join(args.splits_dir, 'val.txt'),
        sequence_length=config.get('model', {}).get('input', {}).get('sequence_length', 60)
    )
    
    # Load test dataset if available
    test_split_path = os.path.join(args.splits_dir, 'test.txt')
    test_dataset = None
    if os.path.exists(test_split_path):
        test_dataset = SignLanguageDataset(
            data_dir=args.data_dir,
            split_file=test_split_path,
            sequence_length=config.get('model', {}).get('input', {}).get('sequence_length', 60)
        )
    
    # Determine number of classes
    num_classes = args.num_classes or len(train_dataset.classes)
    logger.info(f"Number of classes: {num_classes}")
    logger.info(f"Classes: {train_dataset.classes}")
    
    # Compute dataset hash (Requirement 51.2)
    dataset_hash = compute_dataset_hash(args.data_dir, args.splits_dir)
    logger.info(f"Dataset hash: {dataset_hash}")
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=(device == 'cuda')
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=(device == 'cuda')
    )
    
    test_loader = None
    if test_dataset:
        test_loader = DataLoader(
            test_dataset,
            batch_size=args.batch_size,
            shuffle=False,
            num_workers=args.num_workers,
            pin_memory=(device == 'cuda')
        )
    
    # Create model
    logger.info("Creating model...")
    model = create_model(
        num_classes=num_classes,
        sequence_length=config.get('model', {}).get('input', {}).get('sequence_length', 60),
        dropout_rate=config.get('model', {}).get('cnn', {}).get('layers', [{}])[0].get('dropout', 0.3),
        device=device
    )
    
    # Print model info
    total_params, trainable_params = model.count_parameters()
    logger.info(f"Model parameters: {total_params:,} (trainable: {trainable_params:,})")
    logger.info(f"Model size: {model.get_model_size_mb():.2f} MB")
    
    # Create loss function (Requirement 30.3)
    criterion = nn.CrossEntropyLoss()
    
    # Create optimizer (Requirement 30.5 - Adam with lr=0.001)
    optimizer = optim.Adam(
        model.parameters(),
        lr=args.learning_rate,
        betas=(0.9, 0.999),
        eps=1e-8
    )
    
    # Resume from checkpoint if specified
    start_epoch = 1
    if args.resume and os.path.exists(args.resume):
        logger.info(f"Resuming from checkpoint: {args.resume}")
        checkpoint = torch.load(args.resume, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        logger.info(f"Resumed from epoch {checkpoint['epoch']}")
    
    # Create early stopping (Requirement 30.6)
    early_stopping = EarlyStopping(
        patience=args.patience,
        min_delta=args.min_delta,
        mode='max',
        verbose=True
    )
    
    # Start MLflow run (Sub-task 3)
    run_name = f"cnn-lstm-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    with mlflow.start_run(run_name=run_name):
        logger.info(f"Started MLflow run: {run_name}")
        
        # Log hyperparameters (Sub-task 4, Requirement 51.1)
        mlflow.log_params({
            'learning_rate': args.learning_rate,
            'batch_size': args.batch_size,
            'epochs': args.epochs,
            'optimizer': 'Adam',
            'loss_function': 'CrossEntropyLoss',
            'early_stopping_patience': args.patience,
            'early_stopping_min_delta': args.min_delta,
            'num_classes': num_classes,
            'sequence_length': config.get('model', {}).get('input', {}).get('sequence_length', 60),
            'model_architecture': 'CNN+LSTM',
            'dropout_rate': config.get('model', {}).get('cnn', {}).get('layers', [{}])[0].get('dropout', 0.3),
            'device': device,
            'num_workers': args.num_workers,
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'model_size_mb': model.get_model_size_mb()
        })
        
        # Log dataset information (Sub-task 5, Requirement 51.2)
        mlflow.log_params({
            'dataset_hash': dataset_hash,
            'dataset_version': 'v1.0.0',  # Could be extracted from path
            'train_samples': len(train_dataset),
            'val_samples': len(val_dataset),
            'test_samples': len(test_dataset) if test_dataset else 0,
            'data_dir': args.data_dir
        })
        
        # Log random seeds (Sub-task 6, Requirement 51.3)
        mlflow.log_params({
            'random_seed': seed,
            'torch_seed': seed,
            'numpy_seed': seed,
            'cuda_deterministic': device == 'cuda'
        })
        
        # Log environment information (Requirement 51.12)
        mlflow.log_params({
            'python_version': sys.version.split()[0],
            'pytorch_version': torch.__version__,
            'cuda_available': torch.cuda.is_available(),
            'cuda_version': torch.version.cuda if torch.cuda.is_available() else 'N/A',
            'gpu_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'
        })
        
        # Log experiment tags
        mlflow.set_tags(experiment_config.get('tags', {}))
        mlflow.set_tag('run_type', 'training')
        mlflow.set_tag('model_type', 'cnn-lstm')
        
        # Create trainer
        trainer = ModelTrainer(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device,
            checkpoint_dir=args.checkpoint_dir,
            early_stopping=early_stopping,
            test_loader=test_loader,
            class_names=train_dataset.classes
        )
        
        # Train model (Sub-tasks 7, 8, 9 handled in trainer.train())
        trainer.train(
            num_epochs=args.epochs,
            save_best_only=args.save_best_only
        )
        
        # Log model with MLflow (Sub-task 10, Requirement 51.13)
        best_model_path = Path(args.checkpoint_dir) / 'best_model.pth'
        if best_model_path.exists():
            # Load best model
            checkpoint = torch.load(best_model_path, map_location=device)
            model.load_state_dict(checkpoint['model_state_dict'])
            
            # Log model
            mlflow.pytorch.log_model(
                model,
                "model",
                registered_model_name="sign-language-asl"
            )
            logger.info("Logged model to MLflow")
            
            # Log model config as artifact
            model_config_path = Path(args.checkpoint_dir) / 'model_config.yaml'
            with open(model_config_path, 'w') as f:
                yaml.dump(model.get_config(), f)
            mlflow.log_artifact(str(model_config_path))
        
        logger.info(f"MLflow run completed: {mlflow.active_run().info.run_id}")
    
    logger.info("Training script completed successfully!")


if __name__ == '__main__':
    main()
