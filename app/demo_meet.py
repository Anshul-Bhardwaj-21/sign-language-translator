"""
Demo version of Meet-style UI for testing without full system integration.

Run with: streamlit run app/demo_meet.py
"""

import sys
from pathlib import Path
import time
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import streamlit as st
from ui_meet import (
    configure_meet_page, inject_meet_styles, init_meet_ui_state,
    render_status_bar, render_video_with_captions, render_control_bar,
    render_advanced_settings
)


def init_demo_state():
    """Initialize demo state for testing."""
    defaults = {
        "running": False,
        "paused": False,
        "system_status": "Stopped",
        "accessibility_mode": True,
        "current_fps": 0.0,
        "current_confidence": 0.0,
        "live_words": [],
        "confirmed_sentences": [],
        "pending_speech": "",
        "speak_request_id": 0,
        "last_movement_state": "no_hand",
        "display_frame": None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def create_demo_frame():
    """Create a demo video frame for testing."""
    # Create a simple demo frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[:, :, 0] = 50  # Dark background
    frame[:, :, 1] = 50
    frame[:, :, 2] = 50
    
    # Add some demo content
    frame[200:280, 270:370] = [100, 150, 200]  # Demo rectangle
    
    return frame


def main_demo():
    """Demo version of Meet-style UI."""
    # Configure page and inject styles
    configure_meet_page()
    inject_meet_styles()
    init_meet_ui_state()
    init_demo_state()
    
    # Demo title
    st.markdown("# 🎥 Meet-Style UI Demo")
    st.markdown("**Professional Google Meet/Zoom-style interface for sign language translation**")
    
    # Get current state
    fps = st.session_state.current_fps
    hand_detected = st.session_state.last_movement_state != 'no_hand'
    gesture_stable = st.session_state.last_movement_state in {'stable', 'idle'}
    system_status = st.session_state.system_status
    accessibility_mode = st.session_state.accessibility_mode
    confidence = st.session_state.current_confidence
    
    # Render status bar
    render_status_bar(
        fps=fps,
        hand_detected=hand_detected,
        accessibility_mode=accessibility_mode,
        system_status=system_status,
        confidence=confidence,
        gesture_stable=gesture_stable
    )
    
    # Demo captions
    live_caption = " ".join(st.session_state.live_words) if st.session_state.live_words else ""
    confirmed_caption = " ".join(st.session_state.confirmed_sentences) if st.session_state.confirmed_sentences else ""
    has_text = bool(live_caption or confirmed_caption)
    
    # Render video with captions
    display_frame = st.session_state.display_frame
    camera_error = None
    
    if st.session_state.system_status == 'Camera Error':
        camera_error = "Demo camera error for testing"
    elif st.session_state.running and display_frame is None:
        display_frame = create_demo_frame()
        st.session_state.display_frame = display_frame
    
    render_video_with_captions(
        frame=display_frame,
        live_caption=live_caption or "Demo live caption text",
        confirmed_caption=confirmed_caption or "Demo confirmed transcript text",
        accessibility_mode=accessibility_mode,
        camera_error=camera_error
    )
    
    # Render control bar and handle actions
    is_running = st.session_state.running
    is_paused = st.session_state.paused
    
    actions = render_control_bar(
        is_running=is_running,
        is_paused=is_paused,
        accessibility_mode=accessibility_mode,
        has_text=has_text
    )
    
    # Handle button actions
    if actions.get('camera_toggle'):
        st.session_state.running = not is_running
        if st.session_state.running:
            st.session_state.system_status = "Running"
            st.session_state.current_fps = 15.0
            st.session_state.last_movement_state = "stable"
            st.session_state.current_confidence = 0.85
        else:
            st.session_state.system_status = "Stopped"
            st.session_state.current_fps = 0.0
            st.session_state.last_movement_state = "no_hand"
            st.session_state.current_confidence = 0.0
            st.session_state.display_frame = None
        st.rerun()
    
    if actions.get('accessibility_toggle'):
        st.session_state.accessibility_mode = not accessibility_mode
        st.rerun()
    
    if actions.get('pause_toggle') and is_running:
        st.session_state.paused = not is_paused
        st.session_state.system_status = "Paused" if not is_paused else "Running"
        st.rerun()
    
    if actions.get('clear'):
        st.session_state.live_words = []
        st.session_state.confirmed_sentences = []
        st.rerun()
    
    if actions.get('speak'):
        st.session_state.pending_speech = "Demo speech synthesis"
        st.session_state.speak_request_id += 1
        st.success("🔊 Speech synthesis triggered (demo)")
    
    # Advanced settings
    render_advanced_settings()
    
    # Demo controls
    with st.expander("🎮 Demo Controls", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Add Demo Caption"):
                st.session_state.live_words.append("HELLO")
                st.rerun()
            
            if st.button("Confirm Sentence"):
                if st.session_state.live_words:
                    sentence = " ".join(st.session_state.live_words)
                    st.session_state.confirmed_sentences.append(sentence)
                    st.session_state.live_words = []
                    st.rerun()
        
        with col2:
            if st.button("Simulate Camera Error"):
                st.session_state.system_status = "Camera Error"
                st.session_state.running = False
                st.rerun()
            
            if st.button("Reset Demo"):
                for key in ["live_words", "confirmed_sentences", "running", "paused"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    
    # Show current state for debugging
    with st.expander("🔍 Debug State", expanded=False):
        st.json({
            "running": is_running,
            "paused": is_paused,
            "accessibility_mode": accessibility_mode,
            "system_status": system_status,
            "fps": fps,
            "confidence": confidence,
            "has_text": has_text,
            "live_words": st.session_state.live_words,
            "confirmed_sentences": st.session_state.confirmed_sentences,
        })
    
    # Auto-refresh for demo
    if is_running:
        time.sleep(0.1)
        st.rerun()


if __name__ == "__main__":
    main_demo()