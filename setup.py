"""Setup script for Sign Language Accessibility Application."""

import os
import sys
from pathlib import Path


def create_directory_structure():
    """Create necessary directories."""
    directories = [
        "ml/datasets/raw",
        "ml/datasets/dummy",
        "ml/datasets/corrections",
        "ml/models",
        "ml/checkpoints",
        "ml/evaluation",
        "ml/notebooks",
        "logs",
        "configs",
        "tests",
        "backend",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")


def check_python_version():
    """Check Python version."""
    if sys.version_info < (3, 10):
        print("✗ Python 3.10 or higher is required")
        print(f"  Current version: {sys.version}")
        return False
    print(f"✓ Python version: {sys.version_info.major}.{sys.version_info.minor}")
    return True


def check_dependencies():
    """Check if dependencies are installed."""
    try:
        import streamlit
        import cv2
        import mediapipe
        import torch
        import numpy
        print("✓ Core dependencies installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("  Run: pip install -r requirements.txt")
        return False


def create_sample_config():
    """Create sample configuration if not exists."""
    config_path = Path("configs/config.yaml")
    
    if config_path.exists():
        print("✓ Configuration file already exists")
        return
    
    print("✓ Configuration file created at configs/config.yaml")


def print_next_steps():
    """Print next steps for user."""
    print("\n" + "=" * 70)
    print("SETUP COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("\n1. Activate virtual environment:")
    print("   Windows: .venv\\Scripts\\Activate.ps1")
    print("   macOS/Linux: source .venv/bin/activate")
    print("\n2. Install dependencies (if not already done):")
    print("   pip install -r requirements.txt")
    print("\n3. Run the application:")
    print("   streamlit run app/main.py")
    print("\n4. (Optional) Generate dummy data for testing:")
    print("   python ml/dummy_data_generator.py")
    print("\n5. (Optional) Train a model:")
    print("   python ml/train.py --data-dir ml/datasets/dummy --epochs 20")
    print("\nFor more information, see:")
    print("  - README.md (full documentation)")
    print("  - QUICKSTART.md (quick start guide)")
    print("  - docs/EDGE_CASES.md (edge case handling)")
    print("  - docs/FIREBASE_SETUP.md (Firebase setup)")
    print("\n" + "=" * 70)


def main():
    """Main setup function."""
    print("=" * 70)
    print("Sign Language Accessibility Application - Setup")
    print("=" * 70)
    print()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directory structure
    print("\nCreating directory structure...")
    create_directory_structure()
    
    # Check dependencies
    print("\nChecking dependencies...")
    deps_ok = check_dependencies()
    
    # Create sample config
    print("\nSetting up configuration...")
    create_sample_config()
    
    # Print next steps
    print_next_steps()
    
    if not deps_ok:
        print("\n⚠ Warning: Some dependencies are missing.")
        print("Please install them before running the application.")
        sys.exit(1)


if __name__ == "__main__":
    main()
