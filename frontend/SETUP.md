# Frontend Setup Documentation

## Overview

This document describes the React + TypeScript frontend setup for the advanced meeting features application.

## Technology Stack

- **React**: 18.2.0
- **TypeScript**: 5.9.3
- **React Router**: 6.21.0 (for navigation)
- **Tailwind CSS**: 3.4.0 (for styling)
- **Socket.IO Client**: 4.6.0 (for real-time communication)
- **Vite**: 5.0.8 (build tool)
- **Vitest**: 4.0.18 (testing framework)

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   ├── contexts/         # React Context providers
│   │   ├── AppContext.tsx           # Global app state
│   │   ├── AuthContext.tsx          # Authentication state
│   │   ├── MeetingContext.tsx       # Meeting-specific state
│   │   ├── ThemeContext.tsx         # Theme management
│   │   └── WebSocketContext.tsx     # Socket.IO connection
│   ├── hooks/            # Custom React hooks
│   ├── pages/            # Page components
│   ├── services/         # API and service integrations
│   ├── styles/           # Global styles
│   ├── types/            # TypeScript type definitions
│   ├── utils/            # Utility functions
│   ├── App.tsx           # Main app component
│   └── main.tsx          # Entry point
├── public/               # Static assets
├── package.json          # Dependencies
├── tsconfig.json         # TypeScript configuration
├── vite.config.ts        # Vite configuration
└── tailwind.config.js    # Tailwind CSS configuration
```

## State Management

The application uses React Context API for global state management with the following contexts:

### 1. AppContext
- Global application state (theme, user, AI status)
- Connection strength monitoring
- Word recognition tracking

### 2. AuthContext
- User authentication state
- Login/logout functionality
- Protected route handling

### 3. MeetingContext (NEW)
- Meeting-specific state management
- Participant management
- Layout control (grid, spotlight, sidebar, accessibility)
- Active speaker/signer detection
- Recording and caption states
- Meeting settings

### 4. WebSocketContext (UPDATED)
- Socket.IO client connection management
- Real-time event handling
- Automatic reconnection
- Event subscription system

### 5. ThemeContext
- Dark/light theme management
- Theme persistence

## Socket.IO Integration

The WebSocketContext has been updated to use Socket.IO client instead of native WebSocket:

### Features:
- Automatic reconnection with exponential backoff
- Event-based messaging (vs. raw message passing)
- Support for both WebSocket and polling transports
- Query parameter support for room and user identification

### Usage Example:

```typescript
import { useWebSocket } from './contexts/WebSocketContext';

function MyComponent() {
  const { isConnected, sendMessage, subscribe, connect } = useWebSocket();

  useEffect(() => {
    // Connect to meeting
    connect(roomCode, userId);

    // Subscribe to events
    const unsubscribe = subscribe('participant-joined', (data) => {
      console.log('New participant:', data);
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const handleSendMessage = () => {
    sendMessage('chat-message', { text: 'Hello!' });
  };

  return <div>Connected: {isConnected ? 'Yes' : 'No'}</div>;
}
```

## Meeting State Management

The MeetingContext provides comprehensive meeting state management:

### Participant Management:
```typescript
const { participants, addParticipant, removeParticipant, updateParticipant } = useMeeting();

// Add participant
addParticipant({
  id: 'p1',
  userId: 'u1',
  name: 'John Doe',
  audioEnabled: true,
  videoEnabled: true,
  isHost: false,
  isCoHost: false,
  handRaised: false,
  isSpeaking: false,
  isSigning: false,
  joinedAt: new Date(),
});

// Update participant
updateParticipant('p1', { audioEnabled: false });

// Remove participant
removeParticipant('p1');
```

### Layout Management:
```typescript
const { activeLayout, setActiveLayout, activeSpeaker, setActiveSpeaker } = useMeeting();

// Change layout
setActiveLayout('spotlight'); // 'grid' | 'spotlight' | 'sidebar' | 'accessibility'

// Set active speaker
setActiveSpeaker('p1');
```

### Feature Controls:
```typescript
const { 
  isRecording, 
  setIsRecording,
  captionsEnabled,
  setCaptionsEnabled,
  signLanguageCaptionsEnabled,
  setSignLanguageCaptionsEnabled 
} = useMeeting();

// Toggle recording
setIsRecording(true);

// Enable captions
setCaptionsEnabled(true);
setSignLanguageCaptionsEnabled(true);
```

## React Router Configuration

The application uses React Router v6 with the following routes:

- `/` - Landing page
- `/login` - Login page
- `/dashboard` - User dashboard (protected)
- `/admin` - Admin dashboard (protected, admin only)
- `/lobby` - Pre-join lobby (protected)
- `/lobby/:roomCode` - Pre-join lobby with room code (protected)
- `/call/:roomCode` - Video call page (protected)

### Protected Routes:
Routes are protected using custom route components:
- `ProtectedRoute` - Requires authentication
- `AdminRoute` - Requires authentication + admin role

## Tailwind CSS Configuration

Tailwind CSS is configured with:
- Dark mode support (class-based)
- Custom color palette
- Responsive breakpoints
- Custom utility classes

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_SOCKET_URL=http://localhost:8001
VITE_API_URL=http://localhost:8000
```

## Development

### Install Dependencies:
```bash
npm install
```

### Run Development Server:
```bash
npm run dev
```

### Build for Production:
```bash
npm run build
```

### Run Tests:
```bash
npm test
```

### Lint Code:
```bash
npm run lint
```

### Format Code:
```bash
npm run format
```

## Requirements Mapping

This setup satisfies the following requirements:

### Requirement 22.4: Grid View Layout
- Implemented via `MeetingContext.activeLayout = 'grid'`
- Supports responsive grid layout for all participants

### Requirement 22.5: Spotlight View Layout
- Implemented via `MeetingContext.activeLayout = 'spotlight'`
- Shows only active speaker prominently

### Requirement 22.6: Sidebar View Layout
- Implemented via `MeetingContext.activeLayout = 'sidebar'`
- Shows active speaker large with others in sidebar

## Next Steps

1. Implement VideoGrid and VideoTile components (Task 4.5)
2. Implement WebRTC video calling (Task 4.3)
3. Implement ControlBar component (Task 4.6)
4. Implement screen sharing (Task 4.7)
5. Implement ChatPanel component (Task 4.8)

## Notes

- The Socket.IO client is configured to use both WebSocket and polling transports for maximum compatibility
- Automatic reconnection is enabled with exponential backoff
- All contexts are properly typed with TypeScript
- The MeetingContext provides a centralized state management solution for all meeting-related features
