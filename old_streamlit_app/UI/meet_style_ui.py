"""
Google Meet / Zoom style UI for Sign Language Accessibility Video Call.

WHY THIS DESIGN:
- Judges need to understand "video call product" in 5 seconds
- Large central video = familiar video call pattern
- Bottom control bar = Meet/Zoom muscle memory
- Captions overlaid on video = live captioning UX
- Minimal chrome = focus on communication
"""

from __future__ import annotations

import json
from typing import Dict, Optional

import numpy as np
import streamlit as st
import streamlit.components.v1 as components


def configure_meet_page() -> None:
    """
    Configure page for Meet-style video call experience.
    
    WHY: Wide layout, dark theme, minimal UI chrome.
    Collapsed sidebar keeps focus on video call.
    """
    st.set_page_config(
        page_title="Accessibility Video Call",
        page_icon="🎥",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_meet_styles()


def inject_meet_styles() -> None:
    """
    Inject CSS for Meet-style video call interface.
    
    WHY THESE STYLES:
    - Dark background = video call standard (Meet, Zoom)
    - Large video container = central focus
    - Overlaid captions = live captioning UX
    - Bottom control bar = familiar pattern
    - High contrast = accessibility requirement
    """
    st.markdown(
        """
        <style>
            /* ===== GLOBAL RESET ===== */
            /* WHY: Remove Streamlit default padding/margins for full-screen video experience */
            .main .block-container {
                padding-top: 1rem !important;
                padding-bottom: 0rem !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
                max-width: 100% !important;
            }
            
            /* Hide Streamlit branding for clean demo */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* ===== MEET-STYLE DARK THEME ===== */
            /* WHY: Dark backgrounds are video call standard (reduces eye strain, focuses on video) */
            .stApp {
                background-color: #202124 !important;
            }
            
            /* ===== TOP STATUS BAR ===== */
            /* WHY: Quick glance at system status without cluttering video */
            .status-bar {
                background: rgba(32, 33, 36, 0.95);
                border-radius: 8px;
                padding: 0.75rem 1.5rem;
                margin-bottom: 1rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .status-item {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                color: #e8eaed;
                font-size: 0.9rem;
                font-weight: 500;
            }
            
            .status-icon {
                font-size: 1.1rem;
            }
            
            .status-value {
                color: #8ab4f8;
                font-weight: 600;
            }
            
            /* Accessibility Mode indicator */
            .accessibility-badge {
                background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
                color: white;
                padding: 0.4rem 1rem;
                border-radius: 20px;
                font-weight: 600;
                font-size: 0.85rem;
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
            }
            
            /* ===== VIDEO CONTAINER ===== */
            /* WHY: Large central video is the primary focus (Meet/Zoom pattern) */
            .video-container {
                position: relative;
                width: 100%;
                background: #000000;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
                aspect-ratio: 16 / 9;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .video-container img {
                width: 100%;
                height: 100%;
                object-fit: contain;
            }
            
            /* Video error overlay */
            .video-error {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                color: #e8eaed;
                z-index: 10;
            }
            
            .video-error-icon {
                font-size: 4rem;
                margin-bottom: 1rem;
                opacity: 0.5;
            }
            
            .video-error-text {
                font-size: 1.1rem;
                font-weight: 500;
                margin-bottom: 0.5rem;
            }
            
            .video-error-detail {
                font-size: 0.9rem;
                color: #9aa0a6;
            }
            
            /* ===== LIVE CAPTIONS OVERLAY ===== */
            /* WHY: Captions overlaid on video = standard live captioning UX (YouTube, Meet) */
            .captions-overlay {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                background: linear-gradient(to top, rgba(0, 0, 0, 0.9) 0%, rgba(0, 0, 0, 0.7) 70%, transparent 100%);
                padding: 2rem 2rem 1.5rem 2rem;
                z-index: 5;
            }
            
            .caption-text {
                color: #ffffff;
                font-size: 1.5rem;
                font-weight: 600;
                line-height: 1.4;
                text-align: center;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
                min-height: 2.5rem;
                animation: fadeIn 0.3s ease-in;
            }
            
            .caption-confirmed {
                color: #9aa0a6;
                font-size: 1rem;
                text-align: center;
                margin-top: 0.5rem;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
            }
            
            /* Accessibility Mode active - highlight captions */
            .captions-overlay.accessibility-active {
                background: linear-gradient(to top, rgba(139, 92, 246, 0.3) 0%, rgba(99, 102, 241, 0.2) 70%, transparent 100%);
                border-top: 2px solid rgba(139, 92, 246, 0.5);
            }
            
            @keyframes fadeIn {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            /* ===== BOTTOM CONTROL BAR ===== */
            /* WHY: Meet/Zoom pattern - controls at bottom, icon-based, minimal text */
            .control-bar {
                background: rgba(32, 33, 36, 0.95);
                border-radius: 12px;
                padding: 1rem 2rem;
                margin-top: 1rem;
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 1rem;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .control-button {
                background: rgba(60, 64, 67, 0.8);
                border: none;
                border-radius: 50%;
                width: 56px;
                height: 56px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.2s ease;
                color: #e8eaed;
                font-size: 1.5rem;
            }
            
            .control-button:hover {
                background: rgba(80, 84, 87, 0.9);
                transform: scale(1.05);
            }
            
            .control-button:active {
                transform: scale(0.95);
            }
            
            /* Active state for toggle buttons */
            .control-button.active {
                background: #8ab4f8;
                color: #202124;
            }
            
            /* Danger button (end call, clear) */
            .control-button.danger {
                background: #ea4335;
                color: white;
            }
            
            .control-button.danger:hover {
                background: #d33426;
            }
            
            /* Accessibility Mode button - special styling */
            .control-button.accessibility {
                background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
                color: white;
            }
            
            .control-button.accessibility:hover {
                background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
            }
            
            .control-button.accessibility.active {
                box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.4);
            }
            
            /* Button label */
            .control-label {
                color: #9aa0a6;
                font-size: 0.75rem;
                text-align: center;
                margin-top: 0.25rem;
                font-weight: 500;
            }
            
            /* ===== SETTINGS EXPANDER ===== */
            /* WHY: Hide advanced controls to keep main UI clean (Meet pattern) */
            .streamlit-expanderHeader {
                background: rgba(60, 64, 67, 0.5) !important;
                border-radius: 8px !important;
                color: #e8eaed !important;
                font-weight: 500 !important;
            }
            
            .streamlit-expanderContent {
                background: rgba(32, 33, 36, 0.8) !important;
                border-radius: 0 0 8px 8px !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-top: none !important;
            }
            
            /* ===== STREAMLIT WIDGET OVERRIDES ===== */
            /* WHY: Make Streamlit widgets fit dark Meet theme */
            .stButton > button {
                background: rgba(60, 64, 67, 0.8);
                color: #e8eaed;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 0.5rem 1rem;
                font-weight: 500;
                transition: all 0.2s ease;
            }
            
            .stButton > button:hover {
                background: rgba(80, 84, 87, 0.9);
                border-color: rgba(255, 255, 255, 0.2);
            }
            
            /* Slider styling */
            .stSlider > div > div > div {
                background: rgba(60, 64, 67, 0.8);
            }
            
            /* Text color for dark theme */
            .stMarkdown, .stText, p, span, div {
                color: #e8eaed !important;
            }
            
            /* ===== ACCESSIBILITY ENHANCEMENTS ===== */
            /* WHY: High contrast, clear focus states for keyboard navigation */
            *:focus {
                outline: 2px solid #8ab4f8 !important;
                outline-offset: 2px !important;
            }
            
            /* Screen reader only text */
            .sr-only {
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border-width: 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_status_bar(
    fps: float,
    hand_detected: bool,
    accessibility_mode: bool,
    system_status: str,
) -> None:
    """
    Render top status bar with key metrics.
    
    WHY: Quick glance at system state without cluttering video.
    Similar to Meet's top bar showing connection quality.
    """
    status_html = '<div class="status-bar">'
    status_html += '<div style="display: flex; gap: 2rem;">'
    
    # FPS indicator
    fps_color = "#34a853" if fps >= 15 else "#fbbc04"
    status_html += f'''
        <div class="status-item">
            <span class="status-icon">📊</span>
            <span>FPS: <span class="status-value" style="color: {fps_color};">{fps:.1f}</span></span>
        </div>
    '''
    
    # Hand detection status
    hand_icon = "✋" if hand_detected else "👋"
    hand_text = "Hand Detected" if hand_detected else "No Hand"
    hand_color = "#34a853" if hand_detected else "#9aa0a6"
    status_html += f'''
        <div class="status-item">
            <span class="status-icon">{hand_icon}</span>
            <span style="color: {hand_color};">{hand_text}</span>
        </div>
    '''
    
    # System status
    status_html += f'''
        <div class="status-item">
            <span class="status-icon">⚡</span>
            <span>{system_status}</span>
        </div>
    '''
    
    status_html += '</div>'
    
    # Accessibility Mode badge (right side)
    if accessibility_mode:
        status_html += '''
            <div class="accessibility-badge">
                <span>🧏</span>
                <span>Accessibility Mode Active</span>
            </div>
        '''
    
    status_html += '</div>'
    
    st.markdown(status_html, unsafe_allow_html=True)


def render_video_with_captions(
    frame: Optional[np.ndarray],
    live_caption: str,
    confirmed_caption: str,
    accessibility_mode: bool,
    camera_error: Optional[str] = None,
) -> None:
    """
    Render large central video with overlaid captions.
    
    WHY: This is the core video call experience.
    - Large video = primary focus (Meet/Zoom pattern)
    - Overlaid captions = live captioning UX (YouTube, Meet)
    - Error overlay = graceful degradation
    """
    # Start video container
    st.markdown('<div class="video-container">', unsafe_allow_html=True)
    
    # Show video or error
    if camera_error:
        # Camera error overlay
        st.markdown(
            f'''
            <div class="video-error">
                <div class="video-error-icon">📷</div>
                <div class="video-error-text">Camera Unavailable</div>
                <div class="video-error-detail">{camera_error}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
    elif frame is not None:
        # Display video frame
        st.image(frame, channels="RGB", use_container_width=True)
    else:
        # Waiting for camera
        st.markdown(
            '''
            <div class="video-error">
                <div class="video-error-icon">⏳</div>
                <div class="video-error-text">Initializing Camera...</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
    
    # Overlay captions on video
    accessibility_class = "accessibility-active" if accessibility_mode else ""
    caption_display = live_caption if live_caption else "Waiting for gesture..."
    
    st.markdown(
        f'''
        <div class="captions-overlay {accessibility_class}">
            <div class="caption-text">{caption_display}</div>
            {f'<div class="caption-confirmed">{confirmed_caption}</div>' if confirmed_caption else ''}
        </div>
        ''',
        unsafe_allow_html=True,
    )
    
    # End video container
    st.markdown('</div>', unsafe_allow_html=True)


def render_control_bar(
    is_running: bool,
    is_paused: bool,
    accessibility_mode: bool,
    has_text: bool,
) -> Dict[str, bool]:
    """
    Render bottom control bar with icon buttons.
    
    WHY: Meet/Zoom pattern - icon-based controls at bottom.
    Familiar muscle memory for users.
    
    RETURNS: Dict of button states (which buttons were clicked)
    """
    # Use columns for control layout
    cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1])
    
    results = {}
    
    with cols[0]:
        # Microphone (placeholder - not implemented yet)
        st.markdown(
            '''
            <div style="text-align: center;">
                <div class="control-button" title="Microphone (Coming Soon)">
                    🎤
                </div>
                <div class="control-label">Mic</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
    
    with cols[1]:
        # Camera toggle
        camera_icon = "📹" if is_running else "📷"
        camera_class = "active" if is_running else ""
        if st.button(camera_icon, key="camera_toggle", help="Start/Stop Camera"):
            results["camera_toggle"] = True
        st.markdown(f'<div class="control-label">Camera</div>', unsafe_allow_html=True)
    
    with cols[2]:
        # Accessibility Mode toggle
        accessibility_icon = "🧏" if accessibility_mode else "👤"
        if st.button(accessibility_icon, key="accessibility_toggle", help="Toggle Accessibility Mode"):
            results["accessibility_toggle"] = True
        st.markdown(f'<div class="control-label">Accessibility</div>', unsafe_allow_html=True)
    
    with cols[3]:
        # Pause/Resume
        pause_icon = "▶️" if is_paused else "⏸️"
        if st.button(pause_icon, key="pause_toggle", help="Pause/Resume Recognition", disabled=not is_running):
            results["pause_toggle"] = True
        st.markdown(f'<div class="control-label">{"Resume" if is_paused else "Pause"}</div>', unsafe_allow_html=True)
    
    with cols[4]:
        # Clear captions
        if st.button("🗑️", key="clear", help="Clear Captions", disabled=not has_text):
            results["clear"] = True
        st.markdown(f'<div class="control-label">Clear</div>', unsafe_allow_html=True)
    
    with cols[5]:
        # Speak
        if st.button("🔊", key="speak", help="Speak Captions", disabled=not has_text):
            results["speak"] = True
        st.markdown(f'<div class="control-label">Speak</div>', unsafe_allow_html=True)
    
    with cols[6]:
        # Settings (placeholder)
        st.markdown(
            '''
            <div style="text-align: center;">
                <div class="control-button" title="Settings">
                    ⚙️
                </div>
                <div class="control-label">Settings</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
    
    with cols[7]:
        # More options (placeholder)
        st.markdown(
            '''
            <div style="text-align: center;">
                <div class="control-button" title="More Options">
                    ⋮
                </div>
                <div class="control-label">More</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
    
    return results


def trigger_browser_speech(text: str, request_id: int) -> None:
    """
    Trigger browser TTS using Web Speech API.
    
    WHY: Local TTS, no dependencies, works in all modern browsers.
    """
    if not text.strip():
        return

    payload = json.dumps(text)
    components.html(
        f"""
        <script>
            const reqId = {request_id};
            const text = {payload};
            if (window.__lastSpeechId !== reqId) {{
                window.__lastSpeechId = reqId;
                if (window.speechSynthesis) {{
                    window.speechSynthesis.cancel();
                    const utterance = new SpeechSynthesisUtterance(text);
                    utterance.rate = 1.0;
                    utterance.pitch = 1.0;
                    utterance.volume = 1.0;
                    window.speechSynthesis.speak(utterance);
                }}
            }}
        </script>
        """,
        height=0,
    )


def render_advanced_settings() -> None:
    """
    Render advanced settings in collapsible expander.
    
    WHY: Keep main UI clean, hide technical controls.
    Meet pattern - settings hidden in menu.
    """
    with st.expander("⚙️ Advanced Settings", expanded=False):
        st.markdown("### Gesture Recognition")
        
        col1, col2 = st.columns(2)
        
        with col1:
            smoothing = st.slider(
                "Smoothing Window",
                min_value=1,
                max_value=10,
                value=st.session_state.get('smoothing_window', 5),
                help="Higher = smoother but slower response"
            )
            st.session_state.smoothing_window = smoothing
            
            confidence = st.slider(
                "Confidence Threshold",
                min_value=0.3,
                max_value=0.9,
                value=st.session_state.get('confidence_threshold', 0.58),
                step=0.05,
                help="Higher = fewer false positives"
            )
            st.session_state.confidence_threshold = confidence
        
        with col2:
            tts_speed = st.slider(
                "TTS Speed",
                min_value=0.5,
                max_value=2.0,
                value=st.session_state.get('tts_speed', 1.0),
                step=0.1,
                help="Speech synthesis speed"
            )
            st.session_state.tts_speed = tts_speed
            
            hold_frames = st.slider(
                "Gesture Hold Frames",
                min_value=5,
                max_value=15,
                value=st.session_state.get('hold_frames', 8),
                help="Frames to hold before recognition"
            )
            st.session_state.hold_frames = hold_frames
        
        st.markdown("### Display Options")
        
        col3, col4 = st.columns(2)
        
        with col3:
            show_debug = st.checkbox(
                "Show Debug Overlay",
                value=st.session_state.get('show_debug', False),
                help="Display FPS and detection info on video"
            )
            st.session_state.show_debug = show_debug
        
        with col4:
            show_landmarks = st.checkbox(
                "Show Hand Landmarks",
                value=st.session_state.get('show_landmarks', True),
                help="Draw hand skeleton on video"
            )
            st.session_state.show_landmarks = show_landmarks
