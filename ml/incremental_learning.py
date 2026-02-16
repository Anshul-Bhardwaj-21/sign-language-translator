"""Incremental learning from user corrections."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import List, Tuple
import pickle

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from tqdm import tqdm

from model import create_model
from preprocess import normalize_landmarks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_corrections(corrections_dir: str) -> List[Tuple[np.ndarray, str]]:
    """
    Load user corrections from directory.
    
    Expected format: .npz files with 'landmarks' and 'corrected_label'
    """
    corrections_path = Path(corrections_dir)
    
    if not corrections_path.exists():
        logger.warning(f"Corrections directory not found: {corrections_dir}")
        return []
    
    corrections = []
    
    for npz_file in corrections_path.glob("*.npz"):
        try:
            data = np.load(npz_file)
            landmarks = data['landmarks']
            label = str(data['corrected_label'])
            corrections.append((landmarks, label))
        except Exception as exc:
            logger.error(f"Failed to load {npz_file}: {exc}")
    
    logger.info(f"Loaded {len(corrections)} corrections")
    return corrections


def load_replay_buffer(
    base_data_dir: str,
    buffer_size: int,
    classes: List[str]
) -> List[Tuple[np.ndarray, str]]:
    """
    Load samples from original training data for replay buffer.
    
    Prevents catastrophic forgetting by mixing old and new data.
    """
    base_path = Path(base_data_dir)
    
    if not base_path.exists():
        logger.warning(f"Base data directory not found: {base_data_dir}")
        return []
    
    replay_samples = []
    samples_per_class = buffer_size // len(classes)
    
    for class_name in classes:
        class_dir = base_path / class_name
        
        if not class_dir.exists():
            continue
        
        npz_files = list(class_dir.glob("*.npz"))
        
        # Randomly sample
        if len(npz_files) > samples_per_class:
            npz_files = np.random.choice(npz_files, samples_per_class, replace=False)
        
        for npz_file in npz_files:
            try:
                data = np.load(npz_file)
                landmarks = data['landmarks']
                replay_samples.append((landmarks, class_name))
            except Exception as exc:
                logger.error(f"Failed to load {npz_file}: {exc}")
    
    logger.info(f"Loaded {len(replay_samples)} replay buffer samples")
    return replay_samples


def prepare_dataset(
    samples: List[Tuple[np.ndarray, str]],
    classes: List[str],
    sequence_length: int
) -> TensorDataset:
    """Prepare dataset from samples."""
    class_to_idx = {cls: idx for idx, cls in enumerate(classes)}
    
    sequences = []
    labels = []
    
    for landmarks, label in samples:
        if label not in class_to_idx:
            logger.warning(f"Unknown class: {label}")
            continue
        
        # Normalize
        landmarks = normalize_landmarks(landmarks)
        
        # Resample to target length
        landmarks = resample_sequence(landmarks, sequence_length)
        
        # Flatten
        landmarks = landmarks.reshape(sequence_length, -1)
        
        sequences.append(landmarks)
        labels.append(class_to_idx[label])
    
    sequences_tensor = torch.tensor(np.array(sequences), dtype=torch.float32)
    labels_tensor = torch.tensor(labels, dtype=torch.long)
    
    return TensorDataset(sequences_tensor, labels_tensor)


def resample_sequence(sequence: np.ndarray, target_length: int) -> np.ndarray:
    """Resample sequence to target length."""
    current_length = sequence.shape[0]
    
    if current_length == target_length:
        return sequence
    
    old_indices = np.linspace(0, current_length - 1, current_length)
    new_indices = np.linspace(0, current_length - 1, target_length)
    
    resampled = np.zeros((target_length, 21, 3))
    
    for lm_idx in range(21):
        for coord_idx in range(3):
            resampled[:, lm_idx, coord_idx] = np.interp(
                new_indices,
                old_indices,
                sequence[:, lm_idx, coord_idx]
            )
    
    return resampled


def fine_tune(
    model: nn.Module,
    dataloader: DataLoader,
    epochs: int,
    lr: float,
    device: torch.device
) -> nn.Module:
    """Fine-tune model on new data."""
    model.train()
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    for epoch in range(1, epochs + 1):
        total_loss = 0.0
        correct = 0
        total = 0
        
        for sequences, labels in tqdm(dataloader, desc=f"Epoch {epoch}/{epochs}"):
            sequences = sequences.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(sequences)
            loss = criterion(outputs, labels)
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
        
        avg_loss = total_loss / len(dataloader)
        accuracy = 100.0 * correct / total
        
        logger.info(f"Epoch {epoch}: Loss={avg_loss:.4f}, Acc={accuracy:.2f}%")
    
    return model


def main():
    parser = argparse.ArgumentParser(description="Incremental learning from corrections")
    parser.add_argument("--base-model", type=str, required=True,
                        help="Path to base model checkpoint")
    parser.add_argument("--corrections-dir", type=str, required=True,
                        help="Directory containing user corrections")
    parser.add_argument("--base-data-dir", type=str, default="ml/datasets/raw",
                        help="Original training data for replay buffer")
    parser.add_argument("--replay-buffer-size", type=int, default=500,
                        help="Number of samples from original data")
    parser.add_argument("--epochs", type=int, default=5,
                        help="Number of fine-tuning epochs")
    parser.add_argument("--lr", type=float, default=0.0001,
                        help="Learning rate for fine-tuning")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--output", type=str, required=True,
                        help="Output path for updated model")
    parser.add_argument("--min-corrections", type=int, default=5,
                        help="Minimum corrections required to trigger training")
    parser.add_argument("--device", type=str, default="auto")
    
    args = parser.parse_args()
    
    # Device selection
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    
    logger.info(f"Using device: {device}")
    
    # Load base model
    logger.info(f"Loading base model from {args.base_model}")
    checkpoint = torch.load(args.base_model, map_location=device)
    
    classes = checkpoint['classes']
    sequence_length = checkpoint['sequence_length']
    model_type = checkpoint.get('model_type', 'conv_lstm')
    hidden_dim = checkpoint.get('hidden_dim', 128)
    
    model = create_model(
        model_type=model_type,
        input_features=63,
        num_classes=len(classes),
        hidden_dim=hidden_dim
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    
    logger.info(f"Model loaded: {len(classes)} classes, seq_len={sequence_length}")
    
    # Load corrections
    corrections = load_corrections(args.corrections_dir)
    
    if len(corrections) < args.min_corrections:
        logger.warning(
            f"Only {len(corrections)} corrections found, "
            f"minimum {args.min_corrections} required. Skipping training."
        )
        return
    
    # Load replay buffer
    replay_samples = load_replay_buffer(
        args.base_data_dir,
        args.replay_buffer_size,
        classes
    )
    
    # Combine corrections and replay buffer
    all_samples = corrections + replay_samples
    logger.info(f"Total training samples: {len(all_samples)}")
    
    # Prepare dataset
    dataset = prepare_dataset(all_samples, classes, sequence_length)
    dataloader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0
    )
    
    # Fine-tune
    logger.info("Starting fine-tuning...")
    model = fine_tune(model, dataloader, args.epochs, args.lr, device)
    
    # Save updated model
    checkpoint['model_state_dict'] = model.state_dict()
    checkpoint['incremental_updates'] = checkpoint.get('incremental_updates', 0) + 1
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    torch.save(checkpoint, args.output)
    
    logger.info(f"✓ Updated model saved to {args.output}")
    logger.info(f"Incremental updates: {checkpoint['incremental_updates']}")


if __name__ == "__main__":
    main()
