"""
Meet-style Streamlit UI for Sign Language Accessibility Video Call.

RESTRUCTURED FOR HACKATHON DEMO:
- Large central video (Meet/Zoom pattern)
- Overlaid live captions
- Bottom control bar with icons
- Minimal UI chrome
- Camera stability fixes
- Accessibility-first design

WHY: Judges must understand "video call product" in 5 seconds.
"""

from __future__ import annotations

import pickle
from pathlib import Path
import sys
import time
from typing import List, Optional, Tuple

import numpy as np
import streamlit as st

# Import Meet-style UI components
try:
    from app.UI.meet_style_ui import (
        configure_meet_page,
        render_status_bar,
        render_video_with_captions,
        render_control_bar,
        render_advanced_settings,
        trigger_browser_speech,
    )
    from app.camera.camera import CameraManager, CameraConfig
    from app.inference.debug_overlay import OverlayInfo, draw_debug_overlay
    from app.inference.gesture_controls import GestureController, action_feedback
    from app.inference.hand_detector import HandDetector, create_hand_detector
    from app.inference.movement_tracker import MovementSnapshot, MovementTracker
except ModuleNotFoundError:
    from UI.meet_style_ui import (  # type: ignore[no-redef]
        configure_meet_page,
        render_status_bar,
        render_video_with_captions,
        render_control_bar,
        render_advanced_settings,
        trigger_browser_speech,
    )
    from camera.camera import CameraManager, CameraConfig  # type: ignore[no-redef]
    from inference.debug_overlay import OverlayInfo, draw_debug_overlay  # type: ignore[no-redef]
    from inference.gesture_controls import GestureController, action_feedback  # type: ignore[no-redef]
    from inference.hand_detector import HandDetector, create_hand_detector  # type: ignore[no-redef]
    from inference.movement_tracker import MovementSnapshot, MovementTracker  # type: ignore[no-redef]


# ============================================================================
# CONSTANTS
# ============================================================================

TARGET_REFRESH_SECONDS = 0.05
MAX_CONSECUTIVE_FRAME_FAILURES = 20
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_ARTIFACT_PATH = PROJECT_ROOT / "ml" / "models" / "landmark_classifier.pkl"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

try:
    from ml.landmark_features import cosine_similarity_matrix, sequence_to_feature_vector
except Exception:
    cosine_similarity_matrix = None
    sequence_to_feature_vector = None


# ============================================================================
# STATE INITIALIZATION
# ============================================================================

def _init_state() -> None:
    """
    Initialize session state.
    
    WHY: Streamlit reruns on every interaction.
    Session state preserves camera, detector, and UI state across reruns.
    """
    defaults = {
        # Core state
        "running": False,
        "paused": False,
        "accessibility_mode": True,  # Default to accessibility mode
        "system_status": "Ready",
        "status_detail": "Click camera button to start",
        
        # Caption state
        "live_words": [],
        "confirmed_sentences": [],
        "latest_event_note": "",
        "event_note_frames": 0,
        
        # Recognition state
        "token_cooldown": 0,
        "pose_hold_frames": 0,
        "last_pose_token": "",
        "last_detected_gesture": "none",
        "last_movement_state": "no_hand",
        "landmark_sequence": [],
        
        # Camera state
        "frame_failures": 0,
        "display_frame": None,
        "last_raw_frame": None,
        "camera_error": None,
        "current_fps": 0.0,
        
        # TTS state
        "speak_request_id": 0,
        "pending_speech": "",
        
        # Model state
        "model_artifact": None,
        "model_status": "Heuristic mode (no trained model loaded)",
        "model_error": "",
        "current_confidence": 0.0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Initialize stateful objects (preserved across reruns)
    if "camera" not in st.session_state:
        st.session_state.camera: Optional[CameraManager] = None
    if "hand_detector" not in st.session_state:
        st.session_state.hand_detector: Optional[HandDetector] = None
    if "movement_tracker" not in st.session_state:
        st.session_state.movement_tracker = MovementTracker()
    if "gesture_controller" not in st.session_state:
        st.session_state.gesture_controller = GestureController()


# ============================================================================
# CAMERA MANAGEMENT (STABILITY FIXES)
# ============================================================================

def _ensure_camera() -> Tuple[bool, str]:
    """
    Ensure camera is initialized and open.
    
    WHY: Camera stability is critical for video call UX.
    - Create camera only once (stored in session_state)
    - Graceful error handling
    - Never crash on camera failure
    
    RETURNS: (success, error_message)
    """
    # Create camera manager if needed
    if st.session_state.camera is None:
        try:
            config = CameraConfig(
                width=1280,
                height=720,
                target_fps=30,
                buffer_size=1,
            )
            st.session_state.camera = CameraManager(config)
        except Exception as exc:
            return False, f"Camera initialization failed: {exc}"

    # Open camera if not already open
    camera: CameraManager = st.session_state.camera
    if not camera.is_open:
        ok, message = camera.open()
        if not ok:
            return False, message

    return True, "Camera ready"


def _ensure_hand_detector() -> Tuple[bool, str]:
    """
    Ensure hand detector is initialized.
    
    WHY: Detector initialization can fail (MediaPipe issues).
    Graceful error handling prevents crashes.
    
    RETURNS: (success, error_message)
    """
    if st.session_state.hand_detector is None:
        try:
            st.session_state.hand_detector = create_hand_detector()
        except Exception as exc:
            return False, f"Hand detector initialization failed: {exc}"

    return True, "Hand detector ready"


def _release_camera() -> None:
    """
    Safely release camera resources.
    
    WHY: Proper cleanup prevents camera lock issues.
    """
    camera: Optional[CameraManager] = st.session_state.get("camera")
    if camera is not None:
        camera.release()
    st.session_state.camera = None


def _release_hand_detector() -> None:
    """
    Safely release hand detector resources.
    
    WHY: Proper cleanup prevents MediaPipe issues.
    """
    detector: Optional[HandDetector] = st.session_state.get("hand_detector")
    if detector is not None:
        detector.close()
    st.session_state.hand_detector = None


# ============================================================================
# MODEL LOADING
# ============================================================================

def _load_trained_model() -> None:
    """
    Load trained model artifact if available.
    
    WHY: Model loading can fail (file missing, corrupted).
    Graceful fallback to heuristic mode.
    """
    if not MODEL_ARTIFACT_PATH.exists():
        st.session_state.model_artifact = None
        st.session_state.model_status = "Heuristic mode (model not found)"
        return

    try:
        with MODEL_ARTIFACT_PATH.open("rb") as handle:
            artifact = pickle.load(handle)

        labels = artifact.get("labels")
        centroids = artifact.get("centroids")
        if not labels or centroids is None:
            raise ValueError("Artifact missing labels/centroids")

        artifact["centroids"] = np.asarray(centroids, dtype=np.float32)
        artifact["sequence_length"] = int(artifact.get("sequence_length", 24))
        artifact["min_confidence"] = float(artifact.get("min_confidence", 0.58))
        artifact["confidence_scale"] = float(artifact.get("confidence_scale", 6.0))

        st.session_state.model_artifact = artifact
        st.session_state.model_error = ""
        st.session_state.model_status = f"ML model loaded ({len(labels)} classes)"

    except Exception as exc:
        st.session_state.model_artifact = None
        st.session_state.model_error = str(exc)
        st.session_state.model_status = "Heuristic mode (model load failed)"


# ============================================================================
# GESTURE RECOGNITION
# ============================================================================

def _required_sequence_length() -> int:
    """Get required sequence length from model or default."""
    artifact = st.session_state.get("model_artifact")
    if artifact is None:
        return 24
    return int(artifact.get("sequence_length", 24))


def _predict_token_from_model(landmark_sequence: List[List[Tuple[float, float, float]]]) -> Tuple[str, float]:
    """
    Predict gesture token from landmark sequence using trained model.
    
    WHY: ML-based recognition for better accuracy.
    Falls back to heuristic if model unavailable.
    
    RETURNS: (token, confidence)
    """
    artifact = st.session_state.get("model_artifact")
    if artifact is None:
        return "", 0.0
    if sequence_to_feature_vector is None or cosine_similarity_matrix is None:
        return "", 0.0

    seq_len = int(artifact.get("sequence_length", 24))
    if len(landmark_sequence) < seq_len:
        return "", 0.0

    window = landmark_sequence[-seq_len:]
    try:
        feature = sequence_to_feature_vector(window, target_length=seq_len)
    except Exception:
        return "", 0.0

    features = np.expand_dims(feature, axis=0).astype(np.float32)
    centroids = np.asarray(artifact["centroids"], dtype=np.float32)
    similarities = cosine_similarity_matrix(features, centroids)

    logits = similarities * float(artifact.get("confidence_scale", 6.0))
    logits = logits - np.max(logits, axis=1, keepdims=True)
    probs = np.exp(logits)
    probs /= np.sum(probs, axis=1, keepdims=True)

    pred_idx = int(np.argmax(probs[0]))
    confidence = float(probs[0, pred_idx])
    
    # Store confidence for UI
    st.session_state.current_confidence = confidence
    
    if confidence < float(artifact.get("min_confidence", 0.58)):
        return "", confidence

    label = str(artifact["labels"][pred_idx])
    return label, confidence


def _predict_placeholder_token(landmarks: List[Tuple[float, float, float]]) -> Tuple[str, float]:
    """
    Placeholder heuristic-based gesture recognition.
    
    WHY: Fallback when ML model unavailable.
    Simple geometry-based rules.
    """
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    ring_tip = landmarks[16]
    pinky_tip = landmarks[20]
    wrist = landmarks[0]

    openness = (
        (wrist[1] - index_tip[1])
        + (wrist[1] - middle_tip[1])
        + (wrist[1] - ring_tip[1])
        + (wrist[1] - pinky_tip[1])
    ) / 4.0
    pinch = ((thumb_tip[0] - index_tip[0]) ** 2 + (thumb_tip[1] - index_tip[1]) ** 2) ** 0.5
    spread = ((index_tip[0] - pinky_tip[0]) ** 2 + (index_tip[1] - pinky_tip[1]) ** 2) ** 0.5

    if pinch < 0.06 and openness > 0.14:
        return "OK", 0.55
    if openness > 0.22:
        return "HELLO", 0.58
    if openness < 0.10:
        return "YES", 0.54
    if spread > 0.40:
        return "WIDE", 0.52
    return "SIGN", 0.5


# ============================================================================
# CAPTION MANAGEMENT
# ============================================================================

def _update_live_words(
    snapshot: MovementSnapshot,
    landmarks: Optional[List[Tuple[float, float, float]]],
    gesture_detected: bool,
) -> None:
    """
    Update live caption words based on stable hand poses.
    
    WHY: Only add words when hand is stable (prevents false positives).
    Cooldown prevents duplicate words.
    """
    if st.session_state.paused:
        return

    if landmarks is None or not snapshot.has_hand:
        st.session_state.pose_hold_frames = 0
        st.session_state.last_pose_token = ""
        return

    if gesture_detected or snapshot.state not in {"stable", "idle"}:
        st.session_state.pose_hold_frames = 0
        st.session_state.last_pose_token = ""
        return

    if st.session_state.token_cooldown > 0:
        st.session_state.token_cooldown -= 1

    # Try ML model first, fallback to heuristic
    if st.session_state.model_artifact is not None:
        token, confidence = _predict_token_from_model(st.session_state.landmark_sequence)
        if not token:
            return
    else:
        token, confidence = _predict_placeholder_token(landmarks)
        if confidence < 0.45:
            return

    if token == st.session_state.last_pose_token:
        st.session_state.pose_hold_frames += 1
    else:
        st.session_state.last_pose_token = token
        st.session_state.pose_hold_frames = 1

    # Add word after holding gesture for required frames
    hold_frames = st.session_state.get('hold_frames', 8)
    if st.session_state.pose_hold_frames >= hold_frames and st.session_state.token_cooldown == 0:
        live_words = st.session_state.live_words
        if not live_words or live_words[-1] != token:
            live_words.append(token)
        st.session_state.pose_hold_frames = 0
        st.session_state.token_cooldown = 18


def _confirm_sentence() -> None:
    """
    Confirm current live words as a sentence.
    
    WHY: Separate live (tentative) from confirmed (final) captions.
    """
    sentence = " ".join(st.session_state.live_words).strip()
    if not sentence:
        return

    st.session_state.confirmed_sentences.append(sentence)
    st.session_state.live_words = []


def _undo_last_word() -> None:
    """
    Undo last word (from live or confirmed).
    
    WHY: Error correction without clearing everything.
    """
    if st.session_state.live_words:
        st.session_state.live_words.pop()
        return

    confirmed = st.session_state.confirmed_sentences
    if not confirmed:
        return

    last_sentence = confirmed[-1].strip()
    words = last_sentence.split()
    if not words:
        confirmed.pop()
        return

    words.pop()
    if words:
        confirmed[-1] = " ".join(words)
    else:
        confirmed.pop()


def _clear_captions() -> None:
    """Clear all captions."""
    st.session_state.live_words = []
    st.session_state.confirmed_sentences = []


def _get_live_caption() -> str:
    """Get current live caption text."""
    return " ".join(st.session_state.live_words).strip()


def _get_confirmed_caption() -> str:
    """Get confirmed caption text."""
    sentences = st.session_state.confirmed_sentences
    return " ".join(s for s in sentences if s.strip())


def _get_full_caption() -> str:
    """Get full caption (confirmed + live)."""
    confirmed = _get_confirmed_caption()
    live = _get_live_caption()
    if confirmed and live:
        return f"{confirmed} {live}"
    return confirmed or live


# ============================================================================
# GESTURE CONTROL ACTIONS
# ============================================================================

def _handle_gesture_action(action: str) -> None:
    """
    Handle gesture control actions (pause, confirm, undo).
    
    WHY: Gesture-based controls = no hardware needed.
    """
    if action == "toggle_pause":
        st.session_state.paused = not st.session_state.paused
        st.session_state.system_status = "Paused" if st.session_state.paused else "Running"
    elif action == "confirm_sentence":
        _confirm_sentence()
    elif action == "undo_last_word":
        _undo_last_word()


# ============================================================================
# FRAME PROCESSING
# ============================================================================

def _process_single_frame() -> None:
    """
    Process one camera frame: detect hand, recognize gesture, update captions.
    
    WHY: Core recognition loop.
    - Read frame from camera
    - Detect hand landmarks
    - Track movement state
    - Recognize gestures
    - Update captions
    
    CAMERA STABILITY: Graceful error handling, never crash.
    """
    camera: Optional[CameraManager] = st.session_state.camera
    detector: Optional[HandDetector] = st.session_state.hand_detector
    tracker: MovementTracker = st.session_state.movement_tracker
    gestures: GestureController = st.session_state.gesture_controller

    if camera is None or detector is None:
        st.session_state.system_status = "Error"
        st.session_state.camera_error = "Camera or detector not initialized"
        return

    if st.session_state.paused:
        st.session_state.system_status = "Paused"
        return

    # Read frame from camera
    ok, frame_rgb, camera_error = camera.read_frame()
    if not ok or frame_rgb is None:
        st.session_state.frame_failures += 1
        st.session_state.camera_error = camera_error

        # Too many failures - stop for safety
        if st.session_state.frame_failures >= MAX_CONSECUTIVE_FRAME_FAILURES:
            st.session_state.running = False
            st.session_state.system_status = "Error"
            st.session_state.camera_error = "Too many frame failures. Camera stopped."
            _release_camera()
            _release_hand_detector()
        return

    st.session_state.frame_failures = 0
    st.session_state.camera_error = None

    # Detect hand landmarks
    show_landmarks = st.session_state.get('show_landmarks', True)
    detection = detector.detect(frame_rgb, draw_landmarks=show_landmarks)
    
    processed_frame = (
        detection.frame_with_landmarks
        if detection.frame_with_landmarks is not None
        else frame_rgb
    )

    if detection.error_message:
        st.session_state.camera_error = f"Detection error: {detection.error_message}"

    hand_detected = bool(detection.hand_detected and detection.primary_landmarks)

    # Update FPS
    st.session_state.current_fps = camera.get_fps()

    if hand_detected:
        # Track movement
        snapshot = tracker.update(detection.primary_landmarks)
        st.session_state.last_movement_state = snapshot.state

        # Store landmark sequence for ML model
        landmark_sequence = st.session_state.landmark_sequence
        landmark_sequence.append(detection.primary_landmarks)
        max_sequence = max(_required_sequence_length() * 3, 48)
        if len(landmark_sequence) > max_sequence:
            del landmark_sequence[:-max_sequence]

        # Detect gesture controls
        gesture_event = gestures.update(
            detection.primary_landmarks,
            snapshot.state,
            detection.handedness,
        )
        st.session_state.last_detected_gesture = gesture_event.gesture

        if gesture_event.confirmed:
            _handle_gesture_action(gesture_event.action)

        # Update live captions
        _update_live_words(
            snapshot,
            detection.primary_landmarks,
            gesture_detected=gesture_event.gesture != "none",
        )

        st.session_state.system_status = "Running"
    else:
        # No hand detected
        snapshot = tracker.update(None)
        st.session_state.last_movement_state = snapshot.state
        st.session_state.last_detected_gesture = "none"
        st.session_state.landmark_sequence = []
        st.session_state.system_status = "No Hand"
        st.session_state.pose_hold_frames = 0
        st.session_state.last_pose_token = ""

    # Store frame for display
    st.session_state.last_raw_frame = processed_frame.copy()
    st.session_state.display_frame = processed_frame


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main() -> None:
    """
    Main application entry point.
    
    MEET-STYLE UI STRUCTURE:
    1. Top status bar (FPS, hand detection, accessibility mode)
    2. Large central video with overlaid captions
    3. Bottom control bar (camera, accessibility, pause, clear, speak)
    4. Advanced settings (hidden in expander)
    
    WHY: Judges must understand "video call product" in 5 seconds.
    """
    # Configure page
    configure_meet_page()
    
    # Initialize state
    _init_state()
    _load_trained_model()
    
    # ===== TOP STATUS BAR =====
    render_status_bar(
        fps=st.session_state.current_fps,
        hand_detected=st.session_state.last_movement_state != "no_hand",
        accessibility_mode=st.session_state.accessibility_mode,
        system_status=st.session_state.system_status,
    )
    
    # ===== CENTRAL VIDEO WITH CAPTIONS =====
    # Process frame if running
    if st.session_state.running:
        # Ensure camera and detector are ready
        camera_ok, camera_msg = _ensure_camera()
        detector_ok, detector_msg = _ensure_hand_detector()
        
        if not camera_ok or not detector_ok:
            st.session_state.running = False
            st.session_state.camera_error = camera_msg if not camera_ok else detector_msg
        else:
            try:
                _process_single_frame()
            except Exception as exc:
                st.session_state.camera_error = f"Processing error: {exc}"
    
    # Render video with overlaid captions
    render_video_with_captions(
        frame=st.session_state.display_frame,
        live_caption=_get_live_caption(),
        confirmed_caption=_get_confirmed_caption(),
        accessibility_mode=st.session_state.accessibility_mode,
        camera_error=st.session_state.camera_error,
    )
    
    # ===== BOTTOM CONTROL BAR =====
    has_text = bool(st.session_state.live_words or st.session_state.confirmed_sentences)
    controls = render_control_bar(
        is_running=st.session_state.running,
        is_paused=st.session_state.paused,
        accessibility_mode=st.session_state.accessibility_mode,
        has_text=has_text,
    )
    
    # Handle control actions
    if controls.get("camera_toggle"):
        if st.session_state.running:
            # Stop camera
            st.session_state.running = False
            st.session_state.system_status = "Stopped"
            _release_camera()
            _release_hand_detector()
        else:
            # Start camera
            st.session_state.running = True
            st.session_state.system_status = "Starting..."
    
    if controls.get("accessibility_toggle"):
        st.session_state.accessibility_mode = not st.session_state.accessibility_mode
    
    if controls.get("pause_toggle"):
        st.session_state.paused = not st.session_state.paused
        st.session_state.system_status = "Paused" if st.session_state.paused else "Running"
    
    if controls.get("clear"):
        _clear_captions()
    
    if controls.get("speak"):
        text = _get_full_caption()
        st.session_state.pending_speech = text
        st.session_state.speak_request_id += 1
    
    # ===== ADVANCED SETTINGS =====
    render_advanced_settings()
    
    # ===== TEXT-TO-SPEECH =====
    if st.session_state.pending_speech:
        trigger_browser_speech(
            text=st.session_state.pending_speech,
            request_id=st.session_state.speak_request_id,
        )
        st.session_state.pending_speech = ""
    
    # ===== AUTO-RERUN FOR LIVE VIDEO =====
    if st.session_state.running:
        time.sleep(TARGET_REFRESH_SECONDS)
        st.rerun()


if __name__ == "__main__":
    main()
