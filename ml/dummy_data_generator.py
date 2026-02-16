"""Generate synthetic landmark data for testing ML pipeline."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import numpy as np
from tqdm import tqdm


def generate_gesture_sequence(
    gesture_type: str,
    sequence_length: int = 24,
    num_landmarks: int = 21
) -> np.ndarray:
    """
    Generate synthetic hand landmark sequence for a gesture.
    
    Each gesture has characteristic patterns:
    - HELLO: Waving motion (oscillating X coordinate)
    - YES: Nodding motion (oscillating Y coordinate)
    - NO: Shaking motion (oscillating X coordinate, faster)
    - OK: Pinch gesture (thumb and index close)
    - STOP: Open palm (fingers spread)
    - POINT: Index finger extended
    - THUMBS_UP: Thumb extended upward
    - FIST: All fingers closed
    - PEACE: Index and middle fingers extended
    - WAVE: Large waving motion
    
    Args:
        gesture_type: Type of gesture to generate
        sequence_length: Number of frames
        num_landmarks: Number of hand landmarks (21 for MediaPipe)
    
    Returns:
        Landmarks array of shape (sequence_length, num_landmarks, 3)
    """
    # Base hand pose (neutral open palm)
    base_landmarks = np.array([
        [0.0, 0.0, 0.0],      # 0: Wrist
        [0.1, -0.1, 0.0],     # 1: Thumb CMC
        [0.15, -0.15, 0.0],   # 2: Thumb MCP
        [0.18, -0.18, 0.0],   # 3: Thumb IP
        [0.2, -0.2, 0.0],     # 4: Thumb tip
        [0.1, 0.0, 0.0],      # 5: Index MCP
        [0.15, 0.1, 0.0],     # 6: Index PIP
        [0.18, 0.15, 0.0],    # 7: Index DIP
        [0.2, 0.2, 0.0],      # 8: Index tip
        [0.05, 0.0, 0.0],     # 9: Middle MCP
        [0.08, 0.12, 0.0],    # 10: Middle PIP
        [0.1, 0.18, 0.0],     # 11: Middle DIP
        [0.12, 0.22, 0.0],    # 12: Middle tip
        [0.0, 0.0, 0.0],      # 13: Ring MCP
        [0.0, 0.12, 0.0],     # 14: Ring PIP
        [0.0, 0.18, 0.0],     # 15: Ring DIP
        [0.0, 0.22, 0.0],     # 16: Ring tip
        [-0.05, 0.0, 0.0],    # 17: Pinky MCP
        [-0.08, 0.1, 0.0],    # 18: Pinky PIP
        [-0.1, 0.15, 0.0],    # 19: Pinky DIP
        [-0.12, 0.18, 0.0],   # 20: Pinky tip
    ])
    
    sequence = np.zeros((sequence_length, num_landmarks, 3))
    
    for t in range(sequence_length):
        frame = base_landmarks.copy()
        
        # Apply gesture-specific transformations
        if gesture_type == "HELLO":
            # Waving motion
            wave_offset = 0.1 * np.sin(2 * np.pi * t / sequence_length * 3)
            frame[:, 0] += wave_offset
        
        elif gesture_type == "YES":
            # Nodding motion
            nod_offset = 0.08 * np.sin(2 * np.pi * t / sequence_length * 2)
            frame[:, 1] += nod_offset
        
        elif gesture_type == "NO":
            # Shaking motion (faster)
            shake_offset = 0.12 * np.sin(2 * np.pi * t / sequence_length * 4)
            frame[:, 0] += shake_offset
        
        elif gesture_type == "OK":
            # Pinch gesture - bring thumb and index together
            frame[4, 0] = frame[8, 0]  # Thumb tip to index tip X
            frame[4, 1] = frame[8, 1]  # Thumb tip to index tip Y
        
        elif gesture_type == "STOP":
            # Open palm - spread fingers more
            frame[4:, 0] *= 1.3  # Spread fingers
            frame[4:, 1] *= 1.2
        
        elif gesture_type == "POINT":
            # Index finger extended, others closed
            frame[12:, 1] *= 0.3  # Close middle, ring, pinky
            frame[4, 1] *= 0.3    # Close thumb
        
        elif gesture_type == "THUMBS_UP":
            # Thumb up, others closed
            frame[4, 1] = 0.3  # Thumb up
            frame[8:, 1] *= 0.2  # Close other fingers
        
        elif gesture_type == "FIST":
            # All fingers closed
            frame[4:, 1] *= 0.2
            frame[4:, 0] *= 0.5
        
        elif gesture_type == "PEACE":
            # Index and middle extended, others closed
            frame[16:, 1] *= 0.3  # Close ring and pinky
            frame[4, 1] *= 0.3    # Close thumb
        
        elif gesture_type == "WAVE":
            # Large waving motion
            wave_offset = 0.15 * np.sin(2 * np.pi * t / sequence_length * 2)
            frame[:, 0] += wave_offset
            frame[:, 1] += 0.05 * np.cos(2 * np.pi * t / sequence_length * 2)
        
        # Add small random noise for realism
        noise = np.random.normal(0, 0.005, frame.shape)
        frame += noise
        
        sequence[t] = frame
    
    return sequence


def generate_dataset(
    output_dir: str,
    num_classes: int = 10,
    samples_per_class: int = 50,
    sequence_length: int = 24
):
    """
    Generate complete synthetic dataset.
    
    Args:
        output_dir: Directory to save dataset
        num_classes: Number of gesture classes
        samples_per_class: Number of samples per class
        sequence_length: Frames per sequence
    """
    gesture_types = [
        "HELLO", "YES", "NO", "OK", "STOP",
        "POINT", "THUMBS_UP", "FIST", "PEACE", "WAVE"
    ]
    
    # Use only requested number of classes
    gesture_types = gesture_types[:num_classes]
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating dataset with {num_classes} classes, {samples_per_class} samples each")
    print(f"Output directory: {output_path}")
    
    for gesture_type in gesture_types:
        class_dir = output_path / gesture_type
        class_dir.mkdir(exist_ok=True)
        
        print(f"\nGenerating {gesture_type}...")
        
        for sample_idx in tqdm(range(samples_per_class)):
            # Generate sequence
            landmarks = generate_gesture_sequence(
                gesture_type,
                sequence_length=sequence_length
            )
            
            # Add variation by slightly modifying sequence length
            if np.random.rand() > 0.5:
                variation = np.random.randint(-3, 4)
                new_length = max(sequence_length + variation, 10)
                
                if new_length != sequence_length:
                    # Resample
                    old_indices = np.linspace(0, sequence_length - 1, sequence_length)
                    new_indices = np.linspace(0, sequence_length - 1, new_length)
                    
                    resampled = np.zeros((new_length, 21, 3))
                    for lm_idx in range(21):
                        for coord_idx in range(3):
                            resampled[:, lm_idx, coord_idx] = np.interp(
                                new_indices,
                                old_indices,
                                landmarks[:, lm_idx, coord_idx]
                            )
                    landmarks = resampled
            
            # Save
            filename = class_dir / f"sample_{sample_idx:03d}.npz"
            np.savez(
                filename,
                landmarks=landmarks,
                label=gesture_type,
                signer_id=f"synthetic_signer_{sample_idx % 5}"
            )
    
    print(f"\n✓ Dataset generated successfully!")
    print(f"Total samples: {num_classes * samples_per_class}")
    print(f"Location: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic landmark dataset")
    parser.add_argument("--output-dir", type=str, default="ml/datasets/dummy",
                        help="Output directory for dataset")
    parser.add_argument("--num-classes", type=int, default=10,
                        help="Number of gesture classes")
    parser.add_argument("--samples-per-class", type=int, default=50,
                        help="Number of samples per class")
    parser.add_argument("--sequence-length", type=int, default=24,
                        help="Number of frames per sequence")
    
    args = parser.parse_args()
    
    generate_dataset(
        output_dir=args.output_dir,
        num_classes=args.num_classes,
        samples_per_class=args.samples_per_class,
        sequence_length=args.sequence_length
    )


if __name__ == "__main__":
    main()
