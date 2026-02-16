# 🚀 Meet-Style UI Quick Start

## Run the New UI

```bash
streamlit run app/main_meet_style.py
```

The app will open at `http://localhost:8501`

---

## What You'll See

### 1. Top Status Bar
- 📊 FPS indicator
- ✋ Hand detection status
- ⚡ System status
- 🧏 Accessibility Mode badge (when active)

### 2. Large Central Video
- 16:9 aspect ratio
- Black background
- Your camera feed

### 3. Overlaid Captions (at bottom of video)
- Large white text (1.5rem)
- Live caption: "Waiting for gesture..."
- Confirmed caption below (when available)
- Purple highlight when Accessibility Mode active

### 4. Bottom Control Bar
- 🎤 Mic (placeholder)
- 📹 Camera (start/stop)
- 🧏 Accessibility Mode (toggle)
- ⏸️ Pause (pause/resume recognition)
- 🗑️ Clear (clear captions)
- 🔊 Speak (text-to-speech)
- ⚙️ Settings (placeholder)
- ⋮ More (placeholder)

---

## Quick Demo (30 Seconds)

1. **Click camera button (📹)**
   - Video starts
   - Status bar shows "Running"

2. **Show your hand**
   - Status bar shows "✋ Hand Detected"
   - Hand landmarks appear on video

3. **Make a sign and hold stable**
   - Caption appears: "HELLO" (or similar)
   - Caption overlaid at bottom of video

4. **Make fist gesture**
   - Caption confirmed
   - Moves to "confirmed" section

5. **Click accessibility button (🧏)**
   - Purple badge appears in status bar
   - Caption area gets purple highlight

6. **Click speak button (🔊)**
   - Browser TTS reads captions aloud

---

## Troubleshooting

### Camera doesn't start
- Check Windows Settings → Privacy → Camera
- Close other apps using camera
- Click camera button again

### No hand detected
- Ensure good lighting
- Show full hand in frame
- Keep hand 1-2 feet from camera

### Captions not appearing
- Hold gesture stable for ~0.3 seconds
- Check if paused (⏸️ button)
- Verify Accessibility Mode is on (🧏)

### Video looks small
- Maximize browser window
- Video auto-scales to fit

---

## Advanced Settings

Click the expander at bottom: **▼ ⚙️ Advanced Settings**

### Gesture Recognition
- **Smoothing Window**: 1-10 (higher = smoother)
- **Confidence Threshold**: 0.3-0.9 (higher = fewer false positives)
- **TTS Speed**: 0.5-2.0x
- **Gesture Hold Frames**: 5-15 (frames to hold before recognition)

### Display Options
- **Show Debug Overlay**: Display FPS and detection info
- **Show Hand Landmarks**: Draw hand skeleton on video

---

## Keyboard Shortcuts (Coming Soon)

- ALT + A: Toggle Accessibility Mode
- ALT + P: Pause/Resume
- ALT + C: Confirm Caption
- ALT + U: Undo
- ALT + S: Speak
- ALT + X: Clear

---

## Comparison with Original UI

### Original UI
```bash
streamlit run app/main.py
```
- Technical dashboard layout
- Multiple columns
- Exposed controls
- Smaller video

### Meet-Style UI (New)
```bash
streamlit run app/main_meet_style.py
```
- Video call layout
- Large central video
- Overlaid captions
- Bottom control bar
- Dark theme

**Both UIs work!** Use Meet-style for demos.

---

## Tips for Best Demo

1. **Good Lighting**: Face a window or light source
2. **Clean Background**: Minimize distractions
3. **Stable Position**: Keep camera steady
4. **Practice Signs**: Know your gestures
5. **Maximize Window**: Full-screen for best effect
6. **Start with Accessibility Mode ON**: Shows purple highlight

---

## What Makes This "Meet-Style"

### Visual Patterns from Google Meet/Zoom
✅ Large central video (primary focus)  
✅ Dark theme (video call standard)  
✅ Bottom control bar (familiar muscle memory)  
✅ Icon-based buttons (minimal text)  
✅ Overlaid captions (live captioning UX)  
✅ Top status bar (connection quality pattern)  
✅ Rounded corners (modern design)  
✅ Hover effects (interactive feedback)  

### Why This Matters for Judges
- **5-second understanding**: "This is a video call product"
- **Familiar pattern**: "I know how to use this"
- **Professional appearance**: "This looks polished"
- **Accessibility clear**: "I see the purple badge"

---

## Technical Notes

### Camera Stability
- Camera stored in `st.session_state`
- Persists across Streamlit reruns
- Proper open/close lifecycle
- Graceful error handling
- Never crashes

### State Management
- All state in `st.session_state`
- Preserved across reruns
- Proper cleanup on stop

### Performance
- 30 FPS target
- <50ms frame processing
- Smooth animations
- No lag

---

## Next Steps

1. Run the app: `streamlit run app/main_meet_style.py`
2. Click camera button
3. Show hand and make signs
4. Toggle Accessibility Mode
5. Practice demo flow
6. Adjust settings as needed

---

## Support

- **Documentation**: See `MEET_STYLE_UI_COMPLETE.md`
- **Original UI**: `app/main.py` still works
- **Issues**: Check camera permissions, lighting, hand position

---

**Ready to demo!** 🎥🧏✨
