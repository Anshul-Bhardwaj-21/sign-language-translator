"""
VIDEO STREAM MANAGER Module
Purpose: Handle WebRTC streams, video encoding/decoding, and multi-participant streaming
"""

import threading
import queue
import time
import numpy as np
import cv2
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime


# ============================================
# VIDEO STREAM CONSTANTS
# ============================================

# Default video settings
DEFAULT_VIDEO_WIDTH = 640
DEFAULT_VIDEO_HEIGHT = 480
DEFAULT_VIDEO_FPS = 30
DEFAULT_BITRATE = 1000  # kbps
DEFAULT_VIDEO_CODEC = "VP8"  # WebRTC standard

# Stream quality levels
QUALITY_ULTRA = {"width": 1920, "height": 1080, "fps": 30, "bitrate": 5000}
QUALITY_HIGH = {"width": 1280, "height": 720, "fps": 30, "bitrate": 2500}
QUALITY_MEDIUM = {"width": 640, "height": 480, "fps": 30, "bitrate": 1000}
QUALITY_LOW = {"width": 320, "height": 240, "fps": 15, "bitrate": 500}

# Buffer settings
FRAME_QUEUE_SIZE = 30  # Max frames in queue before dropping
BUFFER_TIMEOUT = 5  # seconds


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class StreamFrame:
    """Represents a single video frame in the stream."""
    frame_id: int
    participant_id: str
    data: np.ndarray  # Frame data (BGR)
    timestamp: float
    caption: str = ""  # Live caption
    gesture: str = "none"  # Detected gesture
    
    def __post_init__(self):
        self.created_at = datetime.now()


@dataclass
class StreamConfig:
    """Configuration for a video stream."""
    participant_id: str
    width: int = DEFAULT_VIDEO_WIDTH
    height: int = DEFAULT_VIDEO_HEIGHT
    fps: int = DEFAULT_VIDEO_FPS
    bitrate: int = DEFAULT_BITRATE
    codec: str = DEFAULT_VIDEO_CODEC
    quality: str = "medium"  # ultra, high, medium, low


# ============================================
# VIDEO STREAM CLASS
# ============================================

class VideoStream:
    """Manages a single participant's video stream."""
    
    def __init__(self, config: StreamConfig):
        """
        Initialize video stream.
        
        Args:
            config: StreamConfig object
        """
        self.config = config
        self.participant_id = config.participant_id
        self.frame_queue = queue.Queue(maxsize=FRAME_QUEUE_SIZE)
        self.is_active = False
        self.frame_count = 0
        self.last_frame_time = 0.0
        self.dropped_frames = 0
        self.lock = threading.Lock()
    
    def add_frame(self, frame: StreamFrame) -> bool:
        """
        Add frame to stream buffer.
        
        Args:
            frame: StreamFrame to add
        
        Returns:
            True if added, False if queue full (frame dropped)
        """
        try:
            if not self.is_active:
                return False
            
            self.frame_queue.put_nowait(frame)
            self.frame_count += 1
            self.last_frame_time = time.time()
            return True
        
        except queue.Full:
            self.dropped_frames += 1
            return False
        
        except Exception as e:
            print(f"ERROR: Failed to add frame: {str(e)}")
            return False
    
    def get_frame(self, timeout: float = 1.0) -> Optional[StreamFrame]:
        """
        Get next frame from stream.
        
        Args:
            timeout: Wait timeout in seconds
        
        Returns:
            StreamFrame or None if timeout/error
        """
        try:
            frame = self.frame_queue.get(timeout=timeout)
            return frame
        
        except queue.Empty:
            return None
        
        except Exception as e:
            print(f"ERROR: Failed to get frame: {str(e)}")
            return None
    
    def clear_buffer(self) -> None:
        """Clear frame buffer (e.g., on network lag)."""
        try:
            while not self.frame_queue.empty():
                self.frame_queue.get_nowait()
        except:
            pass
    
    def get_stats(self) -> Dict:
        """Get stream statistics."""
        return {
            "participant_id": self.participant_id,
            "is_active": self.is_active,
            "frame_count": self.frame_count,
            "dropped_frames": self.dropped_frames,
            "queue_size": self.frame_queue.qsize(),
            "fps": self.config.fps,
            "bitrate": self.config.bitrate,
            "quality": self.config.quality
        }


# ============================================
# VIDEO STREAM MANAGER CLASS
# ============================================

class VideoStreamManager:
    """Manages multiple participant video streams."""
    
    def __init__(self):
        """Initialize stream manager."""
        self.streams: Dict[str, VideoStream] = {}
        self.lock = threading.Lock()
        self.is_running = False
        self.event_callbacks = {}
    
    def create_stream(self, config: StreamConfig) -> bool:
        """
        Create a new video stream for participant.
        
        Args:
            config: StreamConfig object
        
        Returns:
            True if created, False if already exists
        """
        try:
            with self.lock:
                if config.participant_id in self.streams:
                    return False
                
                stream = VideoStream(config)
                stream.is_active = True
                self.streams[config.participant_id] = stream
                
                print(f"✓ Stream created for {config.participant_id}")
                self._trigger_event("stream_created", config.participant_id)
                return True
        
        except Exception as e:
            print(f"ERROR: Failed to create stream: {str(e)}")
            return False
    
    def remove_stream(self, participant_id: str) -> bool:
        """
        Remove participant's video stream.
        
        Args:
            participant_id: ID of participant
        
        Returns:
            True if removed, False if not found
        """
        try:
            with self.lock:
                if participant_id not in self.streams:
                    return False
                
                stream = self.streams[participant_id]
                stream.is_active = False
                stream.clear_buffer()
                del self.streams[participant_id]
                
                print(f"✓ Stream removed for {participant_id}")
                self._trigger_event("stream_removed", participant_id)
                return True
        
        except Exception as e:
            print(f"ERROR: Failed to remove stream: {str(e)}")
            return False
    
    def add_frame(self, participant_id: str, frame: StreamFrame) -> bool:
        """
        Add frame to participant's stream.
        
        Args:
            participant_id: ID of participant
            frame: StreamFrame to add
        
        Returns:
            True if added successfully
        """
        try:
            with self.lock:
                if participant_id not in self.streams:
                    return False
                
                return self.streams[participant_id].add_frame(frame)
        
        except Exception as e:
            print(f"ERROR: Failed to add frame: {str(e)}")
            return False
    
    def get_frame(self, participant_id: str, timeout: float = 1.0) -> Optional[StreamFrame]:
        """
        Get frame from participant's stream.
        
        Args:
            participant_id: ID of participant
            timeout: Wait timeout
        
        Returns:
            StreamFrame or None
        """
        try:
            with self.lock:
                if participant_id not in self.streams:
                    return None
            
            stream = self.streams[participant_id]
            return stream.get_frame(timeout)
        
        except Exception as e:
            print(f"ERROR: Failed to get frame: {str(e)}")
            return None
    
    def get_all_frames(self) -> Dict[str, Optional[StreamFrame]]:
        """
        Get latest frame from all active streams.
        
        Returns:
            Dictionary {participant_id: StreamFrame}
        """
        frames = {}
        try:
            with self.lock:
                for participant_id, stream in self.streams.items():
                    frame = stream.get_frame(timeout=0.1)
                    if frame:
                        frames[participant_id] = frame
            return frames
        except:
            return frames
    
    def get_active_participants(self) -> List[str]:
        """Get list of active participant IDs."""
        try:
            with self.lock:
                return [pid for pid, stream in self.streams.items() if stream.is_active]
        except:
            return []
    
    def get_stream_stats(self, participant_id: str) -> Optional[Dict]:
        """Get stats for specific stream."""
        try:
            with self.lock:
                if participant_id not in self.streams:
                    return None
            return self.streams[participant_id].get_stats()
        except:
            return None
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """Get stats for all streams."""
        stats = {}
        try:
            with self.lock:
                for participant_id, stream in self.streams.items():
                    stats[participant_id] = stream.get_stats()
            return stats
        except:
            return {}
    
    def _trigger_event(self, event_name: str, data: any) -> None:
        """Trigger registered event callback."""
        try:
            if event_name in self.event_callbacks:
                callback = self.event_callbacks[event_name]
                callback(data)
        except Exception as e:
            print(f"ERROR: Event callback failed: {str(e)}")
    
    def register_event(self, event_name: str, callback) -> None:
        """Register callback for event."""
        self.event_callbacks[event_name] = callback


# ============================================
# FRAME COMPOSITOR (Combine multiple streams)
# ============================================

class FrameCompositor:
    """Combines multiple video streams into single display frame."""
    
    @staticmethod
    def composite_2x2(
        frames: Dict[str, np.ndarray],
        output_width: int = 1280,
        output_height: int = 720
    ) -> np.ndarray:
        """
        Composite frames in 2x2 grid layout.
        
        Args:
            frames: Dictionary {participant_id: frame}
            output_width: Output width
            output_height: Output height
        
        Returns:
            Composite frame
        """
        try:
            h_per = output_height // 2
            w_per = output_width // 2
            
            composite = np.zeros((output_height, output_width, 3), dtype=np.uint8)
            
            positions = [(0, 0), (w_per, 0), (0, h_per), (w_per, h_per)]
            participant_ids = list(frames.keys())[:4]
            
            for idx, participant_id in enumerate(participant_ids):
                if idx >= 4:
                    break
                
                frame = frames[participant_id]
                x, y = positions[idx]
                
                # Resize frame to grid cell
                resized = cv2.resize(frame, (w_per, h_per))
                composite[y:y+h_per, x:x+w_per] = resized
            
            return composite
        
        except Exception as e:
            print(f"ERROR: Frame composition failed: {str(e)}")
            return np.zeros((output_height, output_width, 3), dtype=np.uint8)
    
    @staticmethod
    def composite_focus(
        local_frame: np.ndarray,
        remote_frames: Dict[str, np.ndarray],
        output_width: int = 1280,
        output_height: int = 720,
        local_size: float = 0.8
    ) -> np.ndarray:
        """
        Composite with focus on local frame + remote thumbnails.
        
        Args:
            local_frame: Local participant frame
            remote_frames: Other participants' frames
            output_width: Output width
            output_height: Output height
            local_size: Size ratio of local frame (0.0-1.0)
        
        Returns:
            Composite frame
        """
        try:
            composite = np.zeros((output_height, output_width, 3), dtype=np.uint8)
            
            # Main local frame
            main_h = int(output_height * local_size)
            main_w = int(output_width * local_size)
            resized_local = cv2.resize(local_frame, (main_w, main_h))
            composite[0:main_h, 0:main_w] = resized_local
            
            # Thumbnail strip
            thumb_h = output_height - main_h
            thumb_w = output_width // 3
            
            for idx, (participant_id, frame) in enumerate(list(remote_frames.items())[:3]):
                if idx >= 3:
                    break
                thumb = cv2.resize(frame, (thumb_w, thumb_h))
                x = thumb_w * idx
                composite[main_h:, x:x+thumb_w] = thumb
            
            return composite
        
        except Exception as e:
            print(f"ERROR: Focus composition failed: {str(e)}")
            return np.zeros((output_height, output_width, 3), dtype=np.uint8)
