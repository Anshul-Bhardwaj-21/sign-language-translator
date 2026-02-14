"""
CALL SESSION Module
Purpose: Orchestrate complete video call workflow integrating all modules
"""

import threading
import time
from typing import Optional, Dict, List
from dataclasses import dataclass
from camera.camera import open_camera, get_frame, release_camera
from inference.hand_detector import create_hand_detector, detect_hand, extract_landmarks, draw_landmarks
from inference.movement_tracker import MovementTracker, classify_hand_state, is_hand_idle, is_hand_stable
from inference.gesture_controls import GestureDetector, detect_control_gesture
from inference.debug_overlay import DebugInfo, draw_debug_info
from server.call_manager import CallManager, ParticipantRole
from server.video_stream_manager import VideoStreamManager, StreamFrame
from server.messaging import MessageManager, MessageType


# ============================================
# SESSION STATE
# ============================================

class SessionState:
    """Session state management."""
    
    IDLE = "idle"
    SETTING_UP = "setting_up"
    IN_CALL = "in_call"
    PAUSED = "paused"
    ENDING = "ending"


# ============================================
# LOCAL PARTICIPANT
# ============================================

@dataclass
class LocalParticipant:
    """Represents the local user."""
    participant_id: str
    name: str
    is_audio_enabled: bool = True
    is_video_enabled: bool = True
    is_screen_sharing: bool = False


# ============================================
# CALL SESSION MANAGER
# ============================================

class CallSessionManager:
    """Orchestrates complete video call with all modules integrated."""
    
    def __init__(self):
        """Initialize call session manager."""
        self.state = SessionState.IDLE
        self.call_manager = CallManager()
        self.message_manager = MessageManager()
        
        # Local participant
        self.local_participant: Optional[LocalParticipant] = None
        self.local_cap = None  # Camera capture
        
        # Hand detection modules
        self.hand_detector = None
        self.movement_tracker = None
        self.gesture_detector = None
        
        # Frame processing
        self.frame_counter = 0
        self.start_time = None
        self.is_processing = False
        self.process_thread = None
        
        # Callbacks
        self.callbacks = {}
    
    # ============================================
    # SETUP & INITIALIZATION
    # ============================================
    
    def initialize_local_participant(self, participant_id: str, name: str) -> bool:
        """
        Initialize local participant.
        
        Args:
            participant_id: Unique participant ID
            name: Display name
        
        Returns:
            True if initialized
        """
        try:
            self.local_participant = LocalParticipant(
                participant_id=participant_id,
                name=name
            )
            print(f"✓ Local participant initialized: {name}")
            return True
        
        except Exception as e:
            print(f"ERROR: Failed to initialize local participant: {str(e)}")
            return False
    
    def initialize_modules(self) -> bool:
        """
        Initialize all detection modules.
        
        Returns:
            True if all initialized successfully
        """
        try:
            # Open camera
            self.local_cap = open_camera(
                width=640,
                height=480,
                fps=30
            )
            if self.local_cap is None:
                print("ERROR: Failed to open camera")
                return False
            
            # Initialize hand detector
            self.hand_detector = create_hand_detector(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.5
            )
            if self.hand_detector is None:
                print("ERROR: Failed to create hand detector")
                return False
            
            # Initialize movement tracker
            self.movement_tracker = MovementTracker(history_size=30)
            
            # Initialize gesture detector
            self.gesture_detector = GestureDetector(
                debounce_frames=5,
                confidence_threshold=0.7
            )
            
            self.state = SessionState.SETTING_UP
            print("✓ All modules initialized successfully")
            return True
        
        except Exception as e:
            print(f"ERROR: Failed to initialize modules: {str(e)}")
            return False
    
    # ============================================
    # CALL MANAGEMENT
    # ============================================
    
    def start_call(self, call_name: str, max_participants: int = 10) -> Optional[str]:
        """
        Start new video call.
        
        Args:
            call_name: Name of call
            max_participants: Maximum participants
        
        Returns:
            Call ID if successful
        """
        try:
            if self.local_participant is None:
                print("ERROR: Local participant not initialized")
                return None
            
            call_id = self.call_manager.start_call(
                host_id=self.local_participant.participant_id,
                call_name=call_name,
                max_participants=max_participants
            )
            
            if call_id:
                # Add local participant to call
                self.call_manager.add_participant(
                    participant_id=self.local_participant.participant_id,
                    name=self.local_participant.name,
                    role=ParticipantRole.HOST
                )
                
                self.state = SessionState.IN_CALL
                self.start_time = time.time()
                self._trigger_callback("call_started", call_id)
                
                # Start processing thread
                self._start_processing()
                
                return call_id
            
            return None
        
        except Exception as e:
            print(f"ERROR: Failed to start call: {str(e)}")
            return None
    
    def end_call(self) -> bool:
        """
        End current call.
        
        Returns:
            True if ended successfully
        """
        try:
            self.state = SessionState.ENDING
            self.is_processing = False
            
            # Wait for processing thread
            if self.process_thread:
                self.process_thread.join(timeout=5)
            
            # Release resources
            if self.local_cap:
                release_camera(self.local_cap)
                self.local_cap = None
            
            # End call
            success = self.call_manager.end_call()
            
            self.state = SessionState.IDLE
            self._trigger_callback("call_ended", None)
            
            return success
        
        except Exception as e:
            print(f"ERROR: Failed to end call: {str(e)}")
            return False
    
    def add_remote_participant(
        self,
        participant_id: str,
        name: str,
        email: str = ""
    ) -> bool:
        """
        Add remote participant to call.
        
        Args:
            participant_id: Unique ID
            name: Display name
            email: Email address
        
        Returns:
            True if added
        """
        return self.call_manager.add_participant(
            participant_id=participant_id,
            name=name,
            email=email
        )
    
    def remove_remote_participant(self, participant_id: str) -> bool:
        """Remove participant from call."""
        return self.call_manager.remove_participant(participant_id)
    
    # ============================================
    # MEDIA CONTROL
    # ============================================
    
    def toggle_audio(self) -> bool:
        """Toggle local audio on/off."""
        try:
            if self.local_participant:
                self.local_participant.is_audio_enabled = not self.local_participant.is_audio_enabled
                action = "unmuted" if self.local_participant.is_audio_enabled else "muted"
                
                self.message_manager.send_system_message(
                    f"🎤 You {action} your microphone"
                )
                return True
            return False
        
        except Exception as e:
            print(f"ERROR: Failed to toggle audio: {str(e)}")
            return False
    
    def toggle_video(self) -> bool:
        """Toggle local video on/off."""
        try:
            if self.local_participant:
                self.local_participant.is_video_enabled = not self.local_participant.is_video_enabled
                action = "enabled" if self.local_participant.is_video_enabled else "disabled"
                
                self.message_manager.send_system_message(
                    f"📹 You {action} your camera"
                )
                return True
            return False
        
        except Exception as e:
            print(f"ERROR: Failed to toggle video: {str(e)}")
            return False
    
    # ============================================
    # FRAME PROCESSING
    # ============================================
    
    def _start_processing(self) -> None:
        """Start background frame processing thread."""
        self.is_processing = True
        self.process_thread = threading.Thread(target=self._process_frames, daemon=True)
        self.process_thread.start()
    
    def _process_frames(self) -> None:
        """
        Main frame processing loop.
        - Capture from camera
        - Detect hands
        - Track movement
        - Detect gestures
        - Broadcast frames
        """
        frame_count = 0
        
        while self.is_processing and self.state == SessionState.IN_CALL:
            try:
                # Get frame from camera
                ret, frame = get_frame(self.local_cap)
                if not ret or frame is None:
                    continue
                
                frame_count += 1
                
                # Hand detection
                hand_detected, detection_results = detect_hand(frame, self.hand_detector)
                
                # Extract landmarks
                landmarks_list, handedness_list = extract_landmarks(detection_results)
                
                # Track movement
                if landmarks_list:
                    for landmarks in landmarks_list:
                        self.movement_tracker.update(landmarks)
                else:
                    self.movement_tracker.update(None)
                
                # Detect gesture
                current_landmarks = landmarks_list[0] if landmarks_list else None
                gesture, confidence, is_confirmed = self.gesture_detector.detect(current_landmarks)
                
                # Get movement state
                movement_state = classify_hand_state(current_landmarks, self.movement_tracker)
                
                # Draw debug overlay
                debug_info = DebugInfo()
                debug_info.fps = frame_count / (time.time() - self.start_time) if self.start_time else 0
                debug_info.hand_detected = hand_detected
                debug_info.hand_count = len(landmarks_list)
                debug_info.movement_state = movement_state
                debug_info.movement_magnitude = self.movement_tracker.get_current_movement()
                debug_info.gesture = gesture
                debug_info.confidence = confidence
                
                frame_display = draw_landmarks(frame, detection_results)
                frame_display = draw_debug_info(frame_display, debug_info)
                
                # Send frame to stream manager
                if self.local_participant:
                    stream_frame = StreamFrame(
                        frame_id=frame_count,
                        participant_id=self.local_participant.participant_id,
                        data=frame_display,
                        timestamp=time.time(),
                        caption="",  # Would be updated by caption module
                        gesture=gesture
                    )
                    
                    self.call_manager.stream_manager.add_frame(
                        self.local_participant.participant_id,
                        stream_frame
                    )
                
                # Update gesture every 100 frames
                if frame_count % 100 == 0 and gesture != "none":
                    self.call_manager.update_participant_gesture(
                        self.local_participant.participant_id,
                        gesture
                    )
                
                self._trigger_callback("frame_processed", {
                    "frame": frame_display,
                    "hand_detected": hand_detected,
                    "gesture": gesture,
                    "movement_state": movement_state
                })
                
                # Small delay to prevent CPU overload
                time.sleep(0.01)
            
            except Exception as e:
                print(f"ERROR in frame processing: {str(e)}")
                continue
    
    # ============================================
    # STATE & INFO
    # ============================================
    
    def get_call_info(self) -> Optional[Dict]:
        """Get current call information."""
        return self.call_manager.get_call_info()
    
    def get_participants(self) -> List:
        """Get all call participants."""
        return self.call_manager.get_all_participants()
    
    def get_messages(self, limit: int = 50) -> List[Dict]:
        """Get chat messages."""
        return self.message_manager.get_messages(limit)
    
    def send_message(self, content: str) -> bool:
        """Send chat message."""
        if not self.local_participant:
            return False
        
        return self.message_manager.send_message(
            message_id="msg_" + str(hash(content))[:8],
            sender_id=self.local_participant.participant_id,
            sender_name=self.local_participant.name,
            content=content,
            message_type=MessageType.TEXT
        )
    
    def get_stream_frames(self) -> Dict:
        """Get latest frames from all participants."""
        return self.call_manager.stream_manager.get_all_frames()
    
    # ============================================
    # CALLBACKS
    # ============================================
    
    def register_callback(self, event_name: str, callback) -> None:
        """Register event callback."""
        self.callbacks[event_name] = callback
    
    def _trigger_callback(self, event_name: str, data: any) -> None:
        """Trigger registered callback."""
        try:
            if event_name in self.callbacks:
                self.callbacks[event_name](data)
        except Exception as e:
            print(f"ERROR: Callback failed: {str(e)}")
    
    # ============================================
    # CLEANUP
    # ============================================
    
    def cleanup(self) -> None:
        """Clean up all resources."""
        try:
            self.is_processing = False
            
            if self.process_thread:
                self.process_thread.join(timeout=5)
            
            if self.local_cap:
                release_camera(self.local_cap)
            
            print("✓ Session cleaned up")
        
        except Exception as e:
            print(f"ERROR: Cleanup failed: {str(e)}")
