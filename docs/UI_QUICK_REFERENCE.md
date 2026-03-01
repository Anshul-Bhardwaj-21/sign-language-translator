# UI Quick Reference Card

## 🎯 At a Glance

### Mode Headers

| Mode | Header | Color |
|------|--------|-------|
| Accessibility | 🧏 Accessibility Mode — Live Captioning Active | Purple Gradient |
| Normal | 📹 Normal Video Call | Blue Gradient |

### Status Badges

| Badge | Meaning | Color |
|-------|---------|-------|
| 🟢 Camera Active | Camera is running | Green |
| 🟡 Hand Detected | Hand visible in frame | Yellow |
| 🔵 Stable Gesture | Hand stable, ready for recognition | Blue |
| ⚠ Poor Lighting | Lighting conditions suboptimal | Orange |
| ❌ No Hand | No hand detected | Gray |
| 📊 XX.X FPS | Current frame rate | Green (≥15) / Orange (<15) |
| 🎯 XX% Conf | Model confidence | Green (≥70%) / Orange (<70%) |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **ALT + A** | Toggle Accessibility Mode |
| **ALT + P** | Pause/Resume Recognition |
| **ALT + C** | Confirm Current Caption |
| **ALT + U** | Undo Last Word |
| **ALT + S** | Speak Current Caption |
| **ALT + X** | Clear All Captions |

### Gesture Controls

| Gesture | Action |
|---------|--------|
| **Open Palm** | Pause/Resume |
| **Fist** | Confirm Sentence |
| **Two Fingers (Peace)** | Undo Last Word |

### Control Buttons

| Button | Function |
|--------|----------|
| **Start** | Initialize camera and hand tracking |
| **Stop** | Stop camera and recognition |
| **Pause** | Pause recognition (keep camera on) |
| **Resume** | Resume recognition |
| **Clear** | Clear all captions |
| **Speak** | Read captions aloud (TTS) |
| **Retry Camera** | Reinitialize camera |

### Configuration Options

| Setting | Range | Default | Purpose |
|---------|-------|---------|---------|
| Smoothing Window | 1-10 frames | 5 | Gesture smoothing |
| Confidence Threshold | 0.3-0.9 | 0.58 | Minimum confidence |
| TTS Voice Speed | 0.5-2.0x | 1.0x | Speech rate |
| Gesture Hold Frames | 5-15 | 8 | Hold time before recognition |

### Sync Status Indicators

| Status | Icon | Meaning |
|--------|------|---------|
| Idle | - | No pending sync |
| Sending | ⏳ | Sending to backend |
| Delivered | ✔ | Successfully synced |
| Failed | ❌ | Sync failed, retry |

### System Metrics

| Metric | Target | Meaning |
|--------|--------|---------|
| FPS | ≥15 | Frames per second |
| Latency | <50ms | Processing delay |
| Model Confidence | ≥70% | Prediction confidence |
| Detection Rate | ≥80% | Hand detection success |
| Gestures Recognized | - | Total gestures detected |
| Uptime | - | Session duration |

## 🎬 Demo Checklist

### Pre-Demo Setup
- [ ] Camera connected and working
- [ ] Good lighting (not backlit)
- [ ] Browser window maximized
- [ ] Backend server running (if multi-user)
- [ ] Practiced signs ready

### Demo Flow
1. [ ] Launch app: `streamlit run app/main.py`
2. [ ] Show Accessibility Mode header
3. [ ] Point out status badges
4. [ ] Click Start button
5. [ ] Show hand detection
6. [ ] Demonstrate sign recognition
7. [ ] Show gesture controls
8. [ ] Open configuration panel
9. [ ] Switch to Normal Mode
10. [ ] Show Caption Only View
11. [ ] Demonstrate keyboard shortcuts
12. [ ] Show system metrics

### Key Talking Points
- [ ] "High contrast, 24-32px font for accessibility"
- [ ] "Real-time status badges show system working"
- [ ] "Gesture controls - no hardware needed"
- [ ] "60+ documented edge cases"
- [ ] "Production-grade error handling"
- [ ] "Complete ML training pipeline"
- [ ] "WebSocket backend for multi-user sync"

## 🐛 Troubleshooting

### Camera Issues
| Problem | Solution |
|---------|----------|
| Camera won't start | Check Windows Settings → Privacy → Camera |
| Black screen | Close other apps using camera |
| Frozen frame | Click "Retry Camera" |
| Poor quality | Adjust lighting, clean lens |

### Hand Detection Issues
| Problem | Solution |
|---------|----------|
| Hand not detected | Ensure good lighting, show full hand |
| Flickering detection | Reduce motion, hold hand steady |
| Wrong hand detected | Show only one hand in frame |
| Poor lighting warning | Add light source, avoid backlighting |

### Recognition Issues
| Problem | Solution |
|---------|----------|
| Gestures not recognized | Hold stable for 0.3s, check confidence |
| Wrong words | Adjust confidence threshold in settings |
| Delayed recognition | Check FPS, close other apps |
| No words appearing | Check if paused, verify model loaded |

### Performance Issues
| Problem | Solution |
|---------|----------|
| Low FPS (<15) | Close other apps, reduce resolution |
| High latency (>50ms) | Check CPU usage, restart app |
| Laggy UI | Reduce smoothing window, disable debug |
| Memory usage high | Restart app, check for leaks |

## 📱 Mobile/Tablet Notes

### Layout Differences
- Single column layout (stacked)
- Touch-optimized buttons (larger)
- Simplified status badges (wrapped)
- Collapsible sections default closed

### Performance Tips
- Use rear camera for better quality
- Ensure stable device position
- Close background apps
- Use landscape orientation

## 🎨 UI Customization

### Color Themes
- Accessibility Mode: Purple gradient
- Normal Mode: Blue gradient
- Success: Green
- Warning: Orange
- Error: Red

### Font Sizes
- Mode Header: 40px
- Live Caption: 32px
- Confirmed Text: 19px
- UI Text: 16px

### Spacing
- Section gap: 1.5rem
- Column gap: 2rem (large)
- Button padding: 0.75rem
- Panel padding: 1rem

## 🔗 Quick Links

- **Full UI Guide**: [docs/UI_GUIDE.md](UI_GUIDE.md)
- **Edge Cases**: [docs/EDGE_CASES.md](EDGE_CASES.md)
- **Firebase Setup**: [docs/FIREBASE_SETUP.md](FIREBASE_SETUP.md)
- **Main README**: [README.md](../README.md)

---

**Print this card for quick reference during demos!**
