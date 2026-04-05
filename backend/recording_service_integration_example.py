"""
Recording Service Integration Example

Demonstrates how to integrate cloud storage with the recording service
for uploading meeting recordings, transcripts, and summaries.

This is a reference implementation showing the integration pattern.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
import logging

from cloud_storage import (
    create_storage_client_from_env,
    StoragePath,
    CloudStorageError
)

logger = logging.getLogger(__name__)


class RecordingServiceWithStorage:
    """
    Recording service integrated with cloud storage.
    
    Handles:
    - Recording upload to cloud storage
    - Transcript upload
    - Summary upload
    - Presigned URL generation for playback
    - Metadata management
    """
    
    def __init__(self):
        """Initialize recording service with cloud storage client"""
        self.storage = create_storage_client_from_env()
        logger.info("Recording service initialized with cloud storage")
    
    def save_recording(
        self,
        meeting_id: str,
        file_path: str,
        duration_seconds: int,
        participants: int
    ) -> Dict[str, Any]:
        """
        Save meeting recording to cloud storage.
        
        Args:
            meeting_id: Unique meeting identifier
            file_path: Local path to recording file
            duration_seconds: Recording duration in seconds
            participants: Number of participants
            
        Returns:
            Dictionary with storage_key and playback_url
            
        Raises:
            CloudStorageError: If upload fails
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        object_name = f"meeting-{meeting_id}-{timestamp}.mp4"
        
        # Prepare metadata
        metadata = {
            "meeting_id": meeting_id,
            "timestamp": timestamp,
            "duration_seconds": str(duration_seconds),
            "participants": str(participants),
            "format": "mp4",
            "codec": "h264"
        }
        
        logger.info(f"Uploading recording for meeting {meeting_id}")
        
        try:
            # Upload recording with retry logic
            key = self.storage.upload_file(
                file_path=file_path,
                storage_path=StoragePath.RECORDINGS,
                object_name=object_name,
                metadata=metadata
            )
            
            # Generate presigned URL for playback (valid 24 hours)
            playback_url = self.storage.generate_presigned_url(
                storage_path=StoragePath.RECORDINGS,
                object_name=object_name,
                expiration=86400  # 24 hours
            )
            
            logger.info(f"Recording uploaded successfully: {key}")
            
            return {
                "storage_key": key,
                "playback_url": playback_url,
                "object_name": object_name,
                "metadata": metadata
            }
        
        except CloudStorageError as e:
            logger.error(f"Failed to upload recording: {e}")
            raise
    
    def save_transcript(
        self,
        meeting_id: str,
        transcript_content: str,
        recording_key: str
    ) -> Dict[str, Any]:
        """
        Save meeting transcript to cloud storage.
        
        Args:
            meeting_id: Unique meeting identifier
            transcript_content: Transcript text content
            recording_key: Associated recording storage key
            
        Returns:
            Dictionary with storage_key and download_url
        """
        from io import BytesIO
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        object_name = f"meeting-{meeting_id}-{timestamp}-transcript.txt"
        
        metadata = {
            "meeting_id": meeting_id,
            "recording_key": recording_key,
            "timestamp": timestamp,
            "format": "text"
        }
        
        logger.info(f"Uploading transcript for meeting {meeting_id}")
        
        try:
            # Upload transcript from memory
            file_obj = BytesIO(transcript_content.encode('utf-8'))
            
            key = self.storage.upload_fileobj(
                file_obj=file_obj,
                storage_path=StoragePath.TRANSCRIPTS,
                object_name=object_name,
                metadata=metadata
            )
            
            # Generate download URL (valid 7 days)
            download_url = self.storage.generate_presigned_url(
                storage_path=StoragePath.TRANSCRIPTS,
                object_name=object_name,
                expiration=604800  # 7 days
            )
            
            logger.info(f"Transcript uploaded successfully: {key}")
            
            return {
                "storage_key": key,
                "download_url": download_url,
                "object_name": object_name
            }
        
        except CloudStorageError as e:
            logger.error(f"Failed to upload transcript: {e}")
            raise
    
    def save_summary(
        self,
        meeting_id: str,
        summary_content: str,
        recording_key: str
    ) -> Dict[str, Any]:
        """
        Save AI-generated meeting summary to cloud storage.
        
        Args:
            meeting_id: Unique meeting identifier
            summary_content: Summary text content
            recording_key: Associated recording storage key
            
        Returns:
            Dictionary with storage_key and download_url
        """
        from io import BytesIO
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        object_name = f"meeting-{meeting_id}-{timestamp}-summary.txt"
        
        metadata = {
            "meeting_id": meeting_id,
            "recording_key": recording_key,
            "timestamp": timestamp,
            "format": "text"
        }
        
        logger.info(f"Uploading summary for meeting {meeting_id}")
        
        try:
            file_obj = BytesIO(summary_content.encode('utf-8'))
            
            key = self.storage.upload_fileobj(
                file_obj=file_obj,
                storage_path=StoragePath.SUMMARIES,
                object_name=object_name,
                metadata=metadata
            )
            
            download_url = self.storage.generate_presigned_url(
                storage_path=StoragePath.SUMMARIES,
                object_name=object_name,
                expiration=604800  # 7 days
            )
            
            logger.info(f"Summary uploaded successfully: {key}")
            
            return {
                "storage_key": key,
                "download_url": download_url,
                "object_name": object_name
            }
        
        except CloudStorageError as e:
            logger.error(f"Failed to upload summary: {e}")
            raise
    
    def save_thumbnail(
        self,
        meeting_id: str,
        thumbnail_path: str,
        recording_key: str
    ) -> Dict[str, Any]:
        """
        Save recording thumbnail to cloud storage.
        
        Args:
            meeting_id: Unique meeting identifier
            thumbnail_path: Local path to thumbnail image
            recording_key: Associated recording storage key
            
        Returns:
            Dictionary with storage_key and thumbnail_url
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        object_name = f"meeting-{meeting_id}-{timestamp}-thumb.jpg"
        
        metadata = {
            "meeting_id": meeting_id,
            "recording_key": recording_key,
            "timestamp": timestamp,
            "format": "jpeg"
        }
        
        logger.info(f"Uploading thumbnail for meeting {meeting_id}")
        
        try:
            key = self.storage.upload_file(
                file_path=thumbnail_path,
                storage_path=StoragePath.THUMBNAILS,
                object_name=object_name,
                metadata=metadata
            )
            
            # Generate public URL (valid 30 days)
            thumbnail_url = self.storage.generate_presigned_url(
                storage_path=StoragePath.THUMBNAILS,
                object_name=object_name,
                expiration=2592000  # 30 days
            )
            
            logger.info(f"Thumbnail uploaded successfully: {key}")
            
            return {
                "storage_key": key,
                "thumbnail_url": thumbnail_url,
                "object_name": object_name
            }
        
        except CloudStorageError as e:
            logger.error(f"Failed to upload thumbnail: {e}")
            raise
    
    def download_recording(
        self,
        object_name: str,
        local_path: str
    ) -> str:
        """
        Download recording from cloud storage.
        
        Args:
            object_name: Object name in storage (without path prefix)
            local_path: Local path to save downloaded file
            
        Returns:
            Local file path
        """
        logger.info(f"Downloading recording: {object_name}")
        
        try:
            return self.storage.download_file(
                storage_path=StoragePath.RECORDINGS,
                object_name=object_name,
                local_path=local_path
            )
        except CloudStorageError as e:
            logger.error(f"Failed to download recording: {e}")
            raise
    
    def delete_recording(
        self,
        object_name: str,
        delete_related: bool = True
    ) -> bool:
        """
        Delete recording and optionally related files (transcript, summary).
        
        Args:
            object_name: Recording object name
            delete_related: Whether to delete transcript and summary
            
        Returns:
            True if deletion successful
        """
        logger.info(f"Deleting recording: {object_name}")
        
        try:
            # Delete recording
            self.storage.delete_file(
                storage_path=StoragePath.RECORDINGS,
                object_name=object_name
            )
            
            if delete_related:
                # Extract meeting ID from object name
                # Format: meeting-{id}-{timestamp}.mp4
                parts = object_name.split('-')
                if len(parts) >= 2:
                    meeting_id = parts[1]
                    
                    # Delete related transcript and summary
                    # List files with meeting ID prefix
                    transcripts = self.storage.list_files(
                        StoragePath.TRANSCRIPTS,
                        prefix=f"meeting-{meeting_id}"
                    )
                    for transcript in transcripts:
                        self.storage.delete_file(StoragePath.TRANSCRIPTS, transcript)
                    
                    summaries = self.storage.list_files(
                        StoragePath.SUMMARIES,
                        prefix=f"meeting-{meeting_id}"
                    )
                    for summary in summaries:
                        self.storage.delete_file(StoragePath.SUMMARIES, summary)
            
            logger.info(f"Recording deleted successfully")
            return True
        
        except CloudStorageError as e:
            logger.error(f"Failed to delete recording: {e}")
            raise
    
    def list_recordings(
        self,
        meeting_id: Optional[str] = None
    ) -> list[str]:
        """
        List recordings, optionally filtered by meeting ID.
        
        Args:
            meeting_id: Optional meeting ID to filter by
            
        Returns:
            List of recording object names
        """
        prefix = f"meeting-{meeting_id}" if meeting_id else ""
        
        try:
            return self.storage.list_files(
                StoragePath.RECORDINGS,
                prefix=prefix
            )
        except CloudStorageError as e:
            logger.error(f"Failed to list recordings: {e}")
            raise


def example_usage():
    """Example usage of RecordingServiceWithStorage"""
    import tempfile
    
    print("=" * 60)
    print("Recording Service Integration Example")
    print("=" * 60)
    
    # Initialize service
    service = RecordingServiceWithStorage()
    
    # Create sample recording file
    temp_dir = Path(tempfile.gettempdir())
    recording_path = temp_dir / "sample-recording.mp4"
    recording_path.write_text("Sample recording content")
    
    # Save recording
    print("\n1. Saving recording...")
    recording_info = service.save_recording(
        meeting_id="test-123",
        file_path=str(recording_path),
        duration_seconds=3600,
        participants=5
    )
    print(f"   Storage key: {recording_info['storage_key']}")
    print(f"   Playback URL: {recording_info['playback_url'][:80]}...")
    
    # Save transcript
    print("\n2. Saving transcript...")
    transcript_content = """
    Meeting Transcript
    
    [00:00] John: Welcome everyone to the meeting.
    [00:15] Sarah: Thanks for having us.
    [00:30] John: Let's discuss the project timeline.
    """
    
    transcript_info = service.save_transcript(
        meeting_id="test-123",
        transcript_content=transcript_content,
        recording_key=recording_info['storage_key']
    )
    print(f"   Storage key: {transcript_info['storage_key']}")
    
    # Save summary
    print("\n3. Saving AI summary...")
    summary_content = """
    Meeting Summary
    
    Key Points:
    - Project timeline discussed
    - Team introductions completed
    
    Action Items:
    - John to send project plan by Friday
    - Sarah to review requirements
    """
    
    summary_info = service.save_summary(
        meeting_id="test-123",
        summary_content=summary_content,
        recording_key=recording_info['storage_key']
    )
    print(f"   Storage key: {summary_info['storage_key']}")
    
    # List recordings
    print("\n4. Listing recordings...")
    recordings = service.list_recordings(meeting_id="test-123")
    print(f"   Found {len(recordings)} recording(s)")
    for rec in recordings:
        print(f"   - {rec}")
    
    # Clean up
    print("\n5. Cleaning up...")
    service.delete_recording(
        object_name=recording_info['object_name'],
        delete_related=True
    )
    print("   Deleted recording and related files")
    
    # Clean up temp file
    recording_path.unlink()
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        example_usage()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
