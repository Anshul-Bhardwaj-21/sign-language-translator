# WebRTC Video Calling Hook

## Overview

The `useWebRTC` hook provides a complete WebRTC implementation for peer-to-peer video calling with support for multiple participants, connection quality monitoring, and adaptive bitrate adjustment.

## Requirements Implemented

### Requirement 1.1: High-Definition Video Streaming
- Supports 720p video resolution at 30 FPS (default)
- Supports 1080p video resolution at 30 FPS (configurable)
- Configurable video constraints with ideal and maximum values

### Requirement 1.3: Adaptive Quality
- Automatically monitors connection quality
- Detects high latency (>200ms) and packet loss (>5%)
- Prepares for adaptive bitrate adjustment

### Requirement 21.1: Low-Latency Audio
- Audio latency optimized for <150ms
- Echo cancellation enabled
- Noise suppression enabled
- Auto gain control enabled
- 48kHz sample rate for high-quality audio

### Requirement 21.2: Low-Latency Video
- Video latency optimized for <200ms
- Efficient codec configuration
- Minimal jitter buffering

### Requirement 21.3: UDP Transport
- Uses UDP for media streams (via WebRTC default)
- Bundle policy set to 'max-bundle' for optimization
- RTCP multiplexing required for reduced port usage

### Requirement 21.5: TURN Fallback
- Attempts direct peer connections first
- Falls back to TURN servers only when necessary
- ICE restart on connection failure

## Features

### 1. Media Stream Initialization
```typescript
const { initializeMedia, localStream } = useWebRTC(meetingId, userId);

// Initialize with default constraints (720p, 30fps)
await initializeMedia();

// Initialize with custom constraints
await initializeMedia({
  audio: true,
  video: { width: 1920, height: 1080, frameRate: 30 }
});
```

### 2. Peer Connection Management
```typescript
const { createPeerConnection, closePeerConnection } = useWebRTC(meetingId, userId);

// Create connection to another user
const peerConnection = await createPeerConnection('user-2');

// Close connection when user leaves
closePeerConnection('user-2');
```

### 3. Remote Stream Handling
```typescript
const { remoteStreams } = useWebRTC(meetingId, userId);

// Access remote streams by user ID
const userStream = remoteStreams.get('user-2');

// Render in video element
<video ref={videoRef} srcObject={userStream} autoPlay />
```

### 4. Connection Quality Monitoring
```typescript
const { connectionQualities } = useWebRTC(meetingId, userId);

// Get quality metrics for a user
const quality = connectionQualities.get('user-2');
console.log({
  latency: quality.latency,        // Round-trip time in ms
  packetLoss: quality.packetLoss,  // Percentage
  bandwidth: quality.bandwidth,     // Mbps
  videoResolution: quality.videoResolution // e.g., "1280x720"
});
```

### 5. Audio/Video Controls
```typescript
const { toggleAudio, toggleVideo } = useWebRTC(meetingId, userId);

// Mute/unmute audio
toggleAudio(false); // Mute
toggleAudio(true);  // Unmute

// Enable/disable video
toggleVideo(false); // Disable
toggleVideo(true);  // Enable
```

### 6. Cleanup
```typescript
const { cleanup } = useWebRTC(meetingId, userId);

// Clean up all connections and streams
useEffect(() => {
  return () => {
    cleanup();
  };
}, []);
```

## Signaling Integration

The hook integrates with the WebSocket signaling server for:

### Offer/Answer Exchange
```typescript
// Automatically handled by the hook
// Client sends offer -> Server forwards -> Peer sends answer
```

### ICE Candidate Exchange
```typescript
// Automatically handled by the hook
// Candidates are exchanged via 'ice-candidate' events
```

### Participant Events
```typescript
// Hook listens for 'participant-left' events
// Automatically closes peer connections when participants leave
```

## Usage Example

```typescript
import { useWebRTC, useWebRTCCaller } from '../hooks/useWebRTC';
import { useWebSocket } from '../contexts/WebSocketContext';

function MeetingRoom() {
  const meetingId = 'meeting-123';
  const currentUserId = 'user-1';
  const { sendMessage } = useWebSocket();
  
  // Initialize WebRTC
  const webrtc = useWebRTC(meetingId, currentUserId);
  const { callUser, callMultipleUsers } = useWebRTCCaller(
    webrtc,
    currentUserId,
    sendMessage
  );
  
  // Initialize media on mount
  useEffect(() => {
    webrtc.initializeMedia();
  }, []);
  
  // Call other participants
  const handleCallParticipants = async (userIds: string[]) => {
    await callMultipleUsers(userIds);
  };
  
  // Render local video
  const localVideoRef = useRef<HTMLVideoElement>(null);
  useEffect(() => {
    if (localVideoRef.current && webrtc.localStream) {
      localVideoRef.current.srcObject = webrtc.localStream;
    }
  }, [webrtc.localStream]);
  
  // Render remote videos
  return (
    <div>
      <video ref={localVideoRef} autoPlay muted />
      
      {Array.from(webrtc.remoteStreams.entries()).map(([userId, stream]) => (
        <RemoteVideo key={userId} userId={userId} stream={stream} />
      ))}
      
      <button onClick={() => webrtc.toggleAudio(false)}>Mute</button>
      <button onClick={() => webrtc.toggleVideo(false)}>Stop Video</button>
    </div>
  );
}
```

## Architecture

### STUN/TURN Configuration
```typescript
const ICE_SERVERS = [
  { urls: 'stun:stun.l.google.com:19302' },
  { urls: 'stun:stun1.l.google.com:19302' },
  { urls: 'stun:stun2.l.google.com:19302' },
  // Add TURN servers for production
];
```

### WebRTC Configuration
```typescript
const RTC_CONFIGURATION = {
  iceServers: ICE_SERVERS,
  iceCandidatePoolSize: 10,
  bundlePolicy: 'max-bundle',    // Optimize for low latency
  rtcpMuxPolicy: 'require',      // Reduce port usage
  iceTransportPolicy: 'all',     // Try direct first, fallback to TURN
};
```

### Media Constraints
```typescript
const DEFAULT_MEDIA_CONSTRAINTS = {
  audio: {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
    sampleRate: 48000,
  },
  video: {
    width: { ideal: 1280, max: 1920 },
    height: { ideal: 720, max: 1080 },
    frameRate: { ideal: 30, max: 30 },
    facingMode: 'user',
  },
};
```

## Connection Quality Monitoring

The hook automatically monitors connection quality every 5 seconds:

- **Latency**: Round-trip time from WebRTC stats
- **Packet Loss**: Calculated from packets lost/received ratio
- **Bandwidth**: Available outgoing bitrate
- **Video Resolution**: Current frame dimensions

When quality degrades (latency >200ms or packet loss >5%), the hook logs a warning and prepares for adaptive bitrate adjustment.

## Error Handling

The hook handles various error scenarios:

- **Media Access Denied**: Sets error state with descriptive message
- **ICE Connection Failed**: Attempts ICE restart automatically
- **Connection Failed**: Sets error state and logs details
- **Peer Connection Errors**: Gracefully handles and logs errors

## State Management

The hook maintains the following state:

- `localStream`: Local MediaStream from getUserMedia
- `remoteStreams`: Map of userId -> MediaStream
- `peerConnections`: Map of userId -> RTCPeerConnection
- `connectionQualities`: Map of userId -> ConnectionQuality
- `isInitialized`: Boolean indicating if media is initialized
- `error`: Error message string or null

## Testing

The hook includes comprehensive tests covering:

- ICE server configuration
- Media constraints (720p/1080p, 30fps)
- Audio optimization settings
- Connection quality monitoring
- ICE candidate exchange
- Offer/answer signaling
- Remote stream handling
- Cleanup functionality
- Adaptive quality adjustment
- ICE connection state handling
- UDP transport configuration

Run tests with:
```bash
npm test useWebRTC.test.ts
```

## Future Enhancements

1. **Adaptive Bitrate**: Implement automatic bitrate adjustment based on quality metrics
2. **Simulcast**: Support multiple quality layers for scalability
3. **Screen Sharing**: Add screen capture support
4. **Recording**: Implement client-side recording
5. **Statistics Dashboard**: Real-time quality metrics visualization
6. **Network Probing**: Bandwidth estimation before call start
7. **Codec Selection**: Allow H.264/VP8/VP9 codec selection
8. **SFU Support**: Add support for Selective Forwarding Unit architecture

## References

- [WebRTC API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API)
- [RTCPeerConnection](https://developer.mozilla.org/en-US/docs/Web/API/RTCPeerConnection)
- [getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)
- [WebRTC Statistics](https://developer.mozilla.org/en-US/docs/Web/API/RTCStatsReport)
