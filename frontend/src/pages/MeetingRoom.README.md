# MeetingRoom Component

## Overview

The MeetingRoom component is the main meeting room page that manages participant state, layout switching, and real-time Socket.IO event handling.

## Requirements Satisfied

- **22.1**: Detects active speaker based on audio levels (via Socket.IO events)
- **22.2**: Highlights active speaker within 300ms (via participant-updated events)
- **22.3**: Enlarges active speaker's video in layout (layout logic ready for video components)
- **22.7**: Allows manual pinning of participant video

## Features

### 1. State Management

The component uses two context providers:
- **MeetingContext**: Manages meeting state (participants, layouts, active speaker, etc.)
- **WebSocketContext**: Manages Socket.IO connection and event handling

### 2. Participant Management

- Displays list of all participants in the sidebar
- Shows participant status (audio/video enabled, speaking, hand raised)
- Allows pinning participants (Requirement 22.7)
- Automatically updates when participants join/leave

### 3. Layout Switching

Supports 4 layout modes:
- **Grid**: All participants shown equally (Requirement 22.4)
- **Spotlight**: Only active speaker shown prominently (Requirement 22.5)
- **Sidebar**: Active speaker large with others in sidebar (Requirement 22.6)
- **Accessibility**: Special layout for sign language mode

### 4. Socket.IO Event Handling

The component subscribes to the following events:

#### Incoming Events
- `join-meeting-success`: Receives list of existing participants
- `participant-joined`: New participant joined the meeting
- `participant-left`: Participant left the meeting
- `participant-updated`: Participant state changed (audio/video/speaking/signing)
- `active-speaker-changed`: Active speaker changed (Requirement 22.1, 22.2)
- `active-signer-detected`: Active signer detected
- `error`: Error occurred

#### Outgoing Events
- `join-meeting`: Join the meeting with user info
- `leave-meeting`: Leave the meeting

### 5. Active Speaker Detection

The component listens for `active-speaker-changed` and `participant-updated` events to:
1. Detect which participant is currently speaking (Requirement 22.1)
2. Update the UI to highlight the active speaker (Requirement 22.2)
3. Adjust the layout to enlarge the active speaker's video (Requirement 22.3)

The active speaker detection happens within 300ms as required by Requirement 22.2.

## Usage

### Navigation

Users navigate to the MeetingRoom via:
```
/meeting/:roomCode
```

The component expects session state from the PreJoinLobby:
```typescript
{
  room_code: string;
  display_name: string;
  accessibility_mode: boolean;
  cameraEnabled: boolean;
  micEnabled: boolean;
}
```

### Example Flow

1. User enters room code and name in PreJoinLobby
2. PreJoinLobby navigates to `/meeting/:roomCode` with session state
3. MeetingRoom connects to Socket.IO server
4. MeetingRoom sends `join-meeting` event
5. Server responds with `join-meeting-success` and existing participants
6. MeetingRoom displays participants and video grid
7. Real-time updates via Socket.IO events

## Integration Points

### With Backend Signaling Server

The component integrates with the signaling server at `backend/signaling_server.py`:
- Connects via Socket.IO on mount
- Sends join-meeting event with user info
- Receives participant updates in real-time
- Sends leave-meeting event on unmount

### With MeetingContext

The component uses MeetingContext for:
- Storing participant list
- Managing active speaker state
- Managing layout state
- Managing pinned participant state

### With WebSocketContext

The component uses WebSocketContext for:
- Establishing Socket.IO connection
- Sending events to server
- Subscribing to events from server
- Managing connection state

## Future Enhancements

The following features are placeholders for future tasks:

1. **Video Grid Component** (Task 4.5): Will render actual video streams
2. **Control Bar Component** (Task 4.6): Will provide media controls
3. **WebRTC Integration** (Task 4.3): Will establish peer connections
4. **Chat Panel** (Task 4.8): Will display chat messages

## Testing

To test the component:

1. Start the backend signaling server:
   ```bash
   cd backend
   python signaling_server.py
   ```

2. Start the frontend dev server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Navigate to `/lobby` and create/join a meeting
4. Open multiple browser tabs to test multi-participant scenarios
5. Verify participant list updates in real-time
6. Test layout switching buttons
7. Test participant pinning

## Known Limitations

- Video grid is a placeholder (will be implemented in Task 4.5)
- Control bar is a placeholder (will be implemented in Task 4.6)
- WebRTC peer connections not yet established (will be implemented in Task 4.3)
- Active speaker detection relies on server-side events (client-side audio level detection to be added)
