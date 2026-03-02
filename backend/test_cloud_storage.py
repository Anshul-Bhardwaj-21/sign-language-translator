"""
Unit tests for cloud storage integration.

Tests cover:
- Upload/download operations
- Presigned URL generation
- Retry logic with exponential backoff
- Error handling
- Local storage provider (for testing without cloud credentials)
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time

from cloud_storage import (
    CloudStorageClient,
    StorageProvider,
    StoragePath,
    CloudStorageError,
    create_storage_client_from_env
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def local_storage_client(temp_dir):
    """Create a local storage client for testing"""
    return CloudStorageClient(
        provider=StorageProvider.LOCAL,
        bucket_name="test-bucket",
        local_storage_path=temp_dir
    )


@pytest.fixture
def test_file(temp_dir):
    """Create a test file"""
    file_path = Path(temp_dir) / "test_upload.txt"
    file_path.write_text("Test content for upload")
    return str(file_path)


class TestLocalStorageProvider:
    """Test local storage provider (no cloud credentials needed)"""
    
    def test_initialization(self, temp_dir):
        """Test client initialization creates bucket structure"""
        client = CloudStorageClient(
            provider=StorageProvider.LOCAL,
            bucket_name="test-bucket",
            local_storage_path=temp_dir
        )
        
        # Verify bucket structure created
        for path in StoragePath:
            assert (Path(temp_dir) / path.value).exists()
    
    def test_upload_file(self, local_storage_client, test_file):
        """Test file upload"""
        key = local_storage_client.upload_file(
            file_path=test_file,
            storage_path=StoragePath.RECORDINGS,
            object_name="test.txt"
        )
        
        assert key == "recordings/test.txt"
        
        # Verify file exists in storage
        stored_path = Path(local_storage_client.local_storage_path) / key
        assert stored_path.exists()
        assert stored_path.read_text() == "Test content for upload"
    
    def test_upload_file_with_metadata(self, local_storage_client, test_file):
        """Test file upload with metadata"""
        metadata = {"meeting_id": "123", "duration": "3600"}
        
        key = local_storage_client.upload_file(
            file_path=test_file,
            storage_path=StoragePath.RECORDINGS,
            object_name="test.txt",
            metadata=metadata
        )
        
        # Verify metadata file created
        metadata_path = Path(local_storage_client.local_storage_path) / (key + ".meta")
        assert metadata_path.exists()
        
        import json
        stored_metadata = json.loads(metadata_path.read_text())
        assert stored_metadata == metadata
    
    def test_upload_fileobj(self, local_storage_client):
        """Test file object upload"""
        from io import BytesIO
        
        file_obj = BytesIO(b"Binary content")
        
        key = local_storage_client.upload_fileobj(
            file_obj=file_obj,
            storage_path=StoragePath.MODELS,
            object_name="model.pth"
        )
        
        assert key == "models/model.pth"
        
        # Verify file exists
        stored_path = Path(local_storage_client.local_storage_path) / key
        assert stored_path.exists()
        assert stored_path.read_bytes() == b"Binary content"
    
    def test_download_file(self, local_storage_client, test_file, temp_dir):
        """Test file download"""
        # Upload first
        local_storage_client.upload_file(
            file_path=test_file,
            storage_path=StoragePath.RECORDINGS,
            object_name="test.txt"
        )
        
        # Download to different location
        download_path = Path(temp_dir) / "downloaded.txt"
        result = local_storage_client.download_file(
            storage_path=StoragePath.RECORDINGS,
            object_name="test.txt",
            local_path=str(download_path)
        )
        
        assert result == str(download_path)
        assert download_path.exists()
        assert download_path.read_text() == "Test content for upload"
    
    def test_download_nonexistent_file(self, local_storage_client, temp_dir):
        """Test downloading non-existent file raises error"""
        download_path = Path(temp_dir) / "downloaded.txt"
        
        with pytest.raises(CloudStorageError, match="File not found"):
            local_storage_client.download_file(
                storage_path=StoragePath.RECORDINGS,
                object_name="nonexistent.txt",
                local_path=str(download_path)
            )
    
    def test_generate_presigned_url(self, local_storage_client, test_file):
        """Test presigned URL generation (returns file:// URL for local)"""
        # Upload first
        local_storage_client.upload_file(
            file_path=test_file,
            storage_path=StoragePath.RECORDINGS,
            object_name="test.txt"
        )
        
        url = local_storage_client.generate_presigned_url(
            storage_path=StoragePath.RECORDINGS,
            object_name="test.txt",
            expiration=3600
        )
        
        assert url.startswith("file://")
        # Check that the path contains recordings and test.txt (handle Windows paths)
        assert "recordings" in url.lower()
        assert "test.txt" in url
    
    def test_generate_presigned_url_nonexistent(self, local_storage_client):
        """Test presigned URL for non-existent file raises error"""
        with pytest.raises(CloudStorageError, match="File not found"):
            local_storage_client.generate_presigned_url(
                storage_path=StoragePath.RECORDINGS,
                object_name="nonexistent.txt"
            )
    
    def test_delete_file(self, local_storage_client, test_file):
        """Test file deletion"""
        # Upload first
        key = local_storage_client.upload_file(
            file_path=test_file,
            storage_path=StoragePath.RECORDINGS,
            object_name="test.txt"
        )
        
        stored_path = Path(local_storage_client.local_storage_path) / key
        assert stored_path.exists()
        
        # Delete
        result = local_storage_client.delete_file(
            storage_path=StoragePath.RECORDINGS,
            object_name="test.txt"
        )
        
        assert result is True
        assert not stored_path.exists()
    
    def test_delete_file_with_metadata(self, local_storage_client, test_file):
        """Test file deletion also removes metadata"""
        metadata = {"test": "data"}
        
        key = local_storage_client.upload_file(
            file_path=test_file,
            storage_path=StoragePath.RECORDINGS,
            object_name="test.txt",
            metadata=metadata
        )
        
        metadata_path = Path(local_storage_client.local_storage_path) / (key + ".meta")
        assert metadata_path.exists()
        
        # Delete
        local_storage_client.delete_file(
            storage_path=StoragePath.RECORDINGS,
            object_name="test.txt"
        )
        
        assert not metadata_path.exists()
    
    def test_list_files(self, local_storage_client, test_file):
        """Test listing files in storage path"""
        # Upload multiple files
        local_storage_client.upload_file(
            file_path=test_file,
            storage_path=StoragePath.RECORDINGS,
            object_name="file1.txt"
        )
        local_storage_client.upload_file(
            file_path=test_file,
            storage_path=StoragePath.RECORDINGS,
            object_name="file2.txt"
        )
        local_storage_client.upload_file(
            file_path=test_file,
            storage_path=StoragePath.MODELS,
            object_name="model.pth"
        )
        
        # List recordings
        files = local_storage_client.list_files(StoragePath.RECORDINGS)
        
        assert len(files) == 2
        assert "file1.txt" in files
        assert "file2.txt" in files
        assert "model.pth" not in files
    
    def test_list_files_with_prefix(self, local_storage_client, test_file):
        """Test listing files with prefix filter"""
        # Upload files with different prefixes
        local_storage_client.upload_file(
            file_path=test_file,
            storage_path=StoragePath.RECORDINGS,
            object_name="meeting-123/video.mp4"
        )
        local_storage_client.upload_file(
            file_path=test_file,
            storage_path=StoragePath.RECORDINGS,
            object_name="meeting-123/audio.mp3"
        )
        local_storage_client.upload_file(
            file_path=test_file,
            storage_path=StoragePath.RECORDINGS,
            object_name="meeting-456/video.mp4"
        )
        
        # List with prefix
        files = local_storage_client.list_files(
            StoragePath.RECORDINGS,
            prefix="meeting-123"
        )
        
        assert len(files) == 2
        # Normalize paths for comparison (handle Windows backslashes)
        normalized_files = [f.replace('\\', '/') for f in files]
        assert any("meeting-123/video.mp4" in f for f in normalized_files)
        assert any("meeting-123/audio.mp3" in f for f in normalized_files)
        assert not any("meeting-456" in f for f in normalized_files)
    
    def test_list_files_empty(self, local_storage_client):
        """Test listing empty storage path"""
        files = local_storage_client.list_files(StoragePath.DATASETS)
        assert files == []


class TestS3StorageProvider:
    """Test AWS S3 storage provider with mocked boto3"""
    
    @patch('cloud_storage.boto3.client')
    def test_s3_initialization(self, mock_boto_client):
        """Test S3 client initialization"""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.return_value = {}
        
        client = CloudStorageClient(
            provider=StorageProvider.S3,
            bucket_name="test-bucket",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            aws_region="us-east-1"
        )
        
        # Verify boto3 client created
        mock_boto_client.assert_called_once()
        mock_s3.head_bucket.assert_called_once_with(Bucket="test-bucket")
    
    @patch('cloud_storage.boto3.client')
    def test_s3_upload_file(self, mock_boto_client, test_file):
        """Test S3 file upload"""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.return_value = {}
        
        client = CloudStorageClient(
            provider=StorageProvider.S3,
            bucket_name="test-bucket",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret"
        )
        
        key = client.upload_file(
            file_path=test_file,
            storage_path=StoragePath.RECORDINGS,
            object_name="test.txt"
        )
        
        assert key == "recordings/test.txt"
        mock_s3.upload_file.assert_called_once()
    
    @patch('cloud_storage.boto3.client')
    def test_s3_download_file(self, mock_boto_client, temp_dir):
        """Test S3 file download"""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.return_value = {}
        
        client = CloudStorageClient(
            provider=StorageProvider.S3,
            bucket_name="test-bucket",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret"
        )
        
        download_path = Path(temp_dir) / "downloaded.txt"
        client.download_file(
            storage_path=StoragePath.RECORDINGS,
            object_name="test.txt",
            local_path=str(download_path)
        )
        
        mock_s3.download_file.assert_called_once()
    
    @patch('cloud_storage.boto3.client')
    def test_s3_generate_presigned_url(self, mock_boto_client):
        """Test S3 presigned URL generation"""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.return_value = {}
        mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/test-bucket/recordings/test.txt?signature=..."
        
        client = CloudStorageClient(
            provider=StorageProvider.S3,
            bucket_name="test-bucket",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret"
        )
        
        url = client.generate_presigned_url(
            storage_path=StoragePath.RECORDINGS,
            object_name="test.txt",
            expiration=3600
        )
        
        assert url.startswith("https://")
        mock_s3.generate_presigned_url.assert_called_once()


class TestGCSStorageProvider:
    """Test Google Cloud Storage provider with mocked google.cloud.storage"""
    
    @patch('cloud_storage.storage.Client')
    def test_gcs_initialization(self, mock_storage_client):
        """Test GCS client initialization"""
        mock_client = Mock()
        mock_storage_client.return_value = mock_client
        mock_bucket = Mock()
        mock_client.get_bucket.return_value = mock_bucket
        
        client = CloudStorageClient(
            provider=StorageProvider.GCS,
            bucket_name="test-bucket",
            gcs_project_id="test-project"
        )
        
        mock_storage_client.assert_called_once()
        mock_client.get_bucket.assert_called_once_with("test-bucket")
    
    @patch('cloud_storage.storage.Client')
    def test_gcs_upload_file(self, mock_storage_client, test_file):
        """Test GCS file upload"""
        mock_client = Mock()
        mock_storage_client.return_value = mock_client
        mock_bucket = Mock()
        mock_client.get_bucket.return_value = mock_bucket
        mock_blob = Mock()
        mock_bucket.blob.return_value = mock_blob
        
        client = CloudStorageClient(
            provider=StorageProvider.GCS,
            bucket_name="test-bucket",
            gcs_project_id="test-project"
        )
        
        key = client.upload_file(
            file_path=test_file,
            storage_path=StoragePath.RECORDINGS,
            object_name="test.txt"
        )
        
        assert key == "recordings/test.txt"
        mock_blob.upload_from_filename.assert_called_once()


class TestRetryLogic:
    """Test retry logic with exponential backoff"""
    
    @patch('cloud_storage.boto3.client')
    def test_retry_on_failure(self, mock_boto_client):
        """Test retry logic retries on failure"""
        from botocore.exceptions import ClientError
        
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.return_value = {}
        
        # Simulate failure then success
        mock_s3.upload_file.side_effect = [
            ClientError({'Error': {'Code': '500', 'Message': 'Server error'}}, 'upload_file'),
            None  # Success on second attempt
        ]
        
        client = CloudStorageClient(
            provider=StorageProvider.S3,
            bucket_name="test-bucket",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            max_retries=3,
            retry_delay=0.1  # Short delay for testing
        )
        
        # Should succeed after retry
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test")
            temp_file = f.name
        
        try:
            key = client.upload_file(
                file_path=temp_file,
                storage_path=StoragePath.RECORDINGS,
                object_name="test.txt"
            )
            assert key == "recordings/test.txt"
            assert mock_s3.upload_file.call_count == 2
        finally:
            os.unlink(temp_file)
    
    @patch('cloud_storage.boto3.client')
    def test_retry_exhaustion(self, mock_boto_client):
        """Test retry logic raises error after max retries"""
        from botocore.exceptions import ClientError
        
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.return_value = {}
        
        # Simulate persistent failure
        mock_s3.upload_file.side_effect = ClientError(
            {'Error': {'Code': '500', 'Message': 'Server error'}},
            'upload_file'
        )
        
        client = CloudStorageClient(
            provider=StorageProvider.S3,
            bucket_name="test-bucket",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            max_retries=2,
            retry_delay=0.1
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test")
            temp_file = f.name
        
        try:
            with pytest.raises(CloudStorageError, match="failed after 2 retries"):
                client.upload_file(
                    file_path=temp_file,
                    storage_path=StoragePath.RECORDINGS,
                    object_name="test.txt"
                )
            
            assert mock_s3.upload_file.call_count == 2
        finally:
            os.unlink(temp_file)
    
    @patch('cloud_storage.time.sleep')
    @patch('cloud_storage.boto3.client')
    def test_exponential_backoff(self, mock_boto_client, mock_sleep):
        """Test exponential backoff timing"""
        from botocore.exceptions import ClientError
        
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.return_value = {}
        
        # Simulate failures
        mock_s3.upload_file.side_effect = ClientError(
            {'Error': {'Code': '500', 'Message': 'Server error'}},
            'upload_file'
        )
        
        client = CloudStorageClient(
            provider=StorageProvider.S3,
            bucket_name="test-bucket",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            max_retries=3,
            retry_delay=1.0
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test")
            temp_file = f.name
        
        try:
            with pytest.raises(CloudStorageError):
                client.upload_file(
                    file_path=temp_file,
                    storage_path=StoragePath.RECORDINGS,
                    object_name="test.txt"
                )
            
            # Verify exponential backoff: 1s, 2s
            assert mock_sleep.call_count == 2
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert sleep_calls[0] == 1.0  # First retry: 1 * 2^0
            assert sleep_calls[1] == 2.0  # Second retry: 1 * 2^1
        finally:
            os.unlink(temp_file)


class TestEnvironmentConfiguration:
    """Test environment-based configuration"""
    
    @patch.dict(os.environ, {
        'STORAGE_PROVIDER': 'local',
        'STORAGE_BUCKET_NAME': 'test-bucket',
        'LOCAL_STORAGE_PATH': '/tmp/test-storage'
    })
    def test_create_from_env_local(self):
        """Test creating client from environment variables (local)"""
        client = create_storage_client_from_env()
        
        assert client.provider == StorageProvider.LOCAL
        assert client.bucket_name == "test-bucket"
    
    @patch.dict(os.environ, {
        'STORAGE_PROVIDER': 's3',
        'STORAGE_BUCKET_NAME': 'my-bucket',
        'AWS_ACCESS_KEY_ID': 'test-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret',
        'AWS_REGION': 'us-west-2'
    })
    @patch('cloud_storage.boto3.client')
    def test_create_from_env_s3(self, mock_boto_client):
        """Test creating S3 client from environment variables"""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.return_value = {}
        
        client = create_storage_client_from_env()
        
        assert client.provider == StorageProvider.S3
        assert client.bucket_name == "my-bucket"


class TestStoragePaths:
    """Test storage path enumeration"""
    
    def test_storage_paths_exist(self):
        """Test all required storage paths are defined"""
        required_paths = [
            "recordings",
            "models",
            "datasets",
            "transcripts",
            "summaries",
            "thumbnails"
        ]
        
        for path in required_paths:
            assert hasattr(StoragePath, path.upper())
            assert StoragePath[path.upper()].value == path


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_invalid_provider(self):
        """Test invalid provider raises error"""
        with pytest.raises(ValueError, match="Unsupported storage provider"):
            CloudStorageClient(
                provider="invalid",
                bucket_name="test-bucket"
            )
    
    @patch('cloud_storage.boto3.client')
    def test_s3_bucket_access_error(self, mock_boto_client):
        """Test S3 bucket access error handling"""
        from botocore.exceptions import ClientError
        
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.side_effect = ClientError(
            {'Error': {'Code': '403', 'Message': 'Access Denied'}},
            'head_bucket'
        )
        
        with pytest.raises(CloudStorageError, match="Failed to access S3 bucket"):
            CloudStorageClient(
                provider=StorageProvider.S3,
                bucket_name="test-bucket",
                aws_access_key_id="test-key",
                aws_secret_access_key="test-secret"
            )
