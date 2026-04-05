"""
Cloud Storage Integration Module

Provides unified interface for AWS S3 and Google Cloud Storage with:
- Upload/download operations with retry logic
- Presigned URL generation for secure access
- Bucket structure management (recordings/, models/, datasets/)
- Comprehensive error handling and logging

Requirements: 11.7, 19.1, 19.2, 32.8
"""

import os
import logging
from typing import Optional, BinaryIO, Dict, Any
from pathlib import Path
from datetime import timedelta
from enum import Enum
import time

# AWS S3
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from botocore.config import Config

# Google Cloud Storage
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from google.api_core import retry

logger = logging.getLogger(__name__)


class StorageProvider(str, Enum):
    """Supported cloud storage providers"""
    S3 = "s3"
    GCS = "gcs"
    LOCAL = "local"


class StoragePath(str, Enum):
    """Bucket structure paths"""
    RECORDINGS = "recordings"
    MODELS = "models"
    DATASETS = "datasets"
    TRANSCRIPTS = "transcripts"
    SUMMARIES = "summaries"
    THUMBNAILS = "thumbnails"


class CloudStorageError(Exception):
    """Base exception for cloud storage operations"""
    pass


class CloudStorageClient:
    """
    Unified cloud storage client supporting AWS S3 and Google Cloud Storage.
    
    Features:
    - Automatic retry with exponential backoff
    - Presigned URL generation
    - Bucket structure management
    - Provider-agnostic interface
    """
    
    def __init__(
        self,
        provider: StorageProvider,
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: str = "us-east-1",
        gcs_project_id: Optional[str] = None,
        gcs_credentials_path: Optional[str] = None,
        local_storage_path: str = "./storage",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize cloud storage client.
        
        Args:
            provider: Storage provider (s3, gcs, or local)
            bucket_name: Name of the storage bucket
            aws_access_key_id: AWS access key (for S3)
            aws_secret_access_key: AWS secret key (for S3)
            aws_region: AWS region (for S3)
            gcs_project_id: GCP project ID (for GCS)
            gcs_credentials_path: Path to GCS credentials JSON (for GCS)
            local_storage_path: Local directory path (for local storage)
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (seconds)
        """
        self.provider = provider
        self.bucket_name = bucket_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize provider-specific clients
        if provider == StorageProvider.S3:
            self._init_s3_client(aws_access_key_id, aws_secret_access_key, aws_region)
        elif provider == StorageProvider.GCS:
            self._init_gcs_client(gcs_project_id, gcs_credentials_path)
        elif provider == StorageProvider.LOCAL:
            self._init_local_storage(local_storage_path)
        else:
            raise ValueError(f"Unsupported storage provider: {provider}")
        
        logger.info(f"Initialized {provider} cloud storage client for bucket: {bucket_name}")
    
    def _init_s3_client(
        self,
        access_key_id: Optional[str],
        secret_access_key: Optional[str],
        region: str
    ):
        """Initialize AWS S3 client with retry configuration"""
        config = Config(
            region_name=region,
            retries={
                'max_attempts': self.max_retries,
                'mode': 'adaptive'
            }
        )
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=config
        )
        
        # Verify bucket exists or create it
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket '{self.bucket_name}' exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.info(f"Creating S3 bucket '{self.bucket_name}'")
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                raise CloudStorageError(f"Failed to access S3 bucket: {e}")
    
    def _init_gcs_client(
        self,
        project_id: Optional[str],
        credentials_path: Optional[str]
    ):
        """Initialize Google Cloud Storage client"""
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        self.gcs_client = storage.Client(project=project_id)
        
        # Verify bucket exists or create it
        try:
            self.gcs_bucket = self.gcs_client.get_bucket(self.bucket_name)
            logger.info(f"GCS bucket '{self.bucket_name}' exists")
        except GoogleCloudError:
            logger.info(f"Creating GCS bucket '{self.bucket_name}'")
            self.gcs_bucket = self.gcs_client.create_bucket(self.bucket_name)
    
    def _init_local_storage(self, storage_path: str):
        """Initialize local file storage"""
        self.local_storage_path = Path(storage_path)
        self.local_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create bucket structure
        for path in StoragePath:
            (self.local_storage_path / path.value).mkdir(exist_ok=True)
        
        logger.info(f"Local storage initialized at: {self.local_storage_path}")
    
    def _retry_operation(self, operation, *args, **kwargs):
        """
        Execute operation with exponential backoff retry logic.
        
        Args:
            operation: Function to execute
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
            
        Returns:
            Result of the operation
            
        Raises:
            CloudStorageError: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except (ClientError, BotoCoreError, GoogleCloudError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Operation failed (attempt {attempt + 1}/{self.max_retries}), "
                        f"retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Operation failed after {self.max_retries} attempts: {e}")
        
        raise CloudStorageError(f"Operation failed after {self.max_retries} retries: {last_exception}")
    
    def upload_file(
        self,
        file_path: str,
        storage_path: StoragePath,
        object_name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload a file to cloud storage with retry logic.
        
        Args:
            file_path: Local path to file to upload
            storage_path: Storage path category (recordings, models, datasets)
            object_name: Object name in storage (defaults to filename)
            metadata: Optional metadata to attach to object
            
        Returns:
            Full object key/path in storage
            
        Raises:
            CloudStorageError: If upload fails after retries
        """
        if object_name is None:
            object_name = Path(file_path).name
        
        full_key = f"{storage_path.value}/{object_name}"
        
        logger.info(f"Uploading {file_path} to {self.provider}://{self.bucket_name}/{full_key}")
        
        if self.provider == StorageProvider.S3:
            return self._upload_to_s3(file_path, full_key, metadata)
        elif self.provider == StorageProvider.GCS:
            return self._upload_to_gcs(file_path, full_key, metadata)
        elif self.provider == StorageProvider.LOCAL:
            return self._upload_to_local(file_path, full_key, metadata)
    
    def _upload_to_s3(self, file_path: str, key: str, metadata: Optional[Dict[str, str]]) -> str:
        """Upload file to AWS S3"""
        extra_args = {}
        if metadata:
            extra_args['Metadata'] = metadata
        
        def upload():
            self.s3_client.upload_file(file_path, self.bucket_name, key, ExtraArgs=extra_args)
        
        self._retry_operation(upload)
        return key
    
    def _upload_to_gcs(self, file_path: str, key: str, metadata: Optional[Dict[str, str]]) -> str:
        """Upload file to Google Cloud Storage"""
        def upload():
            blob = self.gcs_bucket.blob(key)
            if metadata:
                blob.metadata = metadata
            blob.upload_from_filename(file_path)
        
        self._retry_operation(upload)
        return key
    
    def _upload_to_local(self, file_path: str, key: str, metadata: Optional[Dict[str, str]]) -> str:
        """Upload file to local storage"""
        import shutil
        
        dest_path = self.local_storage_path / key
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, dest_path)
        
        # Store metadata in sidecar file
        if metadata:
            metadata_path = dest_path.with_suffix(dest_path.suffix + '.meta')
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
        
        return key
    
    def upload_fileobj(
        self,
        file_obj: BinaryIO,
        storage_path: StoragePath,
        object_name: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload a file-like object to cloud storage with retry logic.
        
        Args:
            file_obj: File-like object to upload
            storage_path: Storage path category
            object_name: Object name in storage
            metadata: Optional metadata to attach to object
            
        Returns:
            Full object key/path in storage
        """
        full_key = f"{storage_path.value}/{object_name}"
        
        logger.info(f"Uploading file object to {self.provider}://{self.bucket_name}/{full_key}")
        
        if self.provider == StorageProvider.S3:
            return self._upload_fileobj_to_s3(file_obj, full_key, metadata)
        elif self.provider == StorageProvider.GCS:
            return self._upload_fileobj_to_gcs(file_obj, full_key, metadata)
        elif self.provider == StorageProvider.LOCAL:
            return self._upload_fileobj_to_local(file_obj, full_key, metadata)
    
    def _upload_fileobj_to_s3(self, file_obj: BinaryIO, key: str, metadata: Optional[Dict[str, str]]) -> str:
        """Upload file object to AWS S3"""
        extra_args = {}
        if metadata:
            extra_args['Metadata'] = metadata
        
        def upload():
            self.s3_client.upload_fileobj(file_obj, self.bucket_name, key, ExtraArgs=extra_args)
        
        self._retry_operation(upload)
        return key
    
    def _upload_fileobj_to_gcs(self, file_obj: BinaryIO, key: str, metadata: Optional[Dict[str, str]]) -> str:
        """Upload file object to Google Cloud Storage"""
        def upload():
            blob = self.gcs_bucket.blob(key)
            if metadata:
                blob.metadata = metadata
            blob.upload_from_file(file_obj)
        
        self._retry_operation(upload)
        return key
    
    def _upload_fileobj_to_local(self, file_obj: BinaryIO, key: str, metadata: Optional[Dict[str, str]]) -> str:
        """Upload file object to local storage"""
        dest_path = self.local_storage_path / key
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dest_path, 'wb') as f:
            f.write(file_obj.read())
        
        if metadata:
            metadata_path = dest_path.with_suffix(dest_path.suffix + '.meta')
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
        
        return key
    
    def download_file(
        self,
        storage_path: StoragePath,
        object_name: str,
        local_path: str
    ) -> str:
        """
        Download a file from cloud storage with retry logic.
        
        Args:
            storage_path: Storage path category
            object_name: Object name in storage
            local_path: Local path to save downloaded file
            
        Returns:
            Local file path
            
        Raises:
            CloudStorageError: If download fails after retries
        """
        full_key = f"{storage_path.value}/{object_name}"
        
        logger.info(f"Downloading {self.provider}://{self.bucket_name}/{full_key} to {local_path}")
        
        # Ensure local directory exists
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        
        if self.provider == StorageProvider.S3:
            return self._download_from_s3(full_key, local_path)
        elif self.provider == StorageProvider.GCS:
            return self._download_from_gcs(full_key, local_path)
        elif self.provider == StorageProvider.LOCAL:
            return self._download_from_local(full_key, local_path)
    
    def _download_from_s3(self, key: str, local_path: str) -> str:
        """Download file from AWS S3"""
        def download():
            self.s3_client.download_file(self.bucket_name, key, local_path)
        
        self._retry_operation(download)
        return local_path
    
    def _download_from_gcs(self, key: str, local_path: str) -> str:
        """Download file from Google Cloud Storage"""
        def download():
            blob = self.gcs_bucket.blob(key)
            blob.download_to_filename(local_path)
        
        self._retry_operation(download)
        return local_path
    
    def _download_from_local(self, key: str, local_path: str) -> str:
        """Download file from local storage"""
        import shutil
        
        source_path = self.local_storage_path / key
        if not source_path.exists():
            raise CloudStorageError(f"File not found: {source_path}")
        
        shutil.copy2(source_path, local_path)
        return local_path
    
    def generate_presigned_url(
        self,
        storage_path: StoragePath,
        object_name: str,
        expiration: int = 3600,
        method: str = "GET"
    ) -> str:
        """
        Generate a presigned URL for secure temporary access to an object.
        
        Args:
            storage_path: Storage path category
            object_name: Object name in storage
            expiration: URL expiration time in seconds (default: 1 hour)
            method: HTTP method (GET for download, PUT for upload)
            
        Returns:
            Presigned URL string
            
        Raises:
            CloudStorageError: If URL generation fails
        """
        full_key = f"{storage_path.value}/{object_name}"
        
        logger.info(f"Generating presigned URL for {self.provider}://{self.bucket_name}/{full_key}")
        
        if self.provider == StorageProvider.S3:
            return self._generate_s3_presigned_url(full_key, expiration, method)
        elif self.provider == StorageProvider.GCS:
            return self._generate_gcs_presigned_url(full_key, expiration, method)
        elif self.provider == StorageProvider.LOCAL:
            return self._generate_local_presigned_url(full_key, expiration)
    
    def _generate_s3_presigned_url(self, key: str, expiration: int, method: str) -> str:
        """Generate presigned URL for AWS S3"""
        try:
            client_method = 'get_object' if method == 'GET' else 'put_object'
            url = self.s3_client.generate_presigned_url(
                client_method,
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except (ClientError, BotoCoreError) as e:
            raise CloudStorageError(f"Failed to generate S3 presigned URL: {e}")
    
    def _generate_gcs_presigned_url(self, key: str, expiration: int, method: str) -> str:
        """Generate presigned URL for Google Cloud Storage"""
        try:
            blob = self.gcs_bucket.blob(key)
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expiration),
                method=method
            )
            return url
        except GoogleCloudError as e:
            raise CloudStorageError(f"Failed to generate GCS presigned URL: {e}")
    
    def _generate_local_presigned_url(self, key: str, expiration: int) -> str:
        """Generate presigned URL for local storage (returns file path)"""
        # For local storage, return a file:// URL
        file_path = self.local_storage_path / key
        if not file_path.exists():
            raise CloudStorageError(f"File not found: {file_path}")
        return f"file://{file_path.absolute()}"
    
    def delete_file(
        self,
        storage_path: StoragePath,
        object_name: str
    ) -> bool:
        """
        Delete a file from cloud storage.
        
        Args:
            storage_path: Storage path category
            object_name: Object name in storage
            
        Returns:
            True if deletion successful
            
        Raises:
            CloudStorageError: If deletion fails
        """
        full_key = f"{storage_path.value}/{object_name}"
        
        logger.info(f"Deleting {self.provider}://{self.bucket_name}/{full_key}")
        
        if self.provider == StorageProvider.S3:
            return self._delete_from_s3(full_key)
        elif self.provider == StorageProvider.GCS:
            return self._delete_from_gcs(full_key)
        elif self.provider == StorageProvider.LOCAL:
            return self._delete_from_local(full_key)
    
    def _delete_from_s3(self, key: str) -> bool:
        """Delete file from AWS S3"""
        def delete():
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
        
        self._retry_operation(delete)
        return True
    
    def _delete_from_gcs(self, key: str) -> bool:
        """Delete file from Google Cloud Storage"""
        def delete():
            blob = self.gcs_bucket.blob(key)
            blob.delete()
        
        self._retry_operation(delete)
        return True
    
    def _delete_from_local(self, key: str) -> bool:
        """Delete file from local storage"""
        file_path = self.local_storage_path / key
        if file_path.exists():
            file_path.unlink()
            
            # Delete metadata file if exists
            metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
            if metadata_path.exists():
                metadata_path.unlink()
        
        return True
    
    def list_files(
        self,
        storage_path: StoragePath,
        prefix: str = ""
    ) -> list[str]:
        """
        List files in a storage path.
        
        Args:
            storage_path: Storage path category
            prefix: Optional prefix to filter results
            
        Returns:
            List of object names (without storage_path prefix)
        """
        full_prefix = f"{storage_path.value}/{prefix}" if prefix else f"{storage_path.value}/"
        
        logger.info(f"Listing files in {self.provider}://{self.bucket_name}/{full_prefix}")
        
        if self.provider == StorageProvider.S3:
            return self._list_s3_files(full_prefix, storage_path.value)
        elif self.provider == StorageProvider.GCS:
            return self._list_gcs_files(full_prefix, storage_path.value)
        elif self.provider == StorageProvider.LOCAL:
            return self._list_local_files(full_prefix, storage_path.value)
    
    def _list_s3_files(self, prefix: str, storage_path: str) -> list[str]:
        """List files in AWS S3"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            # Remove storage_path prefix from keys
            prefix_len = len(storage_path) + 1
            return [obj['Key'][prefix_len:] for obj in response['Contents']]
        except (ClientError, BotoCoreError) as e:
            raise CloudStorageError(f"Failed to list S3 files: {e}")
    
    def _list_gcs_files(self, prefix: str, storage_path: str) -> list[str]:
        """List files in Google Cloud Storage"""
        try:
            blobs = self.gcs_bucket.list_blobs(prefix=prefix)
            
            # Remove storage_path prefix from names
            prefix_len = len(storage_path) + 1
            return [blob.name[prefix_len:] for blob in blobs]
        except GoogleCloudError as e:
            raise CloudStorageError(f"Failed to list GCS files: {e}")
    
    def _list_local_files(self, prefix: str, storage_path: str) -> list[str]:
        """List files in local storage"""
        dir_path = self.local_storage_path / prefix
        if not dir_path.exists():
            return []
        
        # Get all files recursively
        files = []
        for file_path in dir_path.rglob('*'):
            if file_path.is_file() and not file_path.suffix == '.meta':
                # Remove storage_path prefix
                relative_path = file_path.relative_to(self.local_storage_path / storage_path)
                files.append(str(relative_path))
        
        return files


def create_storage_client_from_env() -> CloudStorageClient:
    """
    Create a CloudStorageClient from environment variables.
    
    Environment variables:
        STORAGE_PROVIDER: s3, gcs, or local
        STORAGE_BUCKET_NAME: Bucket name
        AWS_ACCESS_KEY_ID: AWS access key (for S3)
        AWS_SECRET_ACCESS_KEY: AWS secret key (for S3)
        AWS_REGION: AWS region (for S3)
        GCS_PROJECT_ID: GCP project ID (for GCS)
        GCS_CREDENTIALS_PATH: Path to GCS credentials (for GCS)
        LOCAL_STORAGE_PATH: Local storage path (for local)
    
    Returns:
        Configured CloudStorageClient instance
    """
    provider = StorageProvider(os.getenv('STORAGE_PROVIDER', 'local'))
    bucket_name = os.getenv('STORAGE_BUCKET_NAME', 'meeting-recordings')
    
    return CloudStorageClient(
        provider=provider,
        bucket_name=bucket_name,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_region=os.getenv('AWS_REGION', 'us-east-1'),
        gcs_project_id=os.getenv('GCS_PROJECT_ID'),
        gcs_credentials_path=os.getenv('GCS_CREDENTIALS_PATH'),
        local_storage_path=os.getenv('LOCAL_STORAGE_PATH', './storage'),
    )
