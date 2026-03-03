# ControlBar Component

## Overview

The ControlBar component provides meeting controls for participants, including audio/video toggles, screen sharing, reactions, hand raise, and leave meeting functionality.

## Requirements Implemented

- **Requirement 2.1**: Allow participants to share their screen
- **Requirement 7.1**: Allow participants to raise their hand with a single click
- **Requirement 7.6**: Provide at least 5 emoji reactions (👍, 👏, ❤️, 🤔, 😂)
- **Requirement 15.1**: Allow host to mute individual participants (via media state management)

## Features

### Audio/Video Controls
- Toggle microphone on/off with visual feedback
- Toggle camera on/off with visual feedback
- Active state indication (red when muted/disabled)
- Tooltips for better UX

### Screen Sharing
- Start/stop screen sharing
- Visual indicator when sharing is active
- Integration with WebRTC screen capture API (implementation in Task 4.7)

### Reactions
- Emoji picker popup with 5 reactions
- Click outside to close picker
- Reactions are broadcast to all participants
- Reactions display near participant video for 3 seconds (handled by server)

### Hand Raise
- Toggle hand raise status
- Visual feedback (yellow when raised)
- Chronological order maintained by server
- Host can lower hands via participant management

### Leave Meeting
- Prominent red button to leave meeting
- Sends leave event to server
- Navigates back to home page

## Props

```typescript
interface ControlBarProps {
  meetingId: string;           // Current meeting ID
  userId: string;              // Current user ID
  audioEnabled: boolean;       // Current audio state
  videoEnabled: boolean;       // Current video state
  screenSharing: boolean;      // Current screen sharing state
  handRaised: boolean;         // Current hand raise state
  onToggleAudio: (enabled: boolean) => void;      // Audio toggle handler
  onToggleVideo: (enabled: boolean) => void;      // Video toggle handler
  onToggleScreenShare: () => void;                // Screen share toggle handler
  onToggleHandRaise: () => void;                  // Hand raise toggle handler
  onLeaveMeeting: () => void;                     // Leave meeting handler
}
```

## Usage

```tsx
import ControlBar from '../components/ControlBar';

function MeetingRoom() {
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [videoEnabled, setVideoEnabled] = useState(true);
  const [screenSharing, setScreenSharing] = useState(false);
  const [handRaised, setHandRaised] = useState(false);

  return (
    <ControlBar
      meetingId={meetingId}
      userId={userId}
      audioEnabled={audioEnabled}
      videoEnabled={videoEnabled}
      screenSharing={screenSharing}
      handRaised={handRaised}
      onToggleAudio={setAudioEnabled}
      onToggleVideo={setVideoEnabled}
      onToggleScreenShare={() => setScreenSharing(!screenSharing)}
      onToggleHandRaise={() => setHandRaised(!handRaised)}
      onLeaveMeeting={handleLeaveMeeting}
    />
  );
}
```

## WebSocket Events

The component sends the following events to the signaling server:

### toggle-audio
```typescript
{
  meetingId: string;
  userId: string;
  enabled: boolean;
}
```

### toggle-video
```typescript
{
  meetingId: string;
  userId: string;
  enabled: boolean;
}
```

### start-screen-share / stop-screen-share
```typescript
{
  meetingId: string;
  userId: string;
}
```

### raise-hand
```typescript
{
  meetingId: string;
  userId: string;
  raised: boolean;
}
```

### send-reaction
```typescript
{
  meetingId: string;
  userId: string;
  reaction: string; // Emoji character
}
```

## Styling

The component uses Tailwind CSS with the following design system:

- **Background**: `bg-navy-800` (default), `bg-navy-700` (hover)
- **Active states**: `bg-blue-600` (screen sharing, reactions open)
- **Disabled states**: `bg-red-600` (audio/video off)
- **Hand raised**: `bg-yellow-600`
- **Leave button**: `bg-red-600`
- **Tooltips**: Dark background with white text, appear on hover

## Accessibility

- All buttons have descriptive `title` attributes
- Tooltips provide additional context on hover
- Visual feedback for all state changes
- Keyboard navigation support (native button elements)
- Screen reader friendly with semantic HTML

## Integration with MeetingRoom

The ControlBar is integrated into the MeetingRoom component at the bottom of the screen:

1. MeetingRoom maintains local state for audio, video, screen sharing, and hand raise
2. State changes are passed to ControlBar via props
3. ControlBar callbacks update local state and send WebSocket events
4. WebRTC hook methods (toggleAudio, toggleVideo) are called to control media tracks

## Future Enhancements (Phase 2)

- Settings menu for audio/video device selection
- Background effects toggle (blur, replacement)
- Noise cancellation toggle
- Recording controls for hosts
- Breakout room controls
- Whiteboard toggle
- Chat panel toggle

## Testing

To test the ControlBar component:

1. Join a meeting
2. Click audio button - verify microphone mutes/unmutes
3. Click video button - verify camera turns on/off
4. Click screen share - verify screen sharing starts/stops (Task 4.7)
5. Click reactions - verify emoji picker appears
6. Click an emoji - verify reaction is sent and picker closes
7. Click hand raise - verify hand icon appears in participant list
8. Click leave - verify navigation to home page

## Notes

- Screen sharing implementation is a placeholder and will be completed in Task 4.7
- The component assumes WebSocket connection is established
- Media state is managed by the parent component (MeetingRoom)
- WebRTC media track control is handled by the useWebRTC hook
