"""
VIDEO CALL UI Module
Purpose: Streamlit UI components for video calling interface
"""

import streamlit as st
from typing import Any, Dict, List, Optional


# ============================================
# CALL HEADER & INFO
# ============================================

def render_call_header(call_info: Optional[Dict]) -> None:
    """
    Render call header with name, duration, participant count.
    
    Args:
        call_info: Dictionary with call information
    """
    if call_info is None:
        return
    
    try:
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.markdown(f"### 📞 {call_info.get('call_name', 'Video Call')}")
        
        with col2:
            status = call_info.get('state', 'unknown').upper()
            color = "🟢" if status == "ACTIVE" else "🟡" if status == "WAITING" else "🔴"
            st.write(f"{color} **Status:** {status}")
        
        with col3:
            participants = call_info.get('participant_count', 0)
            st.write(f"👥 **{participants}** participants")
        
        # Duration
        duration = call_info.get('duration_seconds')
        if duration:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            st.caption(f"⏱️ Duration: {minutes}m {seconds}s")
    
    except Exception as e:
        print(f"ERROR: Failed to render call header: {str(e)}")


# ============================================
# PARTICIPANTS LIST
# ============================================

def render_participants_panel(participants: List) -> None:
    """
    Render participant list panel.
    
    Args:
        participants: List of Participant objects
    """
    with st.expander("👥 Participants", expanded=True):
        if not participants:
            st.info("No participants yet")
            return
        
        try:
            for participant in participants:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    status_icon = "🎤" if participant.audio_state.value == "active" else "🔇"
                    video_icon = "📹" if participant.video_state.value == "active" else "❌"
                    st.write(f"{status_icon} {video_icon} {participant.name}")
                
                with col2:
                    if participant.is_screen_sharing:
                        st.caption("📺 Screen")
                
                with col3:
                    role_badge = "👑" if participant.role.value == "host" else "👤"
                    st.caption(role_badge)
                
                with col4:
                    if participant.current_caption:
                        st.caption(f"📝 \"{participant.current_caption[:20]}...\"")
                
                st.divider()
        
        except Exception as e:
            print(f"ERROR: Failed to render participants: {str(e)}")


# ============================================
# VIDEO DISPLAY
# ============================================

def render_video_grid(frames: Dict[str, Any], columns: int = 2) -> None:
    """
    Render video feed grid.
    
    Args:
        frames: Dictionary {participant_id: frame}
        columns: Number of columns in grid
    """
    try:
        if not frames:
            st.info("🎥 No video feeds available")
            return
        
        st.write("### 🎥 Video Feeds")
        
        participant_ids = list(frames.keys())
        cols = st.columns(columns)
        
        for idx, participant_id in enumerate(participant_ids):
            col_idx = idx % columns
            with cols[col_idx]:
                frame = frames[participant_id]
                st.image(frame, use_column_width=True, 
                        caption=f"Participant {idx + 1}")
    
    except Exception as e:
        print(f"ERROR: Failed to render video grid: {str(e)}")


# ============================================
# CAPTIONS DISPLAY
# ============================================

def render_live_captions(participants: List) -> None:
    """
    Render live captions from all participants.
    
    Args:
        participants: List of Participant objects
    """
    with st.expander("📝 Live Captions", expanded=True):
        try:
            caption_cols = {}
            for participant in participants:
                if participant.current_caption:
                    caption_cols[participant.name] = participant.current_caption
            
            if not caption_cols:
                st.info("No captions yet")
                return
            
            for name, caption in caption_cols.items():
                st.markdown(f"**{name}:** {caption}")
        
        except Exception as e:
            print(f"ERROR: Failed to render captions: {str(e)}")


# ============================================
# CALL CONTROLS
# ============================================

def render_call_controls(is_host: bool = False) -> Dict[str, bool]:
    """
    Render call control buttons (mute, video, share, end call).
    
    Args:
        is_host: Whether user is call host
    
    Returns:
        Dictionary with button states
    """
    st.write("### ⚙️ Call Controls")
    
    button_states = {}
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    try:
        with col1:
            button_states["mute_audio"] = st.button(
                "🎤 Mute", use_container_width=True,
                help="Toggle microphone on/off"
            )
        
        with col2:
            button_states["toggle_video"] = st.button(
                "📹 Camera", use_container_width=True,
                help="Toggle camera on/off"
            )
        
        with col3:
            button_states["share_screen"] = st.button(
                "📺 Share", use_container_width=True,
                help="Share screen with participants"
            )
        
        with col4:
            button_states["show_chat"] = st.button(
                "💬 Chat", use_container_width=True,
                help="Open chat panel"
            )
        
        with col5:
            button_states["end_call"] = st.button(
                "🔴 End Call", use_container_width=True,
                help="End and exit call"
            )
        
        return button_states
    
    except Exception as e:
        print(f"ERROR: Failed to render call controls: {str(e)}")
        return {}


# ============================================
# CHAT PANEL
# ============================================

def render_chat_panel(call_manager, message_manager) -> None:
    """
    Render chat message panel.
    
    Args:
        call_manager: CallManager instance
        message_manager: MessageManager instance
    """
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write("### 💬 Chat")
    
    with col2:
        if st.button("🗑️ Clear Chat"):
            message_manager.clear_chat()
            st.rerun()
    
    try:
        # Display messages
        chat_display = message_manager.get_chat_display(limit=50)
        st.text_area(
            "Messages",
            value=chat_display,
            height=200,
            disabled=True,
            label_visibility="collapsed"
        )
        
        # Input area
        col1, col2 = st.columns([3, 1])
        
        with col1:
            message_input = st.text_input(
                "Type message...",
                placeholder="Send a message to other participants",
                label_visibility="collapsed"
            )
        
        with col2:
            if st.button("📤 Send", use_container_width=True):
                if message_input:
                    try:
                        from app.server.messaging import MessageType
                    except ModuleNotFoundError:
                        from server.messaging import MessageType  # type: ignore[no-redef]
                    message_manager.send_message(
                        message_id="msg_" + str(hash(message_input))[:8],
                        sender_id="local_user",
                        sender_name="You",
                        content=message_input,
                        message_type=MessageType.TEXT
                    )
                    st.rerun()
        
        # Quick messages
        st.write("**Quick Messages:**")
        col1, col2, col3 = st.columns(3)
        
        quick_msgs = {
            "Hello": "hello",
            "Thank You": "thank_you",
            "Can You Hear Me?": "can_you_see"
        }
        
        for idx, (label, key) in enumerate(quick_msgs.items()):
            col = [col1, col2, col3][idx % 3]
            with col:
                if st.button(label, use_container_width=True):
                    try:
                        from app.server.messaging import MessageType
                    except ModuleNotFoundError:
                        from server.messaging import MessageType  # type: ignore[no-redef]
                    message_manager.send_message(
                        message_id="quick_" + str(hash(label))[:8],
                        sender_id="local_user",
                        sender_name="You",
                        content=label,
                        message_type=MessageType.TEXT
                    )
                    st.rerun()
    
    except Exception as e:
        print(f"ERROR: Failed to render chat panel: {str(e)}")


# ============================================
# SETUP CALL DIALOG
# ============================================

def render_setup_call_dialog() -> Optional[Dict]:
    """
    Render dialog to setup call.
    
    Returns:
        Dictionary with call setup info or None
    """
    st.write("### 📱 Start a Video Call")
    
    try:
        col1, col2 = st.columns(2)
        
        with col1:
            call_name = st.text_input(
                "Call Name",
                placeholder="Team Meeting",
                max_chars=50
            )
        
        with col2:
            max_participants = st.number_input(
                "Max Participants",
                min_value=2,
                max_value=50,
                value=10
            )
        
        your_name = st.text_input(
            "Your Name",
            placeholder="Enter your name",
            max_chars=50
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_call = st.button("▶️ Start Call", use_container_width=True)
        
        with col2:
            join_call = st.button("👤 Join Call", use_container_width=True)
        
        if start_call and call_name and your_name:
            return {
                "action": "start",
                "call_name": call_name,
                "max_participants": max_participants,
                "your_name": your_name
            }
        
        if join_call and your_name:
            call_id = st.text_input("Enter Call ID", placeholder="Paste call ID here")
            if st.button("✓ Join"):
                return {
                    "action": "join",
                    "call_id": call_id,
                    "your_name": your_name
                }
        
        return None
    
    except Exception as e:
        print(f"ERROR: Failed to render setup dialog: {str(e)}")
        return None


# ============================================
# GESTURE FEEDBACK
# ============================================

def render_gesture_feedback(gesture: str, confidence: float) -> None:
    """
    Render detected gesture feedback.
    
    Args:
        gesture: Detected gesture type
        confidence: Gesture confidence score
    """
    if gesture == "none" or confidence < 0.7:
        return
    
    try:
        gesture_icons = {
            "pause": "⏸️ Pause",
            "confirm": "✅ Confirm",
            "undo": "↶ Undo",
            "select": "☝️ Select"
        }
        
        label = gesture_icons.get(gesture, gesture)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"🎯 **Gesture:** {label}")
        with col2:
            st.caption(f"📊 {confidence:.0%}")
    
    except Exception as e:
        print(f"ERROR: Failed to render gesture feedback: {str(e)}")


# ============================================
# CONNECTION STATS
# ============================================

def render_connection_stats(stats: Optional[Dict]) -> None:
    """
    Render connection quality statistics.
    
    Args:
        stats: Dictionary with connection statistics
    """
    if not stats:
        return
    
    with st.expander("📊 Connection Stats"):
        try:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                fps = stats.get("fps", 0)
                st.metric("FPS", f"{fps:.1f}")
            
            with col2:
                bitrate = stats.get("bitrate", 0)
                st.metric("Bitrate", f"{bitrate} kbps")
            
            with col3:
                latency = stats.get("latency", 0)
                st.metric("Latency", f"{latency}ms")
            
            # Additional stats
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"📦 Packets Sent: {stats.get('packets_sent', 0)}")
            with col2:
                st.write(f"📦 Packets Lost: {stats.get('packets_lost', 0)}")
        
        except Exception as e:
            print(f"ERROR: Failed to render stats: {str(e)}")
