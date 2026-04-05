# VideoGrid and VideoTile Components

## Overview

The VideoGrid and VideoTile components work together to display participant video streams in a meeting room with multiple layout options and interactive features.

## Components

### VideoTile

Displays an individual participant's video stream with status indicators and controls.

**Features:**
- Video stream display with fallback to avatar when video is disabled
- Participant name overlay
- Audio/video status indicators (muted/unmuted, video on/off)
- Active speaker highlighting with animated border
- Pinned participant indicator
- Hand raised indicator
- Sign language indicator
- Host/Co-host badges
- Pin/unpin button

**Props:**
```typescript
interface VideoTileProps {
  participant: Participant;        // Participant data
  stream: MediaStream | null;      // Video/audio stream
  isActiveSpeaker?: boolean;       // Highlight as active speaker
  isPinned?: boolean;              // Show pinned indicator
  isLocal?: boolean;               // Is this the local user
  className?: string;              // Additional CSS classes
  onPin?: (participantId: string) => void; // Pin callback
}
```

**Requirements Implemented:**
- 1.3: Display video with adaptive quality
- 1.5: Prioritize active speaker with highest quality
- 22.1: Display participant name and status indicators
- 22.2: Highlight active speaker within 300ms

### VideoGrid

Renders multiple VideoTile components in various responsive layouts.

**Features:**
- Grid layout: All participants displayed equally
- Spotlight layout: One large video with thumbnails
- Sidebar layout: Main video with sidebar of participants
- Accessibility layout: Optimized for sign language visibility
- Responsive grid sizing based on participant count
- Automatic sorting (pinned > active speaker > host > others)
- Empty state when no participants

**Props:**
```typescript
interface VideoGridProps {
  participants: Participant[];              // All participants
  localStream: MediaStream | null;          // Local user's stream
  remoteStreams: Map<string, MediaStream>;  // Remote streams by userId
  currentUserId: string;                    // Current user ID
  layout: LayoutType;                       // Layout mode
  activeSpeaker: string | null;             // Active speaker ID
  pinnedParticipant: string | null;         // Pinned participant ID
  onPinParticipant: (id: string | null) => void; // Pin callback
}
```

**Requirements Implemented:**
- 1.3: Adapt video quality based on grid size
- 1.5: Prioritize active speaker with highest quality
- 22.1: Display all participants in grid
- 22.2: Highlight active speaker within 300ms
- 22.3: Enlarge active speaker's video in layout
- 22.4: Provide grid view layout option
- 22.5: Provide spotlight view layout option
- 22.6: Provide sidebar view layout option
- 22.7: Support manual pinning of participant video

## Layout Modes

### Grid Layout (22.4)
All participants displayed in a responsive grid:
- 1 participant: 1 column
- 2 participants: 2 columns
- 3-4 participants: 2 columns
- 5-6 participants: 3 columns
- 7-9 participants: 3 columns
- 10-12 participants: 4 columns
- 13-16 participants: 4 columns
- 17+ participants: 5 columns

### Spotlight Layout (22.5)
One large video (pinned or active speaker) with thumbnails:
- Main video takes up most of the screen
- Up to 8 thumbnails shown at bottom
- "+X more" indicator if more than 8 other participants

### Sidebar Layout (22.6)
Main video on left, sidebar on right:
- Main video (pinned or active speaker) takes 75% width
- Sidebar shows other participants in vertical list
- Sidebar scrollable if many participants

### Accessibility Layout
Optimized for deaf/hard-of-hearing users:
- Extra large main video for sign language visibility
- Centered layout with max-width constraint
- Up to 6 compact thumbnails at bottom
- High contrast indicators

## Active Speaker Detection

The VideoGrid component responds to active speaker changes within 300ms (Requirement 22.2):

1. Active speaker gets blue border with glow effect
2. Active speaker is prioritized in spotlight/sidebar layouts
3. Active speaker is sorted to top in grid layout (after pinned)
4. "Speaking" indicator shown on video tile

## Pinning Behavior

Users can manually pin participants (Requirement 22.7):

1. Click pin button on any video tile
2. Pinned participant gets purple border with glow effect
3. Pinned participant takes priority over active speaker in layouts
4. Only one participant can be pinned at a time
5. Click pin button again to unpin

## Video Quality Adaptation

The grid layout adapts to participant count (Requirement 1.3):

- Fewer participants = larger tiles = higher quality needed
- More participants = smaller tiles = can use lower quality
- Grid columns automatically adjust based on count
- Future: Actual bitrate adjustment based on tile size

## Integration Example

```tsx
import VideoGrid from '../components/VideoGrid';
import { useMeeting } from '../contexts/MeetingContext';
import { useWebRTC } from '../hooks/useWebRTC';

function MeetingRoom() {
  const {
    participants,
    activeLayout,
    activeSpeaker,
    pinnedParticipant,
    setPinnedParticipant,
  } = useMeeting();
  
  const webrtc = useWebRTC(meetingId, currentUserId);
  
  const handlePinParticipant = (participantId: string | null) => {
    setPinnedParticipant(participantId);
  };
  
  return (
    <VideoGrid
      participants={participants}
      localStream={webrtc.localStream}
      remoteStreams={webrtc.remoteStreams}
      currentUserId={currentUserId}
      layout={activeLayout}
      activeSpeaker={activeSpeaker}
      pinnedParticipant={pinnedParticipant}
      onPinParticipant={handlePinParticipant}
    />
  );
}
```

## Styling

Both components use Tailwind CSS for styling:

- Navy color scheme matching the app theme
- Smooth transitions for state changes (300ms)
- Responsive sizing with flexbox and grid
- Gradient overlays for better text readability
- Hover effects for interactive elements

## Future Enhancements

1. **Video Quality Adaptation**: Implement actual bitrate adjustment based on tile size
2. **Reactions**: Display emoji reactions on video tiles
3. **Screen Sharing**: Special handling for screen share streams
4. **Virtual Backgrounds**: Integration with background effects
5. **Picture-in-Picture**: Allow floating video tiles
6. **Drag and Drop**: Manual reordering of participants
7. **Zoom Controls**: Click to enlarge specific participant

## Testing

Key scenarios to test:

1. Single participant (local only)
2. Two participants (local + remote)
3. Multiple participants (3-16)
4. Active speaker changes
5. Pin/unpin functionality
6. Layout switching
7. Video enable/disable
8. Audio mute/unmute
9. Hand raise indicator
10. Empty state (no participants)

## Performance Considerations

- Video elements use `autoPlay` and `playsInline` for mobile compatibility
- Local video is muted to prevent audio feedback
- Streams are attached via refs to avoid re-renders
- Participant sorting is memoized with `useMemo`
- Grid layout calculations are optimized
- Maximum 8 thumbnails shown in spotlight to limit DOM nodes

## Accessibility

- Semantic HTML structure
- ARIA labels on interactive buttons
- Keyboard navigation support (via button elements)
- High contrast indicators
- Dedicated accessibility layout mode
- Screen reader friendly participant names
