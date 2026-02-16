"""
Meet-style UI for Sign Language Translator

This module provides a Google Meet/Zoom-style interface for the sign language translator.
The design prioritizes familiar video call patterns that judges will immediately recognize
as a professional video communication product.

WHY Meet-style UI:
- Judges expect familiar video call interfaces
- Large central video maximizes gesture visibility
- Professional dark theme reduces eye strain
- Circular control buttons match modern video apps
- Accessibility features are prominently displayed
"""

from __future__ import annotations

import time
from typing import Dict, Optional
import numpy as np
import streamlit as st
import streamlit.components.v1 as components


def configure_meet_page() -> None:
    """
    Configure Streamlit page for Meet-style video call experience.
    
    WHY these settings:
    - Wide layout maximizes video real estate (Meet/Zoom pattern)
    - Collapsed sidebar keeps focus on video call interface  
    - Dark theme matches modern video call applications
    - Hidden menu/footer creates clean demo appearance
    """
    st.set_page_config(
        page_title="Sign Language Video Call",
        page_icon="🤟",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )


def inject_meet_styles() -> None:
    """
    Inject comprehensive CSS for Meet-style dark theme interface.
    
    WHY CSS injection approach:
    - Streamlit default styling breaks video call immersion
    - Meet-style requires precise control over colors and layout
    - CSS injection is more maintainable than inline styles
    - Allows for responsive design across screen sizes
    """
    css = """
    <style>
    /* ===== GLOBAL RESET ===== */
    /* WHY: Remove Streamlit default padding/margins for full-screen video experience */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: none !important;
    }
    
    /* Hide Streamlit branding for clean demo */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* ===== MEET-STYLE DARK THEME ===== */
    /* WHY: #202124 matches Google Meet's exact background color */
    .stApp {
        background-color: #202124 !important;
    }
    
    /* High contrast text for accessibility */
    .stApp, .stApp * {
        color: #e8eaed !important;
    }
    
    /* ===== STATUS BAR STYLING ===== */
    .meet-status-bar {
        background: rgba(60, 64, 67, 0.8);
        border-radius: 8px;
        padding: 8px 16px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(95, 99, 104, 0.3);
    }
    
    .status-metrics {
        display: flex;
        gap: 16px;
        align-items: center;
    }
    
    .status-metric {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 0.875rem;
    }
    
    .fps-good { color: #34a853 !important; }
    .fps-warning { color: #fbbc04 !important; }
    .fps-error { color: #ea4335 !important; }
    
    .hand-detected { color: #34a853 !important; }
    .hand-not-detected { color: #9aa0a6 !important; }
    
    .accessibility-badge {
        background: linear-gradient(135deg, #8e24aa, #ab47bc);
        color: white !important;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.75rem;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(142, 36, 170, 0.3);
        animation: accessibilityPulse 2s ease-in-out infinite;
    }
    
    @keyframes accessibilityPulse {
        0%, 100% { box-shadow: 0 2px 8px rgba(142, 36, 170, 0.3); }
        50% { box-shadow: 0 2px 16px rgba(142, 36, 170, 0.6); }
    }
    
    /* ===== VIDEO CONTAINER STYLING ===== */
    .meet-video-container {
        position: relative;
        width: 100%;
        aspect-ratio: 16/9;
        background: #000;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        margin-bottom: 16px;
    }
    
    .meet-video-container img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        background: #000;
    }
    
    .video-error-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        color: #e8eaed;
        text-align: center;
        padding: 2rem;
    }
    
    .video-error-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.6;
    }
    
    /* ===== CAPTION OVERLAY STYLING ===== */
    .caption-overlay {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
        padding: 2rem 1.5rem 1rem;
        color: white;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .caption-overlay.accessibility-active {
        background: linear-gradient(transparent, rgba(142, 36, 170, 0.3), rgba(0, 0, 0, 0.8));
        box-shadow: 0 -4px 16px rgba(142, 36, 170, 0.2);
    }
    
    .live-caption {
        font-size: 1.5rem;
        font-weight: 500;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
        margin-bottom: 0.5rem;
        min-height: 2rem;
        line-height: 1.3;
        animation: fadeIn 0.3s ease-in-out;
    }
    
    .confirmed-caption {
        font-size: 1rem;
        color: #bdc1c6;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
        opacity: 0.9;
        line-height: 1.4;
        max-height: 4rem;
        overflow-y: auto;
        scrollbar-width: thin;
        scrollbar-color: rgba(255, 255, 255, 0.3) transparent;
    }
    
    /* Smooth text updates animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Custom scrollbar for confirmed captions */
    .confirmed-caption::-webkit-scrollbar {
        width: 4px;
    }
    
    .confirmed-caption::-webkit-scrollbar-track {
        background: transparent;
    }
    
    .confirmed-caption::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.3);
        border-radius: 2px;
    }
    
    .confirmed-caption::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.5);
    }
    
    /* ===== CONTROL BAR STYLING ===== */
    .meet-control-bar {
        display: flex;
        justify-content: center;
        gap: 16px;
        padding: 16px;
        background: rgba(60, 64, 67, 0.8);
        border-radius: 12px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(95, 99, 104, 0.3);
    }
    
    .control-button {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        background: none;
        border: none;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .control-icon {
        width: 56px;
        height: 56px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        background: rgba(95, 99, 104, 0.6);
        color: #e8eaed;
        transition: all 0.2s ease;
    }
    
    .control-button:hover .control-icon {
        background: rgba(95, 99, 104, 0.8);
        transform: scale(1.05);
    }
    
    .control-button.active .control-icon {
        background: #1a73e8;
        color: white;
    }
    
    .control-button.accessibility-active .control-icon {
        background: linear-gradient(135deg, #8e24aa, #ab47bc);
        color: white;
        box-shadow: 0 0 16px rgba(142, 36, 170, 0.4);
        animation: accessibilityGlow 2s ease-in-out infinite;
    }
    
    @keyframes accessibilityGlow {
        0%, 100% { box-shadow: 0 0 16px rgba(142, 36, 170, 0.4); }
        50% { box-shadow: 0 0 24px rgba(142, 36, 170, 0.7); }
    }
    
    .control-button.disabled .control-icon {
        background: rgba(95, 99, 104, 0.3);
        color: rgba(232, 234, 237, 0.4);
        cursor: not-allowed;
    }
    
    .control-label {
        font-size: 0.75rem;
        color: #bdc1c6;
        text-align: center;
        white-space: nowrap;
    }
    
    /* ===== STREAMLIT WIDGET OVERRIDES ===== */
    /* WHY: Make Streamlit widgets fit dark Meet theme */
    .stButton > button {
        background: rgba(60, 64, 67, 0.8) !important;
        color: #e8eaed !important;
        border: 1px solid rgba(95, 99, 104, 0.3) !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background: rgba(95, 99, 104, 0.8) !important;
        border-color: rgba(138, 180, 248, 0.5) !important;
        transform: translateY(-1px) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Expander styling for advanced settings */
    .streamlit-expanderHeader {
        background: rgba(60, 64, 67, 0.5) !important;
        border-radius: 8px !important;
        color: #e8eaed !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(32, 33, 36, 0.8) !important;
        border-radius: 0 0 8px 8px !important;
        border: 1px solid rgba(95, 99, 104, 0.3) !important;
    }
    
    /* ===== RESPONSIVE DESIGN ===== */
    @media (max-width: 768px) {
        .meet-control-bar {
            gap: 12px;
            padding: 12px;
        }
        
        .control-icon {
            width: 48px;
            height: 48px;
            font-size: 1.25rem;
        }
        
        .live-caption {
            font-size: 1.25rem;
        }
        
        .status-metrics {
            gap: 12px;
        }
    }
    
    /* ===== LOBBY STYLING ===== */
    /* Lobby-specific styles for pre-join screen */
    .stTextInput > div > div > input {
        background-color: #3c4043 !important;
        border: 1px solid #5f6368 !important;
        border-radius: 8px !important;
        color: #e8eaed !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #8ab4f8 !important;
        box-shadow: 0 0 0 1px #8ab4f8 !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #9aa0a6 !important;
    }
    
    /* Primary button styling for Join Meeting */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1a73e8, #4285f4) !important;
        border: none !important;
        border-radius: 24px !important;
        color: white !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        padding: 12px 32px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(26, 115, 232, 0.3) !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1557b0, #3367d6) !important;
        box-shadow: 0 4px 12px rgba(26, 115, 232, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    
    .stButton > button[kind="primary"]:disabled {
        background: #3c4043 !important;
        color: #5f6368 !important;
        box-shadow: none !important;
        transform: none !important;
    }
    
    /* Checkbox styling for accessibility preview */
    .stCheckbox > label {
        color: #9aa0a6 !important;
    }
    
    .stCheckbox > label > div[data-testid="stCheckbox"] > div {
        background-color: #3c4043 !important;
        border-color: #5f6368 !important;
    }
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)


def render_status_bar(
    fps: float,
    hand_detected: bool,
    accessibility_mode: bool,
    system_status: str,
    confidence: float = 0.0,
    gesture_stable: bool = False,
) -> None:
    """
    Render top status bar with system metrics and accessibility badge.
    
    WHY this layout:
    - Left-aligned metrics for technical monitoring
    - Right-aligned accessibility badge for prominence
    - Color coding provides instant visual feedback
    - Semi-transparent background maintains video focus
    - Additional metrics (confidence, stability) for technical users
    """
    # Determine FPS color coding (Requirements 5.1)
    if fps >= 15:
        fps_class = "fps-good"
        fps_icon = "📊"
    elif fps >= 10:
        fps_class = "fps-warning"
        fps_icon = "⚠️"
    else:
        fps_class = "fps-error"
        fps_icon = "🔴"
    
    # Hand detection status with enhanced feedback (Requirements 5.2)
    if hand_detected:
        if gesture_stable:
            hand_class = "fps-good"
            hand_icon = "✋"
            hand_text = "Hand Stable"
        else:
            hand_class = "fps-warning"
            hand_icon = "👋"
            hand_text = "Hand Moving"
    else:
        hand_class = "hand-not-detected"
        hand_icon = "🚫"
        hand_text = "No Hand"
    
    # System status with appropriate icons (Requirements 5.3)
    status_icons = {
        "Running": "🟢",
        "Paused": "⏸️",
        "Stopped": "⏹️",
        "Camera Error": "❌",
        "No Hand": "👀",
        "Ready": "✅"
    }
    status_icon = status_icons.get(system_status, "🔄")
    
    # Build metrics HTML
    metrics_html = f"""
        <div class="status-metric">
            <span>{fps_icon}</span>
            <span class="{fps_class}">{fps:.1f} FPS</span>
        </div>
        <div class="status-metric">
            <span>{hand_icon}</span>
            <span class="{hand_class}">{hand_text}</span>
        </div>
        <div class="status-metric">
            <span>{status_icon}</span>
            <span>{system_status}</span>
        </div>
    """
    
    # Add confidence metric if available
    if confidence > 0:
        confidence_class = "fps-good" if confidence > 0.7 else "fps-warning" if confidence > 0.5 else "fps-error"
        metrics_html += f"""
        <div class="status-metric">
            <span>🎯</span>
            <span class="{confidence_class}">{confidence:.0%}</span>
        </div>
        """
    
    # Accessibility badge (Requirements 5.4)
    accessibility_badge = ""
    if accessibility_mode:
        accessibility_badge = '<div class="accessibility-badge">🔍 Accessibility Mode</div>'
    
    status_html = f"""
    <div class="meet-status-bar">
        <div class="status-metrics">
            {metrics_html}
        </div>
        {accessibility_badge}
    </div>
    """
    
    st.markdown(status_html, unsafe_allow_html=True)


def render_video_with_captions(
    frame: Optional[np.ndarray],
    live_caption: str,
    confirmed_caption: str,
    accessibility_mode: bool,
    camera_error: Optional[str] = None,
) -> None:
    """
    Render central 16:9 video feed with overlaid captions.
    
    CRITICAL: This function implements video flicker prevention by:
    1. Only rendering video when video_needs_update=True
    2. Preserving last stable frame during state changes
    3. Using render lock to prevent concurrent updates
    """
    # Prevent concurrent video updates
    if st.session_state.get('video_render_lock', False):
        return
    
    # Preserve stable frame for flicker prevention
    if frame is not None and not camera_error:
        st.session_state.last_stable_frame = frame
    
    # Determine which frame to display
    display_frame = frame
    if display_frame is None and not camera_error:
        display_frame = st.session_state.get('last_stable_frame')
    
    # Only update video if needed (prevents button-triggered rerenders)
    should_render_video = st.session_state.get('video_needs_update', True)
    
    if camera_error or display_frame is None:
        # Always show error overlay immediately
        error_icon = "📷" if camera_error and "camera" in camera_error.lower() else "⚠️"
        error_message = camera_error or "No video feed available"
        
        # Determine error type for better user guidance
        if camera_error:
            if "permission" in camera_error.lower():
                error_icon = "🔒"
                guidance = "Enable camera permissions in your browser settings"
            elif "not found" in camera_error.lower() or "unavailable" in camera_error.lower():
                error_icon = "📷"
                guidance = "Check that your camera is connected and not in use by another app"
            else:
                error_icon = "⚠️"
                guidance = "Try refreshing the page or restarting the application"
        else:
            guidance = "Check camera permissions and try refreshing the page"
        
        video_html = f"""
        <div class="meet-video-container">
            <div class="video-error-overlay">
                <div class="video-error-icon">{error_icon}</div>
                <h3>Video Unavailable</h3>
                <p>{error_message}</p>
                <p style="opacity: 0.7; margin-top: 1rem; font-size: 0.9rem;">
                    {guidance}
                </p>
            </div>
        """
    else:
        # Only render video if update is needed
        if should_render_video:
            st.session_state.video_render_lock = True
            try:
                # Use Streamlit's image component for video display
                col1, col2, col3 = st.columns([1, 8, 1])  # Center the video
                with col2:
                    st.image(display_frame, use_column_width=True, channels="RGB")
                
                # Mark video as updated
                st.session_state.video_needs_update = False
            finally:
                st.session_state.video_render_lock = False
        else:
            # Skip video render but still show container for captions
            pass
    
    # Always render captions (they update independently of video)
    accessibility_class = "accessibility-active" if accessibility_mode else ""
    
    # Ensure captions are properly formatted and not empty
    display_live = live_caption.strip() if live_caption else ""
    display_confirmed = confirmed_caption.strip() if confirmed_caption else ""
    
    # Show placeholder when no captions available
    if not display_live and not display_confirmed:
        display_live = "Listening for sign language..."
    
    caption_html = f"""
    <div class="caption-overlay {accessibility_class}">
        <div class="live-caption">{display_live}</div>
        {f'<div class="confirmed-caption">{display_confirmed}</div>' if display_confirmed else ''}
    </div>
    """
    
    # Render captions overlay
    if camera_error or display_frame is None:
        # Complete error container with captions
        video_html += caption_html + '</div>'
        st.markdown(video_html, unsafe_allow_html=True)
    else:
        # Captions over video (positioned below st.image)
        st.markdown(f"""
        <div style="position: relative; margin-top: -2rem;">
            {caption_html}
        </div>
        """, unsafe_allow_html=True)


def render_control_bar(
    is_running: bool,
    is_paused: bool,
    accessibility_mode: bool,
    has_text: bool,
) -> Dict[str, bool]:
    """
    Render bottom control bar with circular icon buttons.
    
    WHY 8-column layout:
    - Matches Google Meet button arrangement (Requirements 4.1)
    - Provides space for future features (mic, leave meeting)
    - Circular buttons are touch-friendly and modern (Requirements 8.5)
    - Active states provide clear visual feedback (Requirements 8.3, 8.4)
    
    Returns:
        Dict of button states for action handling
    """
    # Initialize actions dictionary
    actions = {}
    
    # Create control bar container
    st.markdown('<div class="meet-control-bar">', unsafe_allow_html=True)
    
    # Create 8 columns for control buttons
    cols = st.columns(8)
    
    # Column 1: Microphone (placeholder) - Requirements 4.2
    with cols[0]:
        st.markdown("""
        <div class="control-button disabled">
            <div class="control-icon">🎤</div>
            <div class="control-label">Mic</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Column 2: Camera toggle - Requirements 4.3
    with cols[1]:
        camera_icon = "📹" if is_running else "📷"
        camera_class = "active" if is_running else ""
        camera_label = "Stop" if is_running else "Start"
        
        # Use invisible button with custom styling
        if st.button(" ", key="camera_toggle", help=f"{camera_label} Camera"):
            actions["camera_toggle"] = True
        
        # Custom button styling overlay
        st.markdown(f"""
        <div style="margin-top: -3.5rem; pointer-events: none;">
            <div class="control-button {camera_class}">
                <div class="control-icon">{camera_icon}</div>
                <div class="control-label">{camera_label}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Column 3: Accessibility mode toggle - Requirements 4.4, 6.1
    with cols[2]:
        accessibility_class = "accessibility-active" if accessibility_mode else ""
        accessibility_label = "Accessibility"
        
        if st.button(" ", key="accessibility_toggle", help="Toggle Accessibility Mode"):
            actions["accessibility_toggle"] = True
        
        st.markdown(f"""
        <div style="margin-top: -3.5rem; pointer-events: none;">
            <div class="control-button {accessibility_class}">
                <div class="control-icon">🔍</div>
                <div class="control-label">{accessibility_label}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Column 4: Pause/Resume recognition - Requirements 4.5
    with cols[3]:
        pause_icon = "▶️" if is_paused else "⏸️"
        pause_label = "Resume" if is_paused else "Pause"
        pause_class = "active" if is_paused else ""
        disabled_class = "disabled" if not is_running else ""
        
        # Only allow interaction if camera is running
        if is_running:
            if st.button(" ", key="pause_toggle", help=f"{pause_label} Recognition"):
                actions["pause_toggle"] = True
        
        st.markdown(f"""
        <div style="margin-top: -3.5rem; pointer-events: none;">
            <div class="control-button {pause_class} {disabled_class}">
                <div class="control-icon">{pause_icon}</div>
                <div class="control-label">{pause_label}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Column 5: Clear captions - Requirements 4.6
    with cols[4]:
        disabled_class = "disabled" if not has_text else ""
        
        if has_text:
            if st.button(" ", key="clear_captions", help="Clear All Captions"):
                actions["clear"] = True
        
        st.markdown(f"""
        <div style="margin-top: -3.5rem; pointer-events: none;">
            <div class="control-button {disabled_class}">
                <div class="control-icon">🗑️</div>
                <div class="control-label">Clear</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Column 6: Speak captions - Requirements 4.7
    with cols[5]:
        disabled_class = "disabled" if not has_text else ""
        
        if has_text:
            if st.button(" ", key="speak_captions", help="Speak Current Captions"):
                actions["speak"] = True
        
        st.markdown(f"""
        <div style="margin-top: -3.5rem; pointer-events: none;">
            <div class="control-button {disabled_class}">
                <div class="control-icon">🔊</div>
                <div class="control-label">Speak</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Column 7: Settings (placeholder)
    with cols[6]:
        st.markdown("""
        <div class="control-button disabled">
            <div class="control-icon">⚙️</div>
            <div class="control-label">Settings</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Column 8: Leave meeting (placeholder) - Requirements 4.8
    with cols[7]:
        st.markdown("""
        <div class="control-button disabled">
            <div class="control-icon">📞</div>
            <div class="control-label">Leave</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Close control bar container
    st.markdown('</div>', unsafe_allow_html=True)
    
    return actions


def render_advanced_settings() -> None:
    """
    Render collapsible advanced settings panel.
    
    WHY collapsible design:
    - Keeps main UI clean and focused on video call experience
    - Provides access to technical controls for power users
    - Phase 1 constraint: reuses existing controls without redesign
    """
    with st.expander("⚙️ Advanced Settings", expanded=False):
        st.info("🚧 Advanced Settings are non-blocking and may reuse existing controls without visual redesign in Phase 1.")
        
        # Placeholder for future advanced settings
        st.write("**Gesture Recognition Settings**")
        st.write("- Smoothing window, confidence threshold, hold frames")
        
        st.write("**Display Options**") 
        st.write("- Debug overlay, landmark visualization")
        
        st.write("**TTS Configuration**")
        st.write("- Speech speed, voice selection")


# Module initialization functions
def init_meet_ui_state() -> None:
    """Initialize Meet-style UI specific session state variables."""
    meet_defaults = {
        "meeting_state": "LOBBY",  # Start in lobby
        "room_code": "",
        "video_needs_update": True,
        "ui_state_changed": False,
        "last_stable_frame": None,
        "button_action_pending": False,
        "video_render_lock": False,
        "state_transition_lock": False,
    }
    
    for key, value in meet_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def validate_state_transition(from_state: str, to_state: str, context: str) -> bool:
    """
    Validate state transitions according to Meet UI state machine rules.
    
    WHY state validation:
    - Prevents invalid transitions (e.g., pause recognition when camera OFF)
    - Blocks rapid button clicks that cause race conditions
    - Ensures UI behaves predictably across all interactions
    
    Args:
        from_state: Current state
        to_state: Desired state
        context: Context of transition (camera, recognition, accessibility)
    
    Returns:
        True if transition is valid, False otherwise
    """
    # Check for transition lock (debouncing)
    if st.session_state.get('state_transition_lock', False):
        return False
    
    # Camera state transitions
    if context == "camera":
        valid_transitions = {
            "OFF": ["ON"],
            "ON": ["OFF", "ERROR"],
            "ERROR": ["OFF"]
        }
        return to_state in valid_transitions.get(from_state, [])
    
    # Recognition state transitions (Requirements 10.1, 10.2)
    elif context == "recognition":
        camera_running = st.session_state.get('running', False)
        
        # Recognition can only be controlled when camera is ON
        if not camera_running and to_state in ["RUNNING", "PAUSED"]:
            return False
        
        valid_transitions = {
            "STOPPED": ["RUNNING"] if camera_running else [],
            "RUNNING": ["PAUSED", "STOPPED"],
            "PAUSED": ["RUNNING", "STOPPED"]
        }
        return to_state in valid_transitions.get(from_state, [])
    
    # Accessibility state transitions (always valid)
    elif context == "accessibility":
        return to_state in ["ON", "OFF"]
    
    return False


def execute_state_transition(context: str, new_state: str) -> bool:
    """
    Execute a validated state transition with proper locking.
    
    Args:
        context: State context (camera, recognition, accessibility)
        new_state: New state to transition to
    
    Returns:
        True if transition was successful, False otherwise
    """
    # Set transition lock to prevent race conditions (Requirements 10.3)
    st.session_state.state_transition_lock = True
    
    try:
        if context == "camera":
            if new_state == "ON":
                st.session_state.running = True
                st.session_state.system_status = "Running"
            elif new_state == "OFF":
                st.session_state.running = False
                st.session_state.paused = False  # Reset recognition state
                st.session_state.system_status = "Stopped"
            elif new_state == "ERROR":
                st.session_state.running = False
                st.session_state.paused = False
                st.session_state.system_status = "Camera Error"
        
        elif context == "recognition":
            if new_state == "RUNNING":
                st.session_state.paused = False
                st.session_state.system_status = "Running"
            elif new_state == "PAUSED":
                st.session_state.paused = True
                st.session_state.system_status = "Paused"
            elif new_state == "STOPPED":
                st.session_state.paused = False
                # Don't change system_status here - let camera state control it
        
        elif context == "accessibility":
            st.session_state.accessibility_mode = (new_state == "ON")
        
        # Mark UI as changed for rerun control
        st.session_state.ui_state_changed = True
        return True
        
    except Exception:
        return False
    
    finally:
        # Release transition lock
        st.session_state.state_transition_lock = False


def get_current_state(context: str) -> str:
    """Get current state for a given context."""
    if context == "camera":
        if st.session_state.get('system_status') == 'Camera Error':
            return "ERROR"
        elif st.session_state.get('running', False):
            return "ON"
        else:
            return "OFF"
    
    elif context == "recognition":
        if not st.session_state.get('running', False):
            return "STOPPED"
        elif st.session_state.get('paused', False):
            return "PAUSED"
        else:
            return "RUNNING"
    
    elif context == "accessibility":
        return "ON" if st.session_state.get('accessibility_mode', True) else "OFF"
    
    return "UNKNOWN"


def render_meeting_lobby() -> None:
    """
    Render the meeting lobby screen with room code input and join button.
    
    This screen appears before the main Meet UI and does not initialize
    camera or runtime components.
    """
    # Center the lobby content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # App title with icon
        st.markdown("""
        <div style="text-align: center; margin-bottom: 3rem;">
            <h1 style="color: #e8eaed; font-size: 2.5rem; margin-bottom: 0.5rem;">
                🤟 Sign Language Video Call
            </h1>
            <p style="color: #9aa0a6; font-size: 1.1rem;">
                Join a meeting to start translating sign language
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Room code input
        st.markdown("""
        <div style="margin-bottom: 2rem;">
            <label style="color: #e8eaed; font-size: 1rem; margin-bottom: 0.5rem; display: block;">
                Meeting Room Code
            </label>
        </div>
        """, unsafe_allow_html=True)
        
        room_code = st.text_input(
            "Meeting Room Code",
            value=st.session_state.get('room_code', ''),
            placeholder="Enter room code (e.g., abc-def-ghi)",
            key="room_code_input",
            label_visibility="collapsed"
        )
        
        # Update session state
        st.session_state.room_code = room_code
        
        # Join button
        st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
        
        join_disabled = not room_code.strip()
        
        if st.button(
            "Join Meeting",
            disabled=join_disabled,
            use_container_width=True,
            type="primary"
        ):
            # Set meeting state to IN_CALL and trigger rerun
            st.session_state.meeting_state = "IN_CALL"
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Accessibility toggle (visible but disabled in lobby)
        st.markdown("""
        <div style="margin-top: 3rem; text-align: center;">
            <p style="color: #9aa0a6; font-size: 0.9rem; margin-bottom: 1rem;">
                Accessibility features will be available after joining
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Disabled accessibility toggle for preview
        st.checkbox(
            "Enable accessibility mode",
            value=True,
            disabled=True,
            help="This will be enabled after joining the meeting"
        )


def main_meet_ui() -> None:
    """
    Main entry point for Meet-style UI.
    
    CRITICAL: This function implements video flicker prevention by isolating
    video rendering from button state changes. Button actions are batched
    and processed without triggering video rerenders.
    """
    # Configure page and inject styles
    configure_meet_page()
    inject_meet_styles()
    init_meet_ui_state()
    
    # Check meeting state - render lobby if not in call
    if st.session_state.get('meeting_state', 'LOBBY') == 'LOBBY':
        render_meeting_lobby()
        return
    
    # Import existing system functions (avoiding circular imports)
    try:
        from old_streamlit_app.main import (
            _init_state, _load_trained_model, _ensure_runtime_components,
            _process_single_frame, _start_runtime, _stop_runtime,
            _clear_captions, _live_caption_text, _full_caption_text,
            join_confirmed_sentences, trigger_browser_speech
        )
    except ImportError:
        st.error("Could not import existing system functions. Please ensure old_streamlit_app/main.py is available.")
        return
    
    # Initialize existing system state
    _init_state()
    _load_trained_model()
    
    # Check if we have pending button actions (batch processing)
    button_action_pending = st.session_state.get('button_action_pending', False)
    
    # Get current system state
    fps = st.session_state.get('current_fps', 0.0)
    hand_detected = st.session_state.get('last_movement_state', 'no_hand') != 'no_hand'
    gesture_stable = st.session_state.get('last_movement_state', '') in {'stable', 'idle'}
    system_status = st.session_state.get('system_status', 'Stopped')
    accessibility_mode = st.session_state.get('accessibility_mode', True)
    confidence = st.session_state.get('current_confidence', 0.0)
    
    # Render status bar
    render_status_bar(
        fps=fps,
        hand_detected=hand_detected,
        accessibility_mode=accessibility_mode,
        system_status=system_status,
        confidence=confidence,
        gesture_stable=gesture_stable
    )
    
    # Get caption text
    live_caption = _live_caption_text()
    confirmed_caption = join_confirmed_sentences(st.session_state.get('confirmed_sentences', []))
    has_text = bool(live_caption or confirmed_caption)
    
    # Check for camera errors
    display_frame = st.session_state.get('display_frame')
    camera_error = None
    if st.session_state.get('system_status') == 'Camera Error':
        camera_error = st.session_state.get('status_detail', 'Camera error occurred')
    
    # Render video with captions (flicker-protected)
    render_video_with_captions(
        frame=display_frame,
        live_caption=live_caption,
        confirmed_caption=confirmed_caption,
        accessibility_mode=accessibility_mode,
        camera_error=camera_error
    )
    
    # Render control bar and handle actions
    is_running = st.session_state.get('running', False)
    is_paused = st.session_state.get('paused', False)
    
    actions = render_control_bar(
        is_running=is_running,
        is_paused=is_paused,
        accessibility_mode=accessibility_mode,
        has_text=has_text
    )
    
    # Batch button actions to prevent video flicker
    if actions and not button_action_pending:
        st.session_state.button_action_pending = True
        
        # Process all button actions without triggering video rerenders
        if actions.get('camera_toggle'):
            current_camera_state = get_current_state("camera")
            new_camera_state = "OFF" if current_camera_state == "ON" else "ON"
            
            if validate_state_transition(current_camera_state, new_camera_state, "camera"):
                if execute_state_transition("camera", new_camera_state):
                    # CRITICAL: Only call runtime functions, never modify them
                    if new_camera_state == "ON":
                        _start_runtime()
                        # Mark video for update when camera starts
                        st.session_state.video_needs_update = True
                    else:
                        _stop_runtime()
        
        if actions.get('accessibility_toggle'):
            current_accessibility_state = get_current_state("accessibility")
            new_accessibility_state = "OFF" if current_accessibility_state == "ON" else "ON"
            
            if validate_state_transition(current_accessibility_state, new_accessibility_state, "accessibility"):
                execute_state_transition("accessibility", new_accessibility_state)
        
        if actions.get('pause_toggle'):
            current_recognition_state = get_current_state("recognition")
            new_recognition_state = "RUNNING" if current_recognition_state == "PAUSED" else "PAUSED"
            
            if validate_state_transition(current_recognition_state, new_recognition_state, "recognition"):
                if execute_state_transition("recognition", new_recognition_state):
                    st.session_state.status_detail = (
                        "Paused via Meet UI." if new_recognition_state == "PAUSED" 
                        else "Resumed via Meet UI."
                    )
        
        if actions.get('clear'):
            _clear_captions()
        
        if actions.get('speak'):
            text = _full_caption_text()
            st.session_state.pending_speech = text
            st.session_state.speak_request_id = st.session_state.get('speak_request_id', 0) + 1
        
        # Clear pending flag and trigger single rerun
        st.session_state.button_action_pending = False
        st.rerun()
    
    # Advanced settings (Phase 1 constraint: reuse existing controls)
    render_advanced_settings()
    
    # Handle speech synthesis
    if st.session_state.get('pending_speech'):
        trigger_browser_speech(
            text=st.session_state.pending_speech,
            request_id=st.session_state.get('speak_request_id', 0),
        )
        st.session_state.pending_speech = ""
    
    # Process video frame if running (NEVER modify this logic)
    if is_running:
        ok, message = _ensure_runtime_components()
        if not ok:
            st.session_state.system_status = "Camera Error"
            st.session_state.status_detail = message
            st.session_state.running = False
        else:
            try:
                _process_single_frame()
                # Mark video for update when new frame arrives
                if st.session_state.get('display_frame') is not None:
                    st.session_state.video_needs_update = True
            except Exception as exc:
                st.session_state.system_status = "Camera Error"
                st.session_state.status_detail = f"Runtime error: {exc}"
    
    # Controlled reruns for live video (only when running and no button actions)
    if is_running and not button_action_pending:
        time.sleep(0.05)  # TARGET_REFRESH_SECONDS
        st.rerun()


if __name__ == "__main__":
    main_meet_ui()