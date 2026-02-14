"""Streamlit UI components for the accessibility-focused translator interface."""

from __future__ import annotations

import json
from typing import Dict, List

import numpy as np
import streamlit as st
import streamlit.components.v1 as components


def configure_page() -> None:
    st.set_page_config(
        page_title="Sign Language Accessibility Translator",
        page_icon="SL",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_accessibility_styles()


def apply_accessibility_styles() -> None:
    """High-contrast, larger text, and low-clutter styling."""
    st.markdown(
        """
        <style>
            :root {
                --bg-soft: #f3f7ff;
                --bg-card: #ffffff;
                --ink-strong: #0f172a;
                --ink-soft: #334155;
                --accent: #0f766e;
                --accent-muted: #ccfbf1;
                --warn: #a16207;
                --danger: #b91c1c;
            }
            .stApp {
                background: radial-gradient(circle at 12% 8%, #eaf3ff 0%, #f6fbff 45%, #ffffff 100%);
            }
            .app-title {
                font-size: 2.1rem;
                font-weight: 800;
                color: var(--ink-strong);
                margin-bottom: 0.2rem;
                letter-spacing: 0.2px;
            }
            .app-subtitle {
                font-size: 1.05rem;
                color: var(--ink-soft);
                margin-bottom: 1.1rem;
            }
            .status-chip {
                font-size: 1.1rem;
                font-weight: 700;
                border-radius: 12px;
                padding: 0.65rem 0.95rem;
                display: inline-block;
                border: 1px solid transparent;
                margin-bottom: 0.9rem;
            }
            .status-running { background: #dcfce7; color: #166534; border-color: #86efac; }
            .status-paused { background: #fef3c7; color: #92400e; border-color: #fcd34d; }
            .status-nohand { background: #fee2e2; color: #991b1b; border-color: #fca5a5; }
            .status-camera { background: #fee2e2; color: #7f1d1d; border-color: #f87171; }
            .status-stopped { background: #e5e7eb; color: #374151; border-color: #cbd5e1; }
            .caption-panel {
                background: var(--bg-card);
                border: 2px solid #dbe7ff;
                border-radius: 14px;
                padding: 0.9rem;
            }
            .caption-title {
                font-size: 1.22rem;
                font-weight: 700;
                color: var(--ink-strong);
            }
            .caption-live {
                min-height: 120px;
                font-size: 1.65rem;
                line-height: 1.48;
                color: #0b2545;
                background: var(--bg-soft);
                border: 1px solid #c7ddff;
                border-radius: 10px;
                padding: 1rem;
                margin-top: 0.6rem;
                margin-bottom: 0.7rem;
            }
            .caption-confirmed {
                font-size: 1.05rem;
                color: #1f2937;
                background: #f8fafc;
                border: 1px dashed #cbd5e1;
                border-radius: 10px;
                padding: 0.75rem;
                min-height: 62px;
            }
            .stButton > button {
                font-size: 1.03rem;
                font-weight: 700;
                padding: 0.75rem 0.4rem;
                border-radius: 11px;
                border: 1px solid #95b8f6;
                min-height: 48px;
            }
            .stButton > button:focus {
                outline: 3px solid #93c5fd;
                outline-offset: 1px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown('<div class="app-title">Real-Time Sign Language Accessibility Translator</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Camera-based hand gesture capture to live captions and local spoken feedback.</div>',
        unsafe_allow_html=True,
    )


def render_status_indicator(status: str, detail: str) -> None:
    css_class = {
        "Running": "status-running",
        "Paused": "status-paused",
        "No Hand": "status-nohand",
        "Camera Error": "status-camera",
        "Stopped": "status-stopped",
    }.get(status, "status-stopped")

    st.markdown(
        f'<div class="status-chip {css_class}">Status: {status}</div>',
        unsafe_allow_html=True,
    )
    if detail:
        st.caption(detail)


def render_caption_panel(live_caption: str, confirmed_caption: str) -> None:
    safe_live = live_caption if live_caption else "Waiting for a stable gesture..."
    safe_confirmed = confirmed_caption if confirmed_caption else "No confirmed sentence yet."

    st.markdown('<div class="caption-panel">', unsafe_allow_html=True)
    st.markdown('<div class="caption-title">Live Caption</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="caption-live">{safe_live}</div>', unsafe_allow_html=True)
    st.markdown('<div class="caption-title" style="font-size:1rem; margin-top:0.5rem;">Confirmed Transcript</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="caption-confirmed">{safe_confirmed}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_controls(is_running: bool, is_paused: bool, has_text: bool) -> Dict[str, bool]:
    st.markdown("### Controls")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        start_stop = st.button("Start" if not is_running else "Stop", use_container_width=True)
    with col2:
        pause_resume = st.button(
            "Pause" if not is_paused else "Resume",
            use_container_width=True,
            disabled=not is_running,
        )
    with col3:
        clear = st.button("Clear", use_container_width=True, disabled=not has_text)
    with col4:
        speak = st.button("Speak", use_container_width=True, disabled=not has_text)
    with col5:
        retry = st.button("Retry Camera", use_container_width=True)

    return {
        "start_stop": start_stop,
        "pause_resume": pause_resume,
        "clear": clear,
        "speak": speak,
        "retry": retry,
    }


def render_camera_panel(frame_rgb: np.ndarray) -> None:
    st.markdown("### Camera Preview")
    if frame_rgb is None:
        st.info("No camera frame available yet.")
        return

    st.image(frame_rgb, channels="RGB", use_container_width=True)


def render_event_note(note: str) -> None:
    if note:
        st.info(note)


def trigger_browser_speech(text: str, request_id: int) -> None:
    """Uses browser Web Speech API to keep TTS local and dependency-free."""
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


def join_confirmed_sentences(sentences: List[str]) -> str:
    return " ".join(sentence for sentence in sentences if sentence.strip())
