#!/usr/bin/env python3
"""
Test script for training pipeline

This script creates a minimal synthetic dataset and tests the training pipeline
to ensure all components work correctly before training on real data.

Usage:
    python backend/models/test_training.py
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

import mlflow
import numpy as np
import torch

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from models.train_model import (
    SignLanguageDataset,
    EarlyStopping,
    ModelTrainer,
    create_model,
    compute_dataset_hash
)


def create_synthetic_dataset(output_dir: str, num_classes: int = 5, samples_per_class: int = 20):
    """
    Create a synthetic dataset for testing.
    
    Args:
        output_dir: Directory to save synthetic data
        num_classes: Number of gesture classes
        samples_per_class: Number of samples per class
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create class directories and samples
    all_samples = []
    
    for class_idx in range(num_classes):
        class_name = f"gesture_{class_idx}"
        class_dir = output_path / class_name
        class_dir.mkdir(exist_ok=True)
        
        for sample_idx in range(samples_per_class):
            # Create synthetic landmark sequence
            # Shape: (60, 126) - 60 frames, 126 features (42 keypoints × 3 coords)
            features = np.random.randn(60, 126).astype(np.float32)
            
            # Add some class-specific pattern (for testing)
            features += class_idx * 0.1
            
            # Save as .npy file
            sample_name = f"sample_{sample_idx:03d}.npy"
            sample_path = class_dir / sample_name
            np.save(sample_path, features)
            
            # Record sample path
            all_samples.append(f"{class_name}/{sample_name}")
    
    return all_samples


def create_split_files(splits_dir: str, all_samples: list, train_ratio: float = 0.7):
    """
    Create train/val/test split files.
    
    Args:
        splits_dir: Directory to save split files
        all_samples: List of all sample paths
        train_ratio: Ratio of training samples
    """
    splits_path = Path(splits_dir)
    splits_path.mkdir(parents=True, exist_ok=True)
    
    # Shuffle samples
    np.random.shuffle(all_samples)
    
    # Split data
    n_samples = len(all_samples)
    n_train = int(n_samples * train_ratio)
    n_val = int(n_samples * 0.15)
    
    train_samples = all_samples[:n_train]
    val_samples = all_samples[n_train:n_train + n_val]
    test_samples = all_samples[n_train + n_val:]
    
    # Write split files
    with open(splits_path / 'train.txt', 'w') as f:
        f.write('\n'.join(train_samples))
    
    with open(splits_path / 'val.txt', 'w') as f:
        f.write('\n'.join(val_samples))
    
    with open(splits_path / 'test.txt', 'w') as f:
        f.write('\n'.join(test_samples))
    
    print(f"Created splits: {len(train_samples)} train, {len(val_samples)} val, {len(test_samples)} test")


def test_dataset():
    """Test SignLanguageDataset class."""
    print("\n" + "="*60)
    print("Testing SignLanguageDataset")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create synthetic data
        data_dir = os.path.join(tmpdir, 'processed')
        splits_dir = os.path.join(tmpdir, 'splits')
        
        all_samples = create_synthetic_dataset(data_dir, num_classes=5, samples_per_class=20)
        create_split_files(splits_dir, all_samples)
        
        # Create dataset
        dataset = SignLanguageDataset(
            data_dir=data_dir,
            split_file=os.path.join(splits_dir, 'train.txt'),
            sequence_length=60
        )
        
        print(f"✓ Dataset created with {len(dataset)} samples")
        print(f"✓ Found {len(dataset.classes)} classes: {dataset.classes}")
        
        # Test loading a sample
        features, label = dataset[0]
        print(f"✓ Sample shape: {features.shape}")
        print(f"✓ Label: {label}")
        
        assert features.shape == (60, 126), f"Expected shape (60, 126), got {features.shape}"
        assert isinstance(label, int), f"Expected int label, got {type(label)}"
        
        print("✓ Dataset test passed!")


def test_early_stopping():
    """Test EarlyStopping class."""
    print("\n" + "="*60)
    print("Testing EarlyStopping")
    print("="*60)
    
    # Test with improving scores
    early_stopping = EarlyStopping(patience=3, min_delta=0.01, mode='max', verbose=False)
    
    scores = [0.5, 0.6, 0.65, 0.66, 0.66, 0.66, 0.66]  # Stops at index 6
    
    for epoch, score in enumerate(scores, 1):
        should_stop = early_stopping(score, epoch)
        if should_stop:
            print(f"✓ Early stopping triggered at epoch {epoch} (expected)")
            break
    
    assert early_stopping.early_stop, "Early stopping should have triggered"
    # Best score is 0.65 because 0.66 doesn't meet min_delta threshold (0.66 - 0.65 = 0.01, not > 0.01)
    assert early_stopping.best_score == 0.65, f"Best score should be 0.65, got {early_stopping.best_score}"
    
    print("✓ Early stopping test passed!")


def test_training_loop():
    """Test complete training loop with synthetic data."""
    print("\n" + "="*60)
    print("Testing Training Loop")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create synthetic data
        data_dir = os.path.join(tmpdir, 'processed')
        splits_dir = os.path.join(tmpdir, 'splits')
        checkpoint_dir = os.path.join(tmpdir, 'checkpoints')
        
        all_samples = create_synthetic_dataset(data_dir, num_classes=5, samples_per_class=20)
        create_split_files(splits_dir, all_samples)
        
        # Create datasets
        train_dataset = SignLanguageDataset(
            data_dir=data_dir,
            split_file=os.path.join(splits_dir, 'train.txt'),
            sequence_length=60
        )
        
        val_dataset = SignLanguageDataset(
            data_dir=data_dir,
            split_file=os.path.join(splits_dir, 'val.txt'),
            sequence_length=60
        )
        
        test_dataset = SignLanguageDataset(
            data_dir=data_dir,
            split_file=os.path.join(splits_dir, 'test.txt'),
            sequence_length=60
        )
        
        # Create data loaders
        train_loader = torch.utils.data.DataLoader(
            train_dataset,
            batch_size=8,
            shuffle=True
        )
        
        val_loader = torch.utils.data.DataLoader(
            val_dataset,
            batch_size=8,
            shuffle=False
        )
        
        test_loader = torch.utils.data.DataLoader(
            test_dataset,
            batch_size=8,
            shuffle=False
        )
        
        print(f"✓ Created data loaders")
        print(f"  Train batches: {len(train_loader)}")
        print(f"  Val batches: {len(val_loader)}")
        print(f"  Test batches: {len(test_loader)}")
        
        # Create model
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = create_model(
            num_classes=len(train_dataset.classes),
            sequence_length=60,
            dropout_rate=0.3,
            device=device
        )
        
        print(f"✓ Created model on device: {device}")
        
        # Create optimizer and loss
        criterion = torch.nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        
        print(f"✓ Created optimizer and loss function")
        
        # Create early stopping
        early_stopping = EarlyStopping(patience=3, min_delta=0.001, mode='max', verbose=False)
        
        # Create trainer
        trainer = ModelTrainer(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device,
            checkpoint_dir=checkpoint_dir,
            early_stopping=early_stopping,
            test_loader=test_loader,
            class_names=train_dataset.classes
        )
        
        print(f"✓ Created trainer")
        
        # Train for a few epochs
        print("\nTraining for 5 epochs (or until early stopping)...")
        trainer.train(num_epochs=5, save_best_only=True)
        
        # Check that checkpoint was saved
        best_model_path = Path(checkpoint_dir) / 'best_model.pth'
        assert best_model_path.exists(), "Best model checkpoint should exist"
        
        print(f"✓ Best model saved: {best_model_path}")
        
        # Check training history
        assert len(trainer.history['train_loss']) > 0, "Training history should not be empty"
        assert len(trainer.history['val_acc']) > 0, "Validation history should not be empty"
        
        print(f"✓ Training history recorded ({len(trainer.history['train_loss'])} epochs)")
        
        # Load checkpoint and verify
        checkpoint = torch.load(best_model_path, map_location=device)
        assert 'model_state_dict' in checkpoint, "Checkpoint should contain model state"
        assert 'optimizer_state_dict' in checkpoint, "Checkpoint should contain optimizer state"
        assert 'best_val_acc' in checkpoint, "Checkpoint should contain best validation accuracy"
        
        print(f"✓ Checkpoint structure verified")
        print(f"  Best validation accuracy: {checkpoint['best_val_acc']:.2f}%")
        
        # Check that training curves were generated
        training_curves_path = Path(checkpoint_dir) / 'training_curves.png'
        assert training_curves_path.exists(), "Training curves plot should exist"
        print(f"✓ Training curves generated: {training_curves_path}")
        
        # Check that confusion matrix was generated
        confusion_matrix_path = Path(checkpoint_dir) / 'confusion_matrix.png'
        assert confusion_matrix_path.exists(), "Confusion matrix plot should exist"
        print(f"✓ Confusion matrix generated: {confusion_matrix_path}")
        
        print("\n✓ Training loop test passed!")


def test_dataset_hash():
    """Test dataset hash computation."""
    print("\n" + "="*60)
    print("Testing Dataset Hash Computation")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create synthetic data
        data_dir = os.path.join(tmpdir, 'processed')
        splits_dir = os.path.join(tmpdir, 'splits')
        
        all_samples = create_synthetic_dataset(data_dir, num_classes=3, samples_per_class=10)
        create_split_files(splits_dir, all_samples)
        
        # Compute hash
        hash1 = compute_dataset_hash(data_dir, splits_dir)
        print(f"✓ Computed dataset hash: {hash1}")
        
        # Compute again - should be same
        hash2 = compute_dataset_hash(data_dir, splits_dir)
        assert hash1 == hash2, "Hash should be deterministic"
        print(f"✓ Hash is deterministic")
        
        # Modify data - hash should change
        new_samples = create_synthetic_dataset(data_dir, num_classes=3, samples_per_class=11)
        create_split_files(splits_dir, new_samples)
        hash3 = compute_dataset_hash(data_dir, splits_dir)
        assert hash1 != hash3, "Hash should change when data changes"
        print(f"✓ Hash changes with data: {hash3}")
        
        print("\n✓ Dataset hash test passed!")


def main():
    """Run all tests."""
    print("="*60)
    print("Training Pipeline Test Suite")
    print("="*60)
    
    # Set random seed for reproducibility
    np.random.seed(42)
    torch.manual_seed(42)
    
    try:
        # Run tests
        test_dataset()
        test_early_stopping()
        test_training_loop()
        
        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60)
        print("\nThe training pipeline is working correctly.")
        print("You can now train on real data using:")
        print("  python backend/models/train_model.py")
        
    except Exception as e:
        print("\n" + "="*60)
        print("✗ Test failed!")
        print("="*60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
