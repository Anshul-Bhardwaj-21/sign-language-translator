"""
CALL MANAGER Module
Purpose: Manage video call sessions, participants, call state, and transitions
"""

import uuid
import threading
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

try:
    from app.server.video_stream_manager import VideoStreamManager, StreamConfig
except ModuleNotFoundError:
    from server.video_stream_manager import VideoStreamManager, StreamConfig  # type: ignore[no-redef]


# ============================================
# CALL STATE ENUMS
# ============================================

class CallState(Enum):
    """Current state of a video call."""
    IDLE = "idle"  # No call active
    WAITING = "waiting"  # Waiting for participants
    ACTIVE = "active"  # Call in progress
    ON_HOLD = "on_hold"  # Call paused
    ENDING = "ending"  # Call terminating
    ENDED = "ended"  # Call completed


class ParticipantRole(Enum):
    """Role of participant in call."""
    HOST = "host"
    ATTENDEE = "attendee"
    GUEST = "guest"


class MediaState(Enum):
    """State of participant's media."""
    ACTIVE = "active"
    MUTED = "muted"
    DISABLED = "disabled"


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class Participant:
    """Represents a call participant."""
    participant_id: str
    name: str
    email: str = ""
    role: ParticipantRole = ParticipantRole.ATTENDEE
    joined_at: datetime = None
    audio_state: MediaState = MediaState.ACTIVE
    video_state: MediaState = MediaState.ACTIVE
    is_screen_sharing: bool = False
    current_caption: str = ""
    detected_gesture: str = "none"
    
    def __post_init__(self):
        if self.joined_at is None:
            self.joined_at = datetime.now()
    
    def toggle_audio(self) -> None:
        """Toggle audio on/off."""
        self.audio_state = (MediaState.ACTIVE if self.audio_state == MediaState.MUTED 
                           else MediaState.MUTED)
    
    def toggle_video(self) -> None:
        """Toggle video on/off."""
        self.video_state = (MediaState.ACTIVE if self.video_state == MediaState.DISABLED 
                           else MediaState.DISABLED)
    
    def get_status(self) -> str:
        """Get participant status string."""
        status = []
        if self.audio_state == MediaState.MUTED:
            status.append("Audio muted")
        if self.video_state == MediaState.DISABLED:
            status.append("Video off")
        if self.is_screen_sharing:
            status.append("Sharing screen")
        return " | ".join(status) if status else "Active"


@dataclass
class CallSession:
    """Represents a video call session."""
    call_id: str
    call_name: str
    host_id: str
    created_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    state: CallState = CallState.IDLE
    max_participants: int = 10
    allow_recording: bool = True
    is_recording: bool = False
    
    def get_duration(self) -> Optional[float]:
        """Get call duration in seconds."""
        if self.started_at is None:
            return None
        
        end_time = self.ended_at if self.ended_at else datetime.now()
        delta = end_time - self.started_at
        return delta.total_seconds()


# ============================================
# CALL MANAGER CLASS
# ============================================

class CallManager:
    """Manages video call sessions and participants."""
    
    def __init__(self):
        """Initialize call manager."""
        self.current_call: Optional[CallSession] = None
        self.participants: Dict[str, Participant] = {}
        self.stream_manager = VideoStreamManager()
        self.lock = threading.Lock()
        self.call_history: List[CallSession] = []
        self.event_callbacks = {}
    
    # ============================================
    # CALL LIFECYCLE
    # ============================================
    
    def start_call(
        self,
        host_id: str,
        call_name: str,
        max_participants: int = 10,
        host_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Start a new video call.
        
        Args:
            host_id: ID of call host
            call_name: Name/title of call
            max_participants: Maximum participants allowed
            host_name: Optional display name for host participant
        
        Returns:
            Call ID if successful, None otherwise
        """
        try:
            with self.lock:
                if self.current_call is not None:
                    return None
                
                call_id = str(uuid.uuid4())
                self.current_call = CallSession(
                    call_id=call_id,
                    call_name=call_name,
                    host_id=host_id,
                    created_at=datetime.now(),
                    max_participants=max_participants
                )
                self.current_call.state = CallState.WAITING
                
                # Add host as participant
                resolved_host_name = host_name.strip() if host_name and host_name.strip() else f"Host ({host_id[:8]})"
                self.participants[host_id] = Participant(
                    participant_id=host_id,
                    name=resolved_host_name,
                    role=ParticipantRole.HOST,
                    joined_at=datetime.now()
                )

                # Ensure host has an active stream immediately.
                host_stream_config = StreamConfig(
                    participant_id=host_id,
                    width=640,
                    height=480,
                    fps=30,
                )
                if not self.stream_manager.create_stream(host_stream_config):
                    self.participants.pop(host_id, None)
                    self.current_call = None
                    return None
                
                print(f"Call started: {call_id}")
                self._trigger_event("call_started", call_id)
                return call_id
        
        except Exception as e:
            print(f"ERROR: Failed to start call: {str(e)}")
            return None
    
    def end_call(self) -> bool:
        """
        End the current video call.
        
        Returns:
            True if ended, False otherwise
        """
        try:
            with self.lock:
                if self.current_call is None:
                    return False
                
                self.current_call.state = CallState.ENDING
                self.current_call.ended_at = datetime.now()
                
                # Save to history
                self.call_history.append(self.current_call)
                
                # Clean up resources
                for participant_id in list(self.participants.keys()):
                    self.stream_manager.remove_stream(participant_id)
                
                call_id = self.current_call.call_id
                self.current_call = None
                self.participants.clear()
                
                print(f"Call ended: {call_id}")
                self._trigger_event("call_ended", call_id)
                return True
        
        except Exception as e:
            print(f"ERROR: Failed to end call: {str(e)}")
            return False
    
    def activate_call(self) -> bool:
        """Mark call as active (started)."""
        try:
            with self.lock:
                if self.current_call is None:
                    return False
                
                self.current_call.state = CallState.ACTIVE
                self.current_call.started_at = datetime.now()
                
                self._trigger_event("call_activated", self.current_call.call_id)
                return True
        
        except Exception as e:
            print(f"ERROR: Failed to activate call: {str(e)}")
            return False
    
    # ============================================
    # PARTICIPANT MANAGEMENT
    # ============================================
    
    def add_participant(
        self,
        participant_id: str,
        name: str,
        email: str = "",
        role: ParticipantRole = ParticipantRole.ATTENDEE
    ) -> bool:
        """
        Add participant to call.
        
        Args:
            participant_id: Unique participant ID
            name: Display name
            email: Email address
            role: Participant role
        
        Returns:
            True if added, False otherwise
        """
        try:
            with self.lock:
                if self.current_call is None:
                    return False
                
                if len(self.participants) >= self.current_call.max_participants:
                    print("ERROR: Max participants reached")
                    return False
                
                if participant_id in self.participants:
                    return False
                
                participant = Participant(
                    participant_id=participant_id,
                    name=name,
                    email=email,
                    role=role,
                    joined_at=datetime.now()
                )
                
                self.participants[participant_id] = participant
                
                # Create video stream
                config = StreamConfig(
                    participant_id=participant_id,
                    width=640,
                    height=480,
                    fps=30
                )
                self.stream_manager.create_stream(config)
                
                print(f"Participant added: {name} ({participant_id})")
                self._trigger_event("participant_joined", participant_id)
                return True
        
        except Exception as e:
            print(f"ERROR: Failed to add participant: {str(e)}")
            return False
    
    def remove_participant(self, participant_id: str) -> bool:
        """
        Remove participant from call.
        
        Args:
            participant_id: ID of participant to remove
        
        Returns:
            True if removed, False otherwise
        """
        try:
            with self.lock:
                if participant_id not in self.participants:
                    return False
                
                # Remove stream
                self.stream_manager.remove_stream(participant_id)
                
                # Remove participant
                del self.participants[participant_id]
                
                print(f"Participant removed: {participant_id}")
                self._trigger_event("participant_left", participant_id)
                return True
        
        except Exception as e:
            print(f"ERROR: Failed to remove participant: {str(e)}")
            return False
    
    def get_participant(self, participant_id: str) -> Optional[Participant]:
        """Get participant object."""
        return self.participants.get(participant_id)
    
    def get_all_participants(self) -> List[Participant]:
        """Get list of all participants."""
        with self.lock:
            return list(self.participants.values())
    
    def get_participant_count(self) -> int:
        """Get number of active participants."""
        with self.lock:
            return len(self.participants)
    
    # ============================================
    # MEDIA CONTROL
    # ============================================
    
    def mute_participant_audio(self, participant_id: str) -> bool:
        """Mute participant's audio."""
        try:
            with self.lock:
                if participant_id not in self.participants:
                    return False
                
                self.participants[participant_id].audio_state = MediaState.MUTED
                self._trigger_event("audio_muted", participant_id)
                return True
        
        except Exception as e:
            print(f"ERROR: Failed to mute audio: {str(e)}")
            return False
    
    def unmute_participant_audio(self, participant_id: str) -> bool:
        """Unmute participant's audio."""
        try:
            with self.lock:
                if participant_id not in self.participants:
                    return False
                
                self.participants[participant_id].audio_state = MediaState.ACTIVE
                self._trigger_event("audio_unmuted", participant_id)
                return True
        
        except Exception as e:
            print(f"ERROR: Failed to unmute audio: {str(e)}")
            return False
    
    def disable_participant_video(self, participant_id: str) -> bool:
        """Disable participant's video."""
        try:
            with self.lock:
                if participant_id not in self.participants:
                    return False
                
                self.participants[participant_id].video_state = MediaState.DISABLED
                self._trigger_event("video_disabled", participant_id)
                return True
        
        except Exception as e:
            print(f"ERROR: Failed to disable video: {str(e)}")
            return False
    
    def enable_participant_video(self, participant_id: str) -> bool:
        """Enable participant's video."""
        try:
            with self.lock:
                if participant_id not in self.participants:
                    return False
                
                self.participants[participant_id].video_state = MediaState.ACTIVE
                self._trigger_event("video_enabled", participant_id)
                return True
        
        except Exception as e:
            print(f"ERROR: Failed to enable video: {str(e)}")
            return False
    
    def toggle_participant_audio(self, participant_id: str) -> bool:
        """Toggle participant's audio on/off."""
        try:
            with self.lock:
                if participant_id not in self.participants:
                    return False
                
                self.participants[participant_id].toggle_audio()
                return True
        
        except Exception as e:
            print(f"ERROR: Failed to toggle audio: {str(e)}")
            return False
    
    def toggle_participant_video(self, participant_id: str) -> bool:
        """Toggle participant's video on/off."""
        try:
            with self.lock:
                if participant_id not in self.participants:
                    return False
                
                self.participants[participant_id].toggle_video()
                return True
        
        except Exception as e:
            print(f"ERROR: Failed to toggle video: {str(e)}")
            return False
    
    # ============================================
    # CAPTION & GESTURE UPDATES
    # ============================================
    
    def update_participant_caption(self, participant_id: str, caption: str) -> bool:
        """Update live caption for participant."""
        try:
            with self.lock:
                if participant_id not in self.participants:
                    return False
                
                self.participants[participant_id].current_caption = caption
                self._trigger_event("caption_updated", (participant_id, caption))
                return True
        
        except Exception as e:
            print(f"ERROR: Failed to update caption: {str(e)}")
            return False
    
    def update_participant_gesture(self, participant_id: str, gesture: str) -> bool:
        """Update detected gesture for participant."""
        try:
            with self.lock:
                if participant_id not in self.participants:
                    return False
                
                self.participants[participant_id].detected_gesture = gesture
                self._trigger_event("gesture_detected", (participant_id, gesture))
                return True
        
        except Exception as e:
            print(f"ERROR: Failed to update gesture: {str(e)}")
            return False
    
    # ============================================
    # CALL STATE
    # ============================================
    
    def get_call_state(self) -> Optional[CallState]:
        """Get current call state."""
        with self.lock:
            return self.current_call.state if self.current_call else None
    
    def get_call_info(self) -> Optional[Dict]:
        """Get current call information."""
        try:
            with self.lock:
                if self.current_call is None:
                    return None
                
                duration = self.current_call.get_duration()
                return {
                    "call_id": self.current_call.call_id,
                    "call_name": self.current_call.call_name,
                    "state": self.current_call.state.value,
                    "participant_count": len(self.participants),
                    "duration_seconds": duration,
                    "is_recording": self.current_call.is_recording
                }
        
        except Exception as e:
            print(f"ERROR: Failed to get call info: {str(e)}")
            return None
    
    # ============================================
    # EVENTS
    # ============================================
    
    def _trigger_event(self, event_name: str, data: Any) -> None:
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
