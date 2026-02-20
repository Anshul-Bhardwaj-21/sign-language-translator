"""
ASL Alphabet Model Training Script

Downloads ASL Alphabet dataset from Kaggle and trains MobileNetV2 classifier.
Dataset: 87,000 images across 29 classes (A-Z, space, del, nothing)
"""

import os
import sys
import zipfile
from pathlib import Path
from typing import Tuple

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Configuration
IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 20
NUM_CLASSES = 29
LEARNING_RATE = 0.001

# Class names (A-Z, space, del, nothing)
CLASS_NAMES = [chr(i) for i in range(65, 91)] + ['space', 'del', 'nothing']


def download_kaggle_dataset(dataset_name: str, download_path: str) -> bool:
    """
    Download ASL Alphabet dataset from Kaggle.
    
    Requires: kaggle API credentials in ~/.kaggle/kaggle.json
    Install: pip install kaggle
    """
    try:
        import kaggle
        print(f"Downloading {dataset_name} from Kaggle...")
        kaggle.api.dataset_download_files(
            dataset_name,
            path=download_path,
            unzip=True
        )
        print("Download complete!")
        return True
    except ImportError:
        print("ERROR: kaggle package not installed. Install with: pip install kaggle")
        print("Also ensure ~/.kaggle/kaggle.json contains your API credentials")
        return False
    except Exception as exc:
        print(f"ERROR downloading dataset: {exc}")
        print("\nManual download instructions:")
        print(f"1. Visit: https://www.kaggle.com/datasets/{dataset_name}")
        print(f"2. Download and extract to: {download_path}")
        return False


def create_model(num_classes: int = NUM_CLASSES) -> keras.Model:
    """Create MobileNetV2-based ASL classifier."""
    
    # Load pre-trained MobileNetV2 (without top layer)
    base_model = MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights='imagenet'
    )
    
    # Freeze base model layers
    base_model.trainable = False
    
    # Build classifier
    model = keras.Sequential([
        layers.Input(shape=(IMG_SIZE, IMG_SIZE, 3)),
        layers.Rescaling(1./255),  # Normalize to [0, 1]
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dropout(0.3),
        layers.Dense(256, activation='relu'),
        layers.Dropout(0.2),
        layers.Dense(num_classes, activation='softmax')
    ])
    
    return model


def prepare_data_generators(data_dir: str) -> Tuple[ImageDataGenerator, ImageDataGenerator]:
    """Create training and validation data generators with augmentation."""
    
    train_datagen = ImageDataGenerator(
        # Note: Rescaling removed - model has Rescaling layer
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        shear_range=0.1,
        zoom_range=0.1,
        horizontal_flip=False,  # ASL signs are not symmetric
        fill_mode='nearest',
        validation_split=0.2
    )
    
    val_datagen = ImageDataGenerator(
        # Note: Rescaling removed - model has Rescaling layer
        validation_split=0.2
    )
    
    return train_datagen, val_datagen


def train_model(data_dir: str, model_save_path: str) -> None:
    """Train ASL classifier and save to disk."""
    
    print(f"\n{'='*60}")
    print("ASL ALPHABET MODEL TRAINING")
    print(f"{'='*60}\n")
    
    # Check if data directory exists
    if not os.path.exists(data_dir):
        print(f"ERROR: Data directory not found: {data_dir}")
        print("\nAttempting to download dataset...")
        
        parent_dir = str(Path(data_dir).parent)
        os.makedirs(parent_dir, exist_ok=True)
        
        success = download_kaggle_dataset(
            "grassknoted/asl-alphabet",
            parent_dir
        )
        
        if not success:
            print("\nTraining aborted. Please download dataset manually.")
            sys.exit(1)
    
    # Create model
    print("Creating MobileNetV2 model...")
    model = create_model(NUM_CLASSES)
    
    # Compile model
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss='categorical_crossentropy',
        metrics=['accuracy', keras.metrics.TopKCategoricalAccuracy(k=3, name='top_3_accuracy')]
    )
    
    print("\nModel Summary:")
    model.summary()
    
    # Prepare data generators
    print(f"\nLoading data from: {data_dir}")
    train_datagen, val_datagen = prepare_data_generators(data_dir)
    
    train_generator = train_datagen.flow_from_directory(
        data_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='training',
        shuffle=True
    )
    
    val_generator = val_datagen.flow_from_directory(
        data_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='validation',
        shuffle=False
    )
    
    print(f"\nTraining samples: {train_generator.samples}")
    print(f"Validation samples: {val_generator.samples}")
    print(f"Classes: {train_generator.num_classes}")
    
    # Callbacks
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=3,
            min_lr=1e-7
        ),
        keras.callbacks.ModelCheckpoint(
            model_save_path,
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1
        )
    ]
    
    # Train model
    print(f"\nStarting training for {EPOCHS} epochs...")
    history = model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=EPOCHS,
        callbacks=callbacks,
        verbose=1
    )
    
    # Save final model
    model.save(model_save_path)
    print(f"\n✓ Model saved to: {model_save_path}")
    
    # Print final metrics
    final_train_acc = history.history['accuracy'][-1]
    final_val_acc = history.history['val_accuracy'][-1]
    final_top3_acc = history.history['top_3_accuracy'][-1]
    
    print(f"\n{'='*60}")
    print("TRAINING COMPLETE")
    print(f"{'='*60}")
    print(f"Final Training Accuracy: {final_train_acc:.4f}")
    print(f"Final Validation Accuracy: {final_val_acc:.4f}")
    print(f"Final Top-3 Accuracy: {final_top3_acc:.4f}")
    print(f"{'='*60}\n")


def main():
    """Main training entry point."""
    
    # Paths
    project_root = Path(__file__).parent
    data_dir = project_root / "data" / "asl_alphabet_train"
    models_dir = project_root / "models"
    model_path = models_dir / "asl_mobilenetv2.h5"
    
    # Create models directory
    models_dir.mkdir(exist_ok=True)
    
    # Train model
    train_model(str(data_dir), str(model_path))
    
    print("\nTo use this model:")
    print("1. Ensure backend/models/asl_mobilenetv2.h5 exists")
    print("2. Start backend server: python backend/server.py")
    print("3. Start frontend: cd frontend && npm run dev")
    print("4. Enable ASL mode in video call")


if __name__ == "__main__":
    main()
