"""Streamlit entrypoint for real-time sign-language accessibility prototype."""

from __future__ import annotations

import pickle
from pathlib import Path
import sys
import time
from typing import List, Optional, Tuple

import numpy as np
import streamlit as st

from UI.ui import (
    configure_page,
    join_confirmed_sentences,
    render_camera_panel,
    render_caption_panel,
    render_controls,
    render_event_note,
    render_header,
    render_status_indicator,
    trigger_browser_speech,
)
from camera.camera import CameraManager, create_camera_manager
from inference.debug_overlay import OverlayInfo, draw_debug_overlay
from inference.gesture_controls import GestureController, action_feedback
from inference.hand_detector import HandDetector, create_hand_detector
from inference.movement_tracker import MovementSnapshot, MovementTracker


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


def _init_state() -> None:
    defaults = {
        "running": False,
        "paused": False,
        "system_status": "Stopped",
        "status_detail": "Press Start to initialize camera and hand tracking.",
        "live_words": [],
        "confirmed_sentences": [],
        "latest_event_note": "",
        "event_note_frames": 0,
        "token_cooldown": 0,
        "pose_hold_frames": 0,
        "last_pose_token": "",
        "last_detected_gesture": "none",
        "last_movement_state": "no_hand",
        "frame_failures": 0,
        "speak_request_id": 0,
        "pending_speech": "",
        "display_frame": None,
        "last_raw_frame": None,
        "model_artifact": None,
        "model_status": "Heuristic mode (no trained model loaded).",
        "model_error": "",
        "landmark_sequence": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "camera" not in st.session_state:
        st.session_state.camera: Optional[CameraManager] = None
    if "hand_detector" not in st.session_state:
        st.session_state.hand_detector: Optional[HandDetector] = None
    if "movement_tracker" not in st.session_state:
        st.session_state.movement_tracker = MovementTracker()
    if "gesture_controller" not in st.session_state:
        st.session_state.gesture_controller = GestureController()


def _ensure_runtime_components() -> Tuple[bool, str]:
    if st.session_state.camera is None:
        st.session_state.camera = create_camera_manager()

    if st.session_state.hand_detector is None:
        st.session_state.hand_detector = create_hand_detector()

    camera: CameraManager = st.session_state.camera
    if not camera.is_open:
        ok, message = camera.open()
        if not ok:
            return False, message

    return True, "Runtime components ready."


def _load_trained_model() -> None:
    """
    Load trained model artifact if available.

    This runs on each rerun but only reloads when the artifact path changes
    from missing to present.
    """
    if not MODEL_ARTIFACT_PATH.exists():
        st.session_state.model_artifact = None
        st.session_state.model_status = "Heuristic mode (model artifact not found)."
        return

    try:
        with MODEL_ARTIFACT_PATH.open("rb") as handle:
            artifact = pickle.load(handle)

        labels = artifact.get("labels")
        centroids = artifact.get("centroids")
        if not labels or centroids is None:
            raise ValueError("Artifact missing labels/centroids.")

        artifact["centroids"] = np.asarray(centroids, dtype=np.float32)
        artifact["sequence_length"] = int(artifact.get("sequence_length", 24))
        artifact["min_confidence"] = float(artifact.get("min_confidence", 0.58))
        artifact["confidence_scale"] = float(artifact.get("confidence_scale", 6.0))

        st.session_state.model_artifact = artifact
        st.session_state.model_error = ""
        st.session_state.model_status = (
            f"ML model loaded ({len(labels)} classes, seq={artifact['sequence_length']})."
        )

    except Exception as exc:
        st.session_state.model_artifact = None
        st.session_state.model_error = str(exc)
        st.session_state.model_status = (
            "Heuristic mode (model load failed; see DISCREPANCIES.txt)."
        )


def _required_sequence_length() -> int:
    artifact = st.session_state.get("model_artifact")
    if artifact is None:
        return 24
    return int(artifact.get("sequence_length", 24))


def _predict_token_from_model(landmark_sequence: List[List[Tuple[float, float, float]]]) -> Tuple[str, float]:
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
    if confidence < float(artifact.get("min_confidence", 0.58)):
        return "", confidence

    label = str(artifact["labels"][pred_idx])
    return label, confidence


def _release_runtime_components() -> None:
    camera: Optional[CameraManager] = st.session_state.get("camera")
    detector: Optional[HandDetector] = st.session_state.get("hand_detector")

    if camera is not None:
        camera.release()
    if detector is not None:
        detector.close()

    st.session_state.camera = None
    st.session_state.hand_detector = None


def _start_runtime() -> None:
    ok, message = _ensure_runtime_components()
    if not ok:
        st.session_state.running = False
        st.session_state.system_status = "Camera Error"
        st.session_state.status_detail = message
        return

    st.session_state.running = True
    st.session_state.paused = False
    st.session_state.system_status = "Running"
    st.session_state.status_detail = "Camera and hand detection active."


def _stop_runtime() -> None:
    _release_runtime_components()
    st.session_state.running = False
    st.session_state.paused = False
    st.session_state.system_status = "Stopped"
    st.session_state.status_detail = "System stopped. Press Start to run again."
    st.session_state.frame_failures = 0
    st.session_state.last_detected_gesture = "none"
    st.session_state.last_movement_state = "no_hand"
    st.session_state.landmark_sequence = []
    st.session_state.movement_tracker = MovementTracker()
    st.session_state.gesture_controller = GestureController()


def _clear_captions() -> None:
    st.session_state.live_words = []
    st.session_state.confirmed_sentences = []
    st.session_state.latest_event_note = "Captions cleared."
    st.session_state.event_note_frames = 35


def _undo_last_word() -> None:
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


def _confirm_sentence() -> None:
    sentence = " ".join(st.session_state.live_words).strip()
    if not sentence:
        return

    st.session_state.confirmed_sentences.append(sentence)
    st.session_state.live_words = []


def _handle_gesture_action(action: str) -> None:
    if action == "toggle_pause":
        st.session_state.paused = not st.session_state.paused
        st.session_state.system_status = "Paused" if st.session_state.paused else "Running"
        st.session_state.status_detail = (
            "Paused by open-palm gesture."
            if st.session_state.paused
            else "Resumed by open-palm gesture."
        )
    elif action == "confirm_sentence":
        _confirm_sentence()
    elif action == "undo_last_word":
        _undo_last_word()


def _predict_placeholder_token(landmarks: List[Tuple[float, float, float]]) -> Tuple[str, float]:
    """
    Placeholder for future ML model.

    Current logic is deterministic geometry-based heuristics only.
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


def _update_live_words(
    snapshot: MovementSnapshot,
    landmarks: Optional[List[Tuple[float, float, float]]],
    gesture_detected: bool,
) -> None:
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

    if st.session_state.pose_hold_frames >= 8 and st.session_state.token_cooldown == 0:
        live_words = st.session_state.live_words
        if not live_words or live_words[-1] != token:
            live_words.append(token)
        st.session_state.pose_hold_frames = 0
        st.session_state.token_cooldown = 18


def _build_overlay(note: str, hand_detected: bool, fps: float) -> OverlayInfo:
    return OverlayInfo(
        fps=fps,
        system_status=st.session_state.system_status,
        hand_detected=hand_detected,
        movement_state=st.session_state.last_movement_state,
        gesture=st.session_state.last_detected_gesture,
        note=note,
    )


def _process_single_frame() -> None:
    camera: Optional[CameraManager] = st.session_state.camera
    detector: Optional[HandDetector] = st.session_state.hand_detector
    tracker: MovementTracker = st.session_state.movement_tracker
    gestures: GestureController = st.session_state.gesture_controller

    if camera is None or detector is None:
        st.session_state.system_status = "Camera Error"
        st.session_state.status_detail = "Runtime not initialized correctly. Press Retry Camera."
        return

    if st.session_state.paused:
        st.session_state.system_status = "Paused"
        st.session_state.status_detail = "Translation paused."
        if st.session_state.last_raw_frame is not None:
            overlay = _build_overlay("Paused", hand_detected=False, fps=camera.get_fps())
            st.session_state.display_frame = draw_debug_overlay(
                st.session_state.last_raw_frame.copy(),
                overlay,
            )
        return

    ok, frame_rgb, camera_error = camera.read_frame()
    if not ok or frame_rgb is None:
        st.session_state.frame_failures += 1
        st.session_state.system_status = "Camera Error"
        st.session_state.status_detail = camera_error

        if st.session_state.last_raw_frame is not None:
            overlay = _build_overlay(
                "Frame dropped - showing last valid frame.",
                hand_detected=False,
                fps=camera.get_fps(),
            )
            st.session_state.display_frame = draw_debug_overlay(
                st.session_state.last_raw_frame.copy(),
                overlay,
            )

        if st.session_state.frame_failures >= MAX_CONSECUTIVE_FRAME_FAILURES:
            _stop_runtime()
            st.session_state.system_status = "Camera Error"
            st.session_state.status_detail = (
                "Too many consecutive frame drops. Camera stopped for safety. "
                "Press Start or Retry Camera."
            )
        return

    st.session_state.frame_failures = 0

    detection = detector.detect(frame_rgb, draw_landmarks=True)
    processed_frame = (
        detection.frame_with_landmarks
        if detection.frame_with_landmarks is not None
        else frame_rgb
    )

    if detection.error_message:
        st.session_state.system_status = "Camera Error"
        st.session_state.status_detail = (
            f"Detection error: {detection.error_message}. Showing last valid state."
        )
        if st.session_state.last_raw_frame is not None:
            processed_frame = st.session_state.last_raw_frame.copy()

    hand_detected = bool(detection.hand_detected and detection.primary_landmarks)

    if hand_detected:
        snapshot = tracker.update(detection.primary_landmarks)
        st.session_state.last_movement_state = snapshot.state

        landmark_sequence = st.session_state.landmark_sequence
        landmark_sequence.append(detection.primary_landmarks)
        max_sequence = max(_required_sequence_length() * 3, 48)
        if len(landmark_sequence) > max_sequence:
            del landmark_sequence[:-max_sequence]

        gesture_event = gestures.update(
            detection.primary_landmarks,
            snapshot.state,
            detection.handedness,
        )
        st.session_state.last_detected_gesture = gesture_event.gesture

        if gesture_event.confirmed:
            _handle_gesture_action(gesture_event.action)
            st.session_state.latest_event_note = action_feedback(gesture_event.action)
            st.session_state.event_note_frames = 35

        _update_live_words(
            snapshot,
            detection.primary_landmarks,
            gesture_detected=gesture_event.gesture != "none",
        )

        if not st.session_state.paused:
            st.session_state.system_status = "Running"
            st.session_state.status_detail = "Hand tracked successfully."
    else:
        snapshot = tracker.update(None)
        st.session_state.last_movement_state = snapshot.state
        st.session_state.last_detected_gesture = "none"
        st.session_state.landmark_sequence = []
        st.session_state.system_status = "No Hand"
        st.session_state.status_detail = "No hand detected. Keep one hand fully inside the frame."
        st.session_state.pose_hold_frames = 0
        st.session_state.last_pose_token = ""

    st.session_state.last_raw_frame = processed_frame.copy()
    overlay = _build_overlay(
        note="",
        hand_detected=hand_detected,
        fps=camera.get_fps(),
    )
    st.session_state.display_frame = draw_debug_overlay(processed_frame, overlay)


def _handle_controls() -> None:
    has_text = bool(st.session_state.live_words or st.session_state.confirmed_sentences)
    controls = render_controls(
        is_running=st.session_state.running,
        is_paused=st.session_state.paused,
        has_text=has_text,
    )

    if controls["start_stop"]:
        if st.session_state.running:
            _stop_runtime()
        else:
            _start_runtime()

    if controls["pause_resume"] and st.session_state.running:
        st.session_state.paused = not st.session_state.paused
        st.session_state.system_status = "Paused" if st.session_state.paused else "Running"
        st.session_state.status_detail = (
            "Paused via button." if st.session_state.paused else "Resumed via button."
        )

    if controls["clear"]:
        _clear_captions()

    if controls["speak"]:
        text = _full_caption_text()
        st.session_state.pending_speech = text
        st.session_state.speak_request_id += 1

    if controls["retry"]:
        _release_runtime_components()
        if st.session_state.running:
            _start_runtime()
        else:
            st.session_state.system_status = "Stopped"
            st.session_state.status_detail = "Camera reset complete. Press Start to run."


def _live_caption_text() -> str:
    return " ".join(st.session_state.live_words).strip()


def _full_caption_text() -> str:
    confirmed = join_confirmed_sentences(st.session_state.confirmed_sentences)
    live = _live_caption_text()
    if confirmed and live:
        return f"{confirmed} {live}"
    return confirmed or live


def main() -> None:
    configure_page()
    _init_state()
    _load_trained_model()

    render_header()
    render_status_indicator(st.session_state.system_status, st.session_state.status_detail)
    st.caption(st.session_state.model_status)
    _handle_controls()

    if st.session_state.running:
        ok, message = _ensure_runtime_components()
        if not ok:
            st.session_state.system_status = "Camera Error"
            st.session_state.status_detail = message
            st.session_state.running = False
            _release_runtime_components()
        else:
            try:
                _process_single_frame()
            except Exception as exc:
                st.session_state.system_status = "Camera Error"
                st.session_state.status_detail = (
                    f"Unexpected runtime error handled safely: {exc}"
                )
                if st.session_state.last_raw_frame is not None:
                    st.session_state.display_frame = st.session_state.last_raw_frame

    live_caption = _live_caption_text()
    confirmed_caption = join_confirmed_sentences(st.session_state.confirmed_sentences)

    left_col, right_col = st.columns([1, 1], gap="large")
    with left_col:
        render_caption_panel(live_caption=live_caption, confirmed_caption=confirmed_caption)
        if st.session_state.event_note_frames > 0:
            render_event_note(st.session_state.latest_event_note)
            st.session_state.event_note_frames -= 1
    with right_col:
        render_camera_panel(st.session_state.display_frame)

    if st.session_state.pending_speech:
        trigger_browser_speech(
            text=st.session_state.pending_speech,
            request_id=st.session_state.speak_request_id,
        )
        st.session_state.pending_speech = ""

    if st.session_state.running:
        # Controlled reruns keep the feed live while preserving Streamlit button events.
        time.sleep(TARGET_REFRESH_SECONDS)
        st.rerun()


if __name__ == "__main__":
    main()
