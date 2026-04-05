import { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useMeeting } from '../contexts/MeetingContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useAuth } from '../contexts/AuthContext';
import { useWebRTC } from '../hooks/useWebRTC';
import VideoGrid from '../components/VideoGrid';
import ControlBar from '../components/ControlBar';
import ChatPanel, { ChatMessage } from '../components/ChatPanel';

/**
 * MeetingRoom Component
 * 
 * Main meeting room page component that manages the overall meeting state and layout.
 * 
 * Requirements:
 * - 22.1: Detect active speaker based on audio levels
 * - 22.2: Highlight active speaker within 300ms
 * - 22.3: Enlarge active speaker's video in layout
 * - 22.7: Allow manual pinning of participant video
 * 
 * Features:
 * - Participant list state management
 * - Active speaker detection state
 * - Layout switching (grid, spotlight, sidebar)
 * - Socket.IO event handling for participant join/leave
 */
export default function MeetingRoom() {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  
  // Get session state from navigation
  const sessionState = location.state as {
    room_code?: string;
    display_name?: string;
    displayName?: string;
    accessibility_mode?: boolean;
    accessibilityMode?: boolean;
    camera_preview_granted?: boolean;
    cameraEnabled?: boolean;
    micEnabled?: boolean;
  } | null;
  
  // Meeting context
  const {
    meetingId,
    setMeetingId,
    participants,
    addParticipant,
    removeParticipant,
    updateParticipant,
    activeLayout,
    setActiveLayout,
    activeSpeaker,
    setActiveSpeaker,
    activeSigner,
    setActiveSigner,
    pinnedParticipant,
    setPinnedParticipant,
    isRecording,
    screenSharingParticipant,
    setScreenSharingParticipant,
  } = useMeeting();
  
  // WebSocket context
  const { isConnected, sendMessage, subscribe, connect, disconnect } = useWebSocket();
  
  // Local state
  const [isJoining, setIsJoining] = useState(true);
  const [joinError, setJoinError] = useState<string | null>(null);
  const [currentUserId] = useState(() => user?.id || `user_${Date.now()}`);
  const [displayName] = useState(() => 
    sessionState?.display_name || 
    sessionState?.displayName || 
    user?.name || 
    'Guest'
  );
  const [localAudioEnabled, setLocalAudioEnabled] = useState(sessionState?.micEnabled ?? true);
  const [localVideoEnabled, setLocalVideoEnabled] = useState(sessionState?.cameraEnabled ?? true);
  const [localScreenSharing, setLocalScreenSharing] = useState(false);
  const [localHandRaised, setLocalHandRaised] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  
  // WebRTC hook for video/audio streams
  const webrtc = useWebRTC(roomCode || '', currentUserId);
  
  // Initialize meeting
  useEffect(() => {
    if (!roomCode) {
      navigate('/');
      return;
    }
    
    // Set meeting ID
    setMeetingId(roomCode);
    
    // Connect to WebSocket
    connect(roomCode, currentUserId);
    
    // Initialize media (camera and microphone)
    const initMedia = async () => {
      try {
        await webrtc.initializeMedia();
      } catch (err) {
        console.error('Failed to initialize media:', err);
        // Continue even if media initialization fails
      }
    };
    
    initMedia();
    
    return () => {
      // Cleanup on unmount
      if (meetingId) {
        sendMessage('leave-meeting', {
          meetingId: roomCode,
          userId: currentUserId,
        });
      }
      webrtc.cleanup();
      disconnect();
    };
  }, [roomCode]);
  
  // Handle Socket.IO events
  useEffect(() => {
    if (!isConnected) return;
    
    // Subscribe to join-meeting-success event
    const unsubscribeJoinSuccess = subscribe('join-meeting-success', (data: any) => {
      console.log('Join meeting success:', data);
      setIsJoining(false);
      
      // Add existing participants to state
      if (data.participants && Array.isArray(data.participants)) {
        data.participants.forEach((p: any) => {
          addParticipant({
            id: p.userId,
            userId: p.userId,
            name: p.userName || 'Participant',
            audioEnabled: p.audioEnabled ?? true,
            videoEnabled: p.videoEnabled ?? true,
            isHost: false,
            isCoHost: false,
            handRaised: false,
            isSpeaking: false,
            isSigning: false,
            joinedAt: new Date(p.joinedAt || Date.now()),
          });
        });
      }
    });
    
    // Subscribe to participant-joined event (Requirement 22.1)
    const unsubscribeParticipantJoined = subscribe('participant-joined', (data: any) => {
      console.log('Participant joined:', data);
      
      if (data.participant) {
        const p = data.participant;
        addParticipant({
          id: p.userId,
          userId: p.userId,
          name: p.userName || 'Participant',
          audioEnabled: p.audioEnabled ?? true,
          videoEnabled: p.videoEnabled ?? true,
          isHost: false,
          isCoHost: false,
          handRaised: false,
          isSpeaking: false,
          isSigning: false,
          joinedAt: new Date(p.joinedAt || Date.now()),
        });
      }
    });
    
    // Subscribe to participant-left event
    const unsubscribeParticipantLeft = subscribe('participant-left', (data: any) => {
      console.log('Participant left:', data);
      
      if (data.userId) {
        removeParticipant(data.userId);
      }
    });
    
    // Subscribe to participant-updated event (Requirement 22.2)
    const unsubscribeParticipantUpdated = subscribe('participant-updated', (data: any) => {
      console.log('Participant updated:', data);
      
      if (data.userId && data.updates) {
        updateParticipant(data.userId, {
          audioEnabled: data.updates.audioEnabled,
          videoEnabled: data.updates.videoEnabled,
          handRaised: data.updates.handRaised,
          isSpeaking: data.updates.isSpeaking,
          isSigning: data.updates.isSigning,
        });
        
        // Update active speaker if speaking status changed (Requirement 22.1, 22.2)
        if (data.updates.isSpeaking !== undefined) {
          if (data.updates.isSpeaking) {
            setActiveSpeaker(data.userId);
          } else if (activeSpeaker === data.userId) {
            setActiveSpeaker(null);
          }
        }
        
        // Update active signer if signing status changed
        if (data.updates.isSigning !== undefined) {
          if (data.updates.isSigning) {
            setActiveSigner(data.userId);
          } else if (activeSigner === data.userId) {
            setActiveSigner(null);
          }
        }
        
        // Update screen sharing participant
        if (data.updates.screenSharing !== undefined) {
          if (data.updates.screenSharing) {
            setScreenSharingParticipant(data.userId);
          } else if (screenSharingParticipant === data.userId) {
            setScreenSharingParticipant(null);
          }
        }
      }
    });
    
    // Subscribe to active-speaker-changed event (Requirement 22.1, 22.2)
    const unsubscribeActiveSpeaker = subscribe('active-speaker-changed', (data: any) => {
      console.log('Active speaker changed:', data);
      
      if (data.userId) {
        setActiveSpeaker(data.userId);
      } else {
        setActiveSpeaker(null);
      }
    });
    
    // Subscribe to active-signer-detected event
    const unsubscribeActiveSigner = subscribe('active-signer-detected', (data: any) => {
      console.log('Active signer detected:', data);
      
      if (data.userId) {
        setActiveSigner(data.userId);
      } else {
        setActiveSigner(null);
      }
    });
    
    // Subscribe to error event
    const unsubscribeError = subscribe('error', (data: any) => {
      console.error('Socket error:', data);
      setJoinError(data.message || 'An error occurred');
    });
    
    // Subscribe to chat-message event (Requirement 10.3)
    const unsubscribeChatMessage = subscribe('chat-message', (data: any) => {
      console.log('Chat message received:', data);
      
      if (data.id && data.senderId && data.senderName && data.messageText && data.timestamp) {
        const newMessage: ChatMessage = {
          id: data.id,
          senderId: data.senderId,
          senderName: data.senderName,
          messageText: data.messageText,
          timestamp: data.timestamp,
          isPrivate: data.isPrivate || false,
        };
        
        setChatMessages((prev) => [...prev, newMessage]);
      }
    });
    
    // Join the meeting
    sendMessage('join-meeting', {
      meetingId: roomCode,
      userId: currentUserId,
      userName: displayName,
      mediaCapabilities: {
        audio: sessionState?.micEnabled ?? true,
        video: sessionState?.cameraEnabled ?? true,
        screenShare: true,
      },
    });
    
    // Cleanup subscriptions
    return () => {
      unsubscribeJoinSuccess();
      unsubscribeParticipantJoined();
      unsubscribeParticipantLeft();
      unsubscribeParticipantUpdated();
      unsubscribeActiveSpeaker();
      unsubscribeActiveSigner();
      unsubscribeError();
      unsubscribeChatMessage();
    };
  }, [isConnected, roomCode, currentUserId, displayName]);
  
  // Handle layout switching (Requirement 22.4, 22.5, 22.6)
  const handleLayoutChange = (layout: 'grid' | 'spotlight' | 'sidebar' | 'accessibility') => {
    setActiveLayout(layout);
  };
  
  // Handle manual pin (Requirement 22.7)
  const handlePinParticipant = (participantId: string | null) => {
    setPinnedParticipant(participantId);
  };
  
  // Handle leave meeting
  const handleLeaveMeeting = () => {
    sendMessage('leave-meeting', {
      meetingId: roomCode,
      userId: currentUserId,
    });
    
    navigate('/');
  };
  
  // Handle audio toggle
  const handleToggleAudio = (enabled: boolean) => {
    setLocalAudioEnabled(enabled);
    webrtc.toggleAudio(enabled);
  };
  
  // Handle video toggle
  const handleToggleVideo = (enabled: boolean) => {
    setLocalVideoEnabled(enabled);
    webrtc.toggleVideo(enabled);
  };
  
  // Handle screen share toggle
  const handleToggleScreenShare = async () => {
    try {
      if (localScreenSharing) {
        // Stop screen sharing
        webrtc.stopScreenShare();
        setLocalScreenSharing(false);
        
        // Notify server
        sendMessage('stop-screen-share', {
          meetingId: roomCode,
          userId: currentUserId,
        });
      } else {
        // Start screen sharing
        await webrtc.startScreenShare();
        setLocalScreenSharing(true);
        
        // Notify server
        sendMessage('start-screen-share', {
          meetingId: roomCode,
          userId: currentUserId,
        });
      }
    } catch (err) {
      console.error('Error toggling screen share:', err);
      setLocalScreenSharing(false);
    }
  };
  
  // Handle hand raise toggle
  const handleToggleHandRaise = () => {
    setLocalHandRaised(!localHandRaised);
  };
  
  // Handle chat toggle
  const handleToggleChat = () => {
    setIsChatOpen(!isChatOpen);
  };
  
  // Handle send chat message (Requirement 10.1, 10.3)
  const handleSendChatMessage = (messageText: string) => {
    sendMessage('send-chat-message', {
      meetingId: roomCode,
      senderId: currentUserId,
      senderName: displayName,
      messageText: messageText,
    });
  };
  
  // Loading state
  if (isJoining) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-navy-950">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <div className="text-white text-lg">Joining meeting...</div>
          <div className="text-gray-400 text-sm mt-2">Room: {roomCode}</div>
        </div>
      </div>
    );
  }
  
  // Error state
  if (joinError) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-navy-950">
        <div className="max-w-md w-full bg-navy-900/50 backdrop-blur-xl border border-red-500/30 rounded-2xl shadow-2xl p-8">
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-red-500/20 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Failed to Join Meeting</h2>
            <p className="text-gray-400 mb-6">{joinError}</p>
            <button
              onClick={() => navigate('/')}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Return to Home
            </button>
          </div>
        </div>
      </div>
    );
  }
  
  // Main meeting room UI
  return (
    <div className="flex flex-col h-screen bg-navy-950">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-navy-900/50 backdrop-blur-xl border-b border-white/10">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-white">Meeting Room</h1>
          <div className="px-3 py-1 bg-navy-800 rounded-lg">
            <span className="text-gray-400 text-sm">Room: </span>
            <span className="text-white text-sm font-mono">{roomCode}</span>
          </div>
          {isRecording && (
            <div className="flex items-center gap-2 px-3 py-1 bg-red-500/20 border border-red-500/30 rounded-lg">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              <span className="text-red-400 text-sm font-medium">Recording</span>
            </div>
          )}
          {screenSharingParticipant && (
            <div className="flex items-center gap-2 px-3 py-1 bg-blue-500/20 border border-blue-500/30 rounded-lg">
              <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <span className="text-blue-400 text-sm font-medium">
                {screenSharingParticipant === currentUserId ? 'You are' : 'Someone is'} sharing screen
              </span>
            </div>
          )}
        </div>
        
        {/* Layout Controls (Requirement 22.4, 22.5, 22.6) */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 bg-navy-800 rounded-lg p-1">
            <button
              onClick={() => handleLayoutChange('grid')}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activeLayout === 'grid'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-navy-700'
              }`}
              title="Grid View"
            >
              Grid
            </button>
            <button
              onClick={() => handleLayoutChange('spotlight')}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activeLayout === 'spotlight'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-navy-700'
              }`}
              title="Spotlight View"
            >
              Spotlight
            </button>
            <button
              onClick={() => handleLayoutChange('sidebar')}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activeLayout === 'sidebar'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-navy-700'
              }`}
              title="Sidebar View"
            >
              Sidebar
            </button>
            {sessionState?.accessibility_mode && (
              <button
                onClick={() => handleLayoutChange('accessibility')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeLayout === 'accessibility'
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-navy-700'
                }`}
                title="Accessibility Layout"
              >
                A11y
              </button>
            )}
          </div>
          
          <button
            onClick={handleLeaveMeeting}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
          >
            Leave Meeting
          </button>
        </div>
      </div>
      
      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Video Grid Area */}
        <div className="flex-1 p-4">
          <VideoGrid
            participants={participants}
            localStream={webrtc.localStream}
            remoteStreams={webrtc.remoteStreams}
            currentUserId={currentUserId}
            layout={activeLayout}
            activeSpeaker={activeSpeaker}
            pinnedParticipant={pinnedParticipant}
            screenSharingParticipant={screenSharingParticipant}
            onPinParticipant={handlePinParticipant}
          />
        </div>
        
        {/* Sidebar for participants list */}
        <div className="w-80 bg-navy-900/50 backdrop-blur-xl border-l border-white/10 p-4 overflow-y-auto">
          <h2 className="text-white font-semibold mb-4">
            Participants ({participants.length})
          </h2>
          
          <div className="space-y-2">
            {participants.map((participant) => (
              <div
                key={participant.id}
                className={`p-3 rounded-lg border transition-colors ${
                  activeSpeaker === participant.id
                    ? 'bg-blue-500/20 border-blue-500/50'
                    : pinnedParticipant === participant.id
                    ? 'bg-purple-500/20 border-purple-500/50'
                    : 'bg-navy-800 border-white/5 hover:border-white/10'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-white text-sm font-medium">
                        {participant.name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-white text-sm font-medium truncate">
                        {participant.name}
                        {participant.id === currentUserId && ' (You)'}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        {participant.audioEnabled ? (
                          <svg className="w-3 h-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M7 4a3 3 0 016 0v6a3 3 0 11-6 0V4z" />
                            <path d="M5.5 9.643a.75.75 0 00-1.5 0V10c0 3.06 2.29 5.585 5.25 5.954V17.5h-1.5a.75.75 0 000 1.5h4.5a.75.75 0 000-1.5h-1.5v-1.546A6.001 6.001 0 0016 10v-.357a.75.75 0 00-1.5 0V10a4.5 4.5 0 01-9 0v-.357z" />
                          </svg>
                        ) : (
                          <svg className="w-3 h-3 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M3.28 2.22a.75.75 0 00-1.06 1.06l14.5 14.5a.75.75 0 101.06-1.06l-1.5-1.5A6.01 6.01 0 0016 10v-.357a.75.75 0 00-1.5 0V10a4.5 4.5 0 01-.83 2.6l-1.2-1.2A3 3 0 0013 10V4a3 3 0 00-4.93-2.32L6.85 3.9A4.5 4.5 0 017 4v.357a.75.75 0 001.5 0V4a3 3 0 00-3-3c-.36 0-.71.06-1.03.18L3.28 2.22z" />
                          </svg>
                        )}
                        {participant.videoEnabled ? (
                          <svg className="w-3 h-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
                          </svg>
                        ) : (
                          <svg className="w-3 h-3 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M3.28 2.22a.75.75 0 00-1.06 1.06l14.5 14.5a.75.75 0 101.06-1.06l-1.5-1.5A6.01 6.01 0 0016 10v-.357a.75.75 0 00-1.5 0V10a4.5 4.5 0 01-.83 2.6l-1.2-1.2A3 3 0 0013 10V4a3 3 0 00-4.93-2.32L6.85 3.9A4.5 4.5 0 017 4v.357a.75.75 0 001.5 0V4a3 3 0 00-3-3c-.36 0-.71.06-1.03.18L3.28 2.22z" />
                          </svg>
                        )}
                        {participant.isSpeaking && (
                          <span className="text-blue-400 text-xs">Speaking</span>
                        )}
                        {participant.handRaised && (
                          <span className="text-yellow-400 text-xs">✋</span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Pin button (Requirement 22.7) */}
                  <button
                    onClick={() => handlePinParticipant(
                      pinnedParticipant === participant.id ? null : participant.id
                    )}
                    className={`p-1 rounded transition-colors ${
                      pinnedParticipant === participant.id
                        ? 'text-purple-400 hover:text-purple-300'
                        : 'text-gray-400 hover:text-white'
                    }`}
                    title={pinnedParticipant === participant.id ? 'Unpin' : 'Pin participant'}
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L11 4.323V3a1 1 0 011-1zm-5 8.274l-.818 2.552c-.25.78.409 1.574 1.195 1.574H6.5a1 1 0 01.894.553l.448.894a1 1 0 001.788 0l.448-.894A1 1 0 0111 13.4h1.123c.786 0 1.445-.794 1.195-1.574L12.5 10.274V3.5a1.5 1.5 0 00-3 0v6.774z" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
          
          {participants.length === 0 && (
            <div className="text-center text-gray-400 text-sm mt-8">
              No other participants yet
            </div>
          )}
        </div>
      </div>
      
      {/* Control Bar */}
      <div className="px-6 py-4 bg-navy-900/50 backdrop-blur-xl border-t border-white/10">
        <div className="flex items-center justify-between">
          <ControlBar
            meetingId={roomCode || ''}
            userId={currentUserId}
            audioEnabled={localAudioEnabled}
            videoEnabled={localVideoEnabled}
            screenSharing={localScreenSharing}
            handRaised={localHandRaised}
            onToggleAudio={handleToggleAudio}
            onToggleVideo={handleToggleVideo}
            onToggleScreenShare={handleToggleScreenShare}
            onToggleHandRaise={handleToggleHandRaise}
            onLeaveMeeting={handleLeaveMeeting}
          />
          
          {/* Chat Button */}
          <button
            onClick={handleToggleChat}
            className={`relative px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              isChatOpen
                ? 'bg-blue-600 text-white'
                : 'bg-navy-800 text-gray-300 hover:bg-navy-700 hover:text-white'
            }`}
            title="Toggle chat"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span className="text-sm font-medium">Chat</span>
            {chatMessages.length > 0 && !isChatOpen && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                {chatMessages.length > 9 ? '9+' : chatMessages.length}
              </span>
            )}
          </button>
        </div>
      </div>
      
      {/* Chat Panel - Requirements 10.1, 10.3, 10.4, 10.5, 10.7 */}
      <ChatPanel
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        messages={chatMessages}
        onSendMessage={handleSendChatMessage}
        currentUserId={currentUserId}
        currentUserName={displayName}
      />
    </div>
  );
}
