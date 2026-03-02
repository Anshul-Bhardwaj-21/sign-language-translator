# Cloud Storage Setup Guide

This guide explains how to configure and use the cloud storage integration for storing recordings, ML models, and datasets.

## Overview

The cloud storage module provides a unified interface for:
- **AWS S3**: Amazon Simple Storage Service
- **Google Cloud Storage (GCS)**: Google Cloud Platform storage
- **Local Storage**: File system storage for development

## Features

- ✅ Upload/download files with automatic retry logic
- ✅ Presigned URL generation for secure temporary access
- ✅ Organized bucket structure (recordings/, models/, datasets/)
- ✅ Exponential backoff retry strategy
- ✅ Comprehensive error handling and logging
- ✅ Provider-agnostic interface

## Bucket Structure

Files are organized into the following paths:

```
bucket-name/
├── recordings/     # Meeting recordings (MP4 files)
├── models/         # ML model artifacts (.pth, .onnx)
├── datasets/       # Training datasets
├── transcripts/    # Meeting transcripts (JSON, TXT)
├── summaries/      # AI-generated summaries
└── thumbnails/     # Video thumbnails
```

## Configuration

### Environment Variables

Add these variables to your `.env` file:

```bash
# Storage Provider Selection
STORAGE_PROVIDER=local  # Options: s3, gcs, local

# Bucket Configuration
STORAGE_BUCKET_NAME=meeting-recordings

# AWS S3 Configuration (if using S3)
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-1

# Google Cloud Storage Configuration (if using GCS)
GCS_PROJECT_ID=your-project-id
GCS_CREDENTIALS_PATH=/path/to/credentials.json

# Local Storage Configuration (if using local)
LOCAL_STORAGE_PATH=./storage
```

### AWS S3 Setup

1. **Create an S3 Bucket**:
   ```bash
   aws s3 mb s3://meeting-recordings --region us-east-1
   ```

2. **Create IAM User with S3 Access**:
   - Go to AWS IAM Console
   - Create new user with programmatic access
   - Attach policy: `AmazonS3FullAccess` (or create custom policy)

3. **Get Access Keys**:
   - Save the Access Key ID and Secret Access Key
   - Add them to your `.env` file

4. **Configure CORS (if needed for browser uploads)**:
   ```json
   [
     {
       "AllowedHeaders": ["*"],
       "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
       "AllowedOrigins": ["*"],
       "ExposeHeaders": ["ETag"]
     }
   ]
   ```

### Google Cloud Storage Setup

1. **Create a GCS Bucket**:
   ```bash
   gsutil mb -p your-project-id gs://meeting-recordings
   ```

2. **Create Service Account**:
   - Go to GCP Console → IAM & Admin → Service Accounts
   - Create new service account
   - Grant role: `Storage Admin`

3. **Download Credentials**:
   - Create JSON key for the service account
   - Save to secure location
   - Set `GCS_CREDENTIALS_PATH` in `.env`

4. **Set Project ID**:
   - Add your GCP project ID to `GCS_PROJECT_ID` in `.env`

### Local Storage Setup (Development)

For local development without cloud credentials:

```bash
# .env
STORAGE_PROVIDER=local
LOCAL_STORAGE_PATH=./storage
```

The local storage will automatically create the bucket structure in the specified directory.

## Usage Examples

### Basic Usage

```python
from cloud_storage import create_storage_client_from_env, StoragePath

# Create client from environment variables
storage = create_storage_client_from_env()

# Upload a file
storage.upload_file(
    file_path="/path/to/recording.mp4",
    storage_path=StoragePath.RECORDINGS,
    object_name="meeting-123-2024-01-15.mp4",
    metadata={"meeting_id": "123", "duration": "3600"}
)

# Download a file
storage.download_file(
    storage_path=StoragePath.RECORDINGS,
    object_name="meeting-123-2024-01-15.mp4",
    local_path="/tmp/recording.mp4"
)

# Generate presigned URL (valid for 1 hour)
url = storage.generate_presigned_url(
    storage_path=StoragePath.RECORDINGS,
    object_name="meeting-123-2024-01-15.mp4",
    expiration=3600
)
print(f"Download URL: {url}")
```

### Upload with Retry Logic

The client automatically retries failed operations with exponential backoff:

```python
# Automatic retry on network errors
storage.upload_file(
    file_path="large-file.mp4",
    storage_path=StoragePath.RECORDINGS,
    object_name="recording.mp4"
)
# Will retry up to 3 times with delays: 1s, 2s, 4s
```

### Upload File Object

```python
from io import BytesIO

# Upload from memory
file_obj = BytesIO(b"File content")
storage.upload_fileobj(
    file_obj=file_obj,
    storage_path=StoragePath.MODELS,
    object_name="model-v1.pth"
)
```

### List Files

```python
# List all recordings
files = storage.list_files(StoragePath.RECORDINGS)
print(f"Found {len(files)} recordings")

# List with prefix filter
meeting_files = storage.list_files(
    StoragePath.RECORDINGS,
    prefix="meeting-123"
)
```

### Delete Files

```python
# Delete a file
storage.delete_file(
    storage_path=StoragePath.RECORDINGS,
    object_name="old-recording.mp4"
)
```

### Custom Client Configuration

```python
from cloud_storage import CloudStorageClient, StorageProvider

# Create S3 client with custom settings
storage = CloudStorageClient(
    provider=StorageProvider.S3,
    bucket_name="my-bucket",
    aws_access_key_id="...",
    aws_secret_access_key="...",
    aws_region="us-west-2",
    max_retries=5,
    retry_delay=2.0
)
```

## Integration with Recording Service

Example integration with the recording service:

```python
from cloud_storage import create_storage_client_from_env, StoragePath
from datetime import datetime

class RecordingService:
    def __init__(self):
        self.storage = create_storage_client_from_env()
    
    async def save_recording(self, meeting_id: str, file_path: str):
        """Save recording to cloud storage"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        object_name = f"meeting-{meeting_id}-{timestamp}.mp4"
        
        # Upload with metadata
        key = self.storage.upload_file(
            file_path=file_path,
            storage_path=StoragePath.RECORDINGS,
            object_name=object_name,
            metadata={
                "meeting_id": meeting_id,
                "timestamp": timestamp,
                "format": "mp4"
            }
        )
        
        # Generate presigned URL for playback (valid 24 hours)
        url = self.storage.generate_presigned_url(
            storage_path=StoragePath.RECORDINGS,
            object_name=object_name,
            expiration=86400
        )
        
        return {
            "storage_key": key,
            "playback_url": url
        }
```

## Integration with ML Model Registry

Example integration with ML model storage:

```python
from cloud_storage import create_storage_client_from_env, StoragePath

class ModelRegistry:
    def __init__(self):
        self.storage = create_storage_client_from_env()
    
    def save_model(self, model_path: str, version: str):
        """Save trained model to cloud storage"""
        object_name = f"sign-language-model-{version}.pth"
        
        key = self.storage.upload_file(
            file_path=model_path,
            storage_path=StoragePath.MODELS,
            object_name=object_name,
            metadata={
                "version": version,
                "framework": "pytorch",
                "model_type": "cnn-lstm"
            }
        )
        
        return key
    
    def load_model(self, version: str, local_path: str):
        """Download model from cloud storage"""
        object_name = f"sign-language-model-{version}.pth"
        
        self.storage.download_file(
            storage_path=StoragePath.MODELS,
            object_name=object_name,
            local_path=local_path
        )
        
        return local_path
```

## Error Handling

The module provides comprehensive error handling:

```python
from cloud_storage import CloudStorageError

try:
    storage.upload_file(
        file_path="recording.mp4",
        storage_path=StoragePath.RECORDINGS,
        object_name="test.mp4"
    )
except CloudStorageError as e:
    logger.error(f"Upload failed: {e}")
    # Handle error (retry, notify user, etc.)
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest backend/test_cloud_storage.py -v

# Run specific test class
pytest backend/test_cloud_storage.py::TestLocalStorageProvider -v

# Run with coverage
pytest backend/test_cloud_storage.py --cov=cloud_storage --cov-report=html
```

The tests use local storage by default, so no cloud credentials are needed for testing.

## Security Best Practices

1. **Never commit credentials**: Keep `.env` file out of version control
2. **Use IAM roles**: In production, use IAM roles instead of access keys
3. **Limit permissions**: Grant minimum required permissions (principle of least privilege)
4. **Rotate keys**: Regularly rotate access keys and credentials
5. **Use presigned URLs**: For temporary access instead of exposing permanent URLs
6. **Enable encryption**: Use server-side encryption (SSE-S3 or SSE-KMS)
7. **Monitor access**: Enable CloudTrail (AWS) or Cloud Audit Logs (GCP)

## Performance Optimization

1. **Multipart uploads**: For files > 100MB, use multipart upload (boto3 handles automatically)
2. **Parallel uploads**: Upload multiple files concurrently
3. **Compression**: Compress files before upload to reduce bandwidth
4. **CDN integration**: Use CloudFront (AWS) or Cloud CDN (GCP) for faster downloads
5. **Regional buckets**: Create buckets in regions close to your users

## Troubleshooting

### Issue: "Access Denied" error

**Solution**: Verify IAM permissions and credentials:
```bash
# AWS
aws s3 ls s3://your-bucket --profile your-profile

# GCP
gsutil ls gs://your-bucket
```

### Issue: "Bucket not found" error

**Solution**: Ensure bucket exists and name is correct:
```bash
# AWS
aws s3 mb s3://your-bucket

# GCP
gsutil mb gs://your-bucket
```

### Issue: Slow uploads/downloads

**Solution**: 
- Check network connectivity
- Use regional buckets closer to your location
- Enable multipart upload for large files
- Consider using transfer acceleration (AWS)

### Issue: Retry exhaustion

**Solution**: Increase retry attempts or delay:
```python
storage = CloudStorageClient(
    provider=StorageProvider.S3,
    bucket_name="my-bucket",
    max_retries=5,
    retry_delay=2.0
)
```

## Cost Optimization

1. **Lifecycle policies**: Automatically delete or archive old recordings
2. **Storage classes**: Use cheaper storage classes for infrequent access
3. **Compression**: Compress files to reduce storage costs
4. **Monitoring**: Track storage usage and set up billing alerts

### AWS S3 Lifecycle Policy Example

```json
{
  "Rules": [
    {
      "Id": "ArchiveOldRecordings",
      "Status": "Enabled",
      "Prefix": "recordings/",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ],
      "Expiration": {
        "Days": 365
      }
    }
  ]
}
```

## References

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [google-cloud-storage Documentation](https://cloud.google.com/python/docs/reference/storage/latest)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the test suite for usage examples
3. Check application logs for detailed error messages
4. Consult cloud provider documentation
