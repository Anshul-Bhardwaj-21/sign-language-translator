"""
Cloud Storage Integration Example

This script demonstrates how to use the cloud storage module for:
- Uploading recordings, models, and datasets
- Downloading files
- Generating presigned URLs
- Managing files

Run this script to test your cloud storage configuration.
"""

import os
import tempfile
from pathlib import Path
from cloud_storage import (
    create_storage_client_from_env,
    StoragePath,
    CloudStorageError
)


def create_sample_file(content: str, filename: str) -> str:
    """Create a temporary sample file for testing"""
    temp_dir = tempfile.gettempdir()
    file_path = Path(temp_dir) / filename
    file_path.write_text(content)
    return str(file_path)


def example_upload_recording():
    """Example: Upload a meeting recording"""
    print("\n=== Example 1: Upload Recording ===")
    
    # Create storage client from environment variables
    storage = create_storage_client_from_env()
    
    # Create a sample recording file
    sample_file = create_sample_file(
        "This is a sample meeting recording",
        "sample-recording.txt"
    )
    
    try:
        # Upload with metadata
        key = storage.upload_file(
            file_path=sample_file,
            storage_path=StoragePath.RECORDINGS,
            object_name="meeting-123-2024-01-15.txt",
            metadata={
                "meeting_id": "123",
                "duration": "3600",
                "participants": "5"
            }
        )
        
        print(f"✓ Uploaded recording: {key}")
        return key
    
    except CloudStorageError as e:
        print(f"✗ Upload failed: {e}")
        return None


def example_download_recording(object_name: str):
    """Example: Download a recording"""
    print("\n=== Example 2: Download Recording ===")
    
    storage = create_storage_client_from_env()
    
    # Download to temporary location
    download_path = Path(tempfile.gettempdir()) / "downloaded-recording.txt"
    
    try:
        storage.download_file(
            storage_path=StoragePath.RECORDINGS,
            object_name=object_name,
            local_path=str(download_path)
        )
        
        print(f"✓ Downloaded to: {download_path}")
        print(f"  Content: {download_path.read_text()}")
        
        # Clean up
        download_path.unlink()
        
    except CloudStorageError as e:
        print(f"✗ Download failed: {e}")


def example_presigned_url(object_name: str):
    """Example: Generate presigned URL for secure access"""
    print("\n=== Example 3: Generate Presigned URL ===")
    
    storage = create_storage_client_from_env()
    
    try:
        # Generate URL valid for 1 hour
        url = storage.generate_presigned_url(
            storage_path=StoragePath.RECORDINGS,
            object_name=object_name,
            expiration=3600
        )
        
        print(f"✓ Presigned URL (valid for 1 hour):")
        print(f"  {url[:100]}..." if len(url) > 100 else f"  {url}")
        
    except CloudStorageError as e:
        print(f"✗ URL generation failed: {e}")


def example_upload_model():
    """Example: Upload ML model"""
    print("\n=== Example 4: Upload ML Model ===")
    
    storage = create_storage_client_from_env()
    
    # Create a sample model file
    sample_model = create_sample_file(
        "This is a sample ML model",
        "sample-model.pth"
    )
    
    try:
        key = storage.upload_file(
            file_path=sample_model,
            storage_path=StoragePath.MODELS,
            object_name="sign-language-model-v1.0.pth",
            metadata={
                "version": "1.0",
                "framework": "pytorch",
                "accuracy": "0.85"
            }
        )
        
        print(f"✓ Uploaded model: {key}")
        return key
    
    except CloudStorageError as e:
        print(f"✗ Model upload failed: {e}")
        return None


def example_list_files():
    """Example: List files in storage"""
    print("\n=== Example 5: List Files ===")
    
    storage = create_storage_client_from_env()
    
    try:
        # List all recordings
        recordings = storage.list_files(StoragePath.RECORDINGS)
        print(f"✓ Found {len(recordings)} recording(s):")
        for recording in recordings[:5]:  # Show first 5
            print(f"  - {recording}")
        
        # List all models
        models = storage.list_files(StoragePath.MODELS)
        print(f"✓ Found {len(models)} model(s):")
        for model in models[:5]:  # Show first 5
            print(f"  - {model}")
    
    except CloudStorageError as e:
        print(f"✗ List failed: {e}")


def example_delete_file(object_name: str):
    """Example: Delete a file"""
    print("\n=== Example 6: Delete File ===")
    
    storage = create_storage_client_from_env()
    
    try:
        storage.delete_file(
            storage_path=StoragePath.RECORDINGS,
            object_name=object_name
        )
        
        print(f"✓ Deleted: {object_name}")
    
    except CloudStorageError as e:
        print(f"✗ Delete failed: {e}")


def example_upload_fileobj():
    """Example: Upload file object (from memory)"""
    print("\n=== Example 7: Upload File Object ===")
    
    from io import BytesIO
    
    storage = create_storage_client_from_env()
    
    # Create file object in memory
    file_obj = BytesIO(b"This is transcript content from memory")
    
    try:
        key = storage.upload_fileobj(
            file_obj=file_obj,
            storage_path=StoragePath.TRANSCRIPTS,
            object_name="meeting-123-transcript.txt",
            metadata={"meeting_id": "123"}
        )
        
        print(f"✓ Uploaded file object: {key}")
        return key
    
    except CloudStorageError as e:
        print(f"✗ Upload failed: {e}")
        return None


def main():
    """Run all examples"""
    print("=" * 60)
    print("Cloud Storage Integration Examples")
    print("=" * 60)
    
    # Check configuration
    provider = os.getenv('STORAGE_PROVIDER', 'local')
    bucket = os.getenv('STORAGE_BUCKET_NAME', 'meeting-recordings')
    
    print(f"\nConfiguration:")
    print(f"  Provider: {provider}")
    print(f"  Bucket: {bucket}")
    
    if provider == 's3':
        print(f"  AWS Region: {os.getenv('AWS_REGION', 'us-east-1')}")
    elif provider == 'gcs':
        print(f"  GCP Project: {os.getenv('GCS_PROJECT_ID', 'not set')}")
    elif provider == 'local':
        print(f"  Local Path: {os.getenv('LOCAL_STORAGE_PATH', './storage')}")
    
    # Run examples
    recording_key = example_upload_recording()
    
    if recording_key:
        # Extract object name from key (remove path prefix)
        object_name = recording_key.split('/', 1)[1] if '/' in recording_key else recording_key
        
        example_download_recording(object_name)
        example_presigned_url(object_name)
    
    model_key = example_upload_model()
    
    transcript_key = example_upload_fileobj()
    
    example_list_files()
    
    # Clean up (delete uploaded files)
    if recording_key:
        object_name = recording_key.split('/', 1)[1] if '/' in recording_key else recording_key
        example_delete_file(object_name)
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
