import React, { useState, useEffect, useRef } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import {
  Video,
  VideoOff,
  Mic,
  MicOff,
  Monitor,
  MonitorOff,
  Hand,
  MessageSquare,
  Users,
  Eye,
  Settings,
  LogOut,
  Moon,
  Sun,
  Phone,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import ParticipantTile from '../components/ParticipantTile';
import ChatPanel from '../components/ChatPanel';
import ParticipantsPanel from '../components/ParticipantsPanel';
import ASLCaptionDisplay from '../components/ASLCaptionDisplay';
import ASLAudioPlayer, { getAudioPlayerInstance } from '../components/ASLAudioPlayer';
import { ASLCaptureService, CaptionMessage, AudioMessage, ErrorMessage } from '../services/ASLCaptureService';

interface Participant {
  id: string;
  name: string;
  stream?: MediaStream;
  isMuted: boolean;
  isCameraOn: boolean;
  isHandRaised: boolean;
  isSpeaking?: boolean;
  isLocal?: boolean;
}

interface ChatMessage {
  id: string;
  senderId: string;
  senderName: string;
  text: string;
  timestamp: Date;
}

const VideoCallPage: React.FC = () => {
  const { roomCode } = useParams<{ roomCode: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { theme, toggleTheme, accessibilityMode, toggleAccessibility } = useTheme();

  // Get state from lobby
  const lobbyState = location.state as any;
  const displayName = lobbyState?.displayName || user?.name || 'Guest';

  // Local media state
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [isCameraOn, setIsCameraOn] = useState(false);
  const [isMicOn, setIsMicOn] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [isHandRaised, setIsHandRaised] = useState(false);

  // UI state
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isParticipantsOpen, setIsParticipantsOpen] = useState(false);
  const [showLeaveDialog, setShowLeaveDialog] = useState(false);
  const [fps, setFps] = useState(0);
  
  // ASL state
  const [isASLMode, setIsASLMode] = useState(false);
  const [aslConnected, setAslConnected] = useState(false);
  const [liveCaption, setLiveCaption] = useState('');
  const [confirmedWords, setConfirmedWords] = useState<string[]>([]);
  const [confirmedSentences, setConfirmedSentences] = useState<string[]>([]);
  const [aslError, setAslError] = useState<string | null>(null);
  
  const aslServiceRef = useRef<ASLCaptureService | null>(null);

  // Participants and messages
  const [participants, setParticipants] = useState<Participant[]>([
    {
      id: user?.id || 'local',
      name: displayName,
      isMuted: !isMicOn,
      isCameraOn: isCameraOn,
      isHandRaised: false,
      isLocal: true,
      stream: localStream || undefined,
    },
  ]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const localVideoRef = useRef<HTMLVideoElement>(null);
  const isHost = true; // First person is host

  // Initialize camera
  const initializeCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: true,
      });

      setLocalStream(stream);
      setIsCameraOn(true);

      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      // Update local participant
      setParticipants((prev) =>
        prev.map((p) =>
          p.isLocal ? { ...p, stream, isCameraOn: true } : p
        )
      );

      // Calculate FPS
      let lastTime = Date.now();
      let frames = 0;
      const fpsInterval = setInterval(() => {
        const now = Date.now();
        const delta = (now - lastTime) / 1000;
        setFps(Math.round(frames / delta));
        frames = 0;
        lastTime = now;
      }, 1000);

      const videoTrack = stream.getVideoTracks()[0];
      if (videoTrack) {
        const settings = videoTrack.getSettings();
        if (settings.frameRate) {
          setFps(Math.round(settings.frameRate));
        }
      }

      return () => clearInterval(fpsInterval);
    } catch (error) {
      console.error('Failed to initialize camera:', error);
    }
  };

  // Toggle camera
  const toggleCamera = async () => {
    if (isCameraOn && localStream) {
      localStream.getVideoTracks().forEach((track) => track.stop());
      setIsCameraOn(false);
      setFps(0);
      setParticipants((prev) =>
        prev.map((p) => (p.isLocal ? { ...p, isCameraOn: false } : p))
      );
    } else {
      await initializeCamera();
    }
  };

  // Toggle microphone
  const toggleMic = () => {
    if (localStream) {
      localStream.getAudioTracks().forEach((track) => {
        track.enabled = !track.enabled;
      });
      setIsMicOn(!isMicOn);
      setParticipants((prev) =>
        prev.map((p) => (p.isLocal ? { ...p, isMuted: isMicOn } : p))
      );
    }
  };

  // Toggle screen share
  const toggleScreenShare = async () => {
    if (isScreenSharing) {
      // Stop screen sharing
      setIsScreenSharing(false);
    } else {
      try {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
        });
        setIsScreenSharing(true);

        // Stop screen share when user stops it from browser
        screenStream.getVideoTracks()[0].onended = () => {
          setIsScreenSharing(false);
        };
      } catch (error) {
        console.error('Failed to share screen:', error);
      }
    }
  };

  // Toggle hand raise
  const toggleHandRaise = () => {
    setIsHandRaised(!isHandRaised);
    setParticipants((prev) =>
      prev.map((p) => (p.isLocal ? { ...p, isHandRaised: !isHandRaised } : p))
    );
  };

  // Send message
  const handleSendMessage = (text: string) => {
    const message: ChatMessage = {
      id: Date.now().toString(),
      senderId: user?.id || 'local',
      senderName: displayName,
      text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, message]);
  };

  // Mute participant (admin only)
  const handleMuteParticipant = (participantId: string) => {
    if (isHost) {
      setParticipants((prev) =>
        prev.map((p) => (p.id === participantId ? { ...p, isMuted: true } : p))
      );
    }
  };

  // Remove participant (admin only)
  const handleRemoveParticipant = (participantId: string) => {
    if (isHost) {
      if (confirm('Remove this participant from the meeting?')) {
        setParticipants((prev) => prev.filter((p) => p.id !== participantId));
      }
    }
  };

  // Mute all (admin only)
  const handleMuteAll = () => {
    if (isHost) {
      if (confirm('Mute all participants?')) {
        setParticipants((prev) =>
          prev.map((p) => (p.isLocal ? p : { ...p, isMuted: true }))
        );
      }
    }
  };

  // Leave meeting
  const handleLeaveMeeting = () => {
    if (localStream) {
      localStream.getTracks().forEach((track) => track.stop());
    }
    
    // Stop ASL service
    if (aslServiceRef.current) {
      aslServiceRef.current.stop();
      aslServiceRef.current = null;
    }
    
    navigate('/dashboard');
  };
  
  // Toggle ASL mode
  const toggleASLMode = async () => {
    if (isASLMode) {
      // Stop ASL mode
      if (aslServiceRef.current) {
        aslServiceRef.current.stop();
        aslServiceRef.current = null;
      }
      setIsASLMode(false);
      setAslConnected(false);
      setLiveCaption('');
      setConfirmedWords([]);
      setAslError(null);
    } else {
      // Start ASL mode
      try {
        const service = new ASLCaptureService({
          sessionId: roomCode || 'default',
          userId: user?.id || 'guest',
          backendUrl: 'ws://localhost:8000'
        });
        
        // Register callbacks
        service.onCaption((caption: CaptionMessage) => {
          if (caption.level === 'live') {
            setLiveCaption(caption.text);
          } else if (caption.level === 'word') {
            setConfirmedWords(caption.text.split(' '));
          } else if (caption.level === 'sentence') {
            setConfirmedSentences(prev => [...prev, caption.text]);
            setConfirmedWords([]);
            setLiveCaption('');
          }
        });
        
        service.onAudio((audio: AudioMessage) => {
          const audioPlayer = getAudioPlayerInstance();
          if (audioPlayer) {
            audioPlayer.addToQueue(audio);
          }
        });
        
        service.onError((error: ErrorMessage) => {
          console.error('ASL error:', error);
          setAslError(error.message);
          
          if (error.severity === 'fatal') {
            setIsASLMode(false);
            setAslConnected(false);
          }
        });
        
        service.onConnectionChange((connected: boolean) => {
          setAslConnected(connected);
        });
        
        // Start service
        await service.start();
        aslServiceRef.current = service;
        setIsASLMode(true);
        
      } catch (error) {
        console.error('Failed to start ASL mode:', error);
        setAslError(error instanceof Error ? error.message : 'Failed to start ASL mode');
      }
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (e.key.toLowerCase()) {
        case 'm':
          toggleMic();
          break;
        case 'v':
          toggleCamera();
          break;
        case 's':
          toggleScreenShare();
          break;
        case 'r':
          toggleHandRaise();
          break;
        case 'c':
          setIsChatOpen((prev) => !prev);
          break;
        case 'p':
          setIsParticipantsOpen((prev) => !prev);
          break;
        case 'a':
          toggleAccessibility();
          break;
        case 'l':
          setShowLeaveDialog(true);
          break;
        case 'escape':
          setIsChatOpen(false);
          setIsParticipantsOpen(false);
          setShowLeaveDialog(false);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isMicOn, isCameraOn, isScreenSharing, isHandRaised]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (localStream) {
        localStream.getTracks().forEach((track) => track.stop());
      }
      if (aslServiceRef.current) {
        aslServiceRef.current.stop();
      }
    };
  }, [localStream]);

  // Grid layout based on participant count
  const getGridCols = () => {
    const count = participants.length;
    if (count === 1) return 'grid-cols-1';
    if (count <= 4) return 'grid-cols-2';
    if (count <= 9) return 'grid-cols-3';
    return 'grid-cols-4';
  };

  return (
    <div className="h-screen bg-gray-900 dark:bg-black flex flex-col">
      {/* Header */}
      <div className="bg-gray-800 dark:bg-gray-900 border-b border-gray-700 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-white font-semibold">Room: {roomCode}</h1>
          {isCameraOn && fps > 0 && (
            <div
              className={`px-3 py-1 rounded-full text-xs font-semibold ${
                fps > 20
                  ? 'bg-green-500/20 text-green-400'
                  : fps > 10
                  ? 'bg-yellow-500/20 text-yellow-400'
                  : 'bg-red-500/20 text-red-400'
              }`}
            >
              {fps} FPS
            </div>
          )}
          {accessibilityMode && (
            <div className="px-3 py-1 bg-purple-500/20 text-purple-400 rounded-full text-xs font-semibold">
              Sign Language Mode
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={toggleTheme}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            title="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="w-5 h-5 text-yellow-400" />
            ) : (
              <Moon className="w-5 h-5 text-gray-400" />
            )}
          </button>
          <button
            onClick={toggleAccessibility}
            className={`p-2 hover:bg-gray-700 rounded-lg transition-colors ${
              accessibilityMode ? 'bg-purple-600' : ''
            }`}
            title="Toggle accessibility mode"
          >
            <Eye className="w-5 h-5 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center p-6 overflow-hidden relative">
        <div className={`grid ${getGridCols()} gap-4 max-w-7xl w-full`}>
          {participants.map((participant) => (
            <ParticipantTile
              key={participant.id}
              participant={participant}
              isAdmin={isHost && user?.isAdmin}
              onMute={handleMuteParticipant}
              onRemove={handleRemoveParticipant}
            />
          ))}
        </div>
        
        {/* ASL Caption Display */}
        {isASLMode && (
          <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 w-full max-w-2xl px-4">
            <ASLCaptionDisplay
              liveCaption={liveCaption}
              confirmedWords={confirmedWords}
              confirmedSentences={confirmedSentences}
            />
            
            {/* ASL Status Indicator */}
            <div className="mt-4 flex items-center justify-center gap-2">
              <div className={`w-3 h-3 rounded-full ${aslConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
              <span className="text-white text-sm">
                {aslConnected ? 'ASL Recognition Active' : 'Connecting...'}
              </span>
            </div>
            
            {/* ASL Error Display */}
            {aslError && (
              <div className="mt-2 bg-red-500/20 border border-red-500 rounded-lg p-3 text-red-200 text-sm">
                {aslError}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Control Bar */}
      <div className="bg-gray-800 dark:bg-gray-900 border-t border-gray-700 px-6 py-4">
        <div className="flex items-center justify-center gap-3">
          {/* Camera */}
          <button
            onClick={toggleCamera}
            className={`p-4 rounded-full transition-colors ${
              isCameraOn
                ? 'bg-gray-700 hover:bg-gray-600'
                : 'bg-red-600 hover:bg-red-700'
            }`}
            title="Toggle camera (V)"
          >
            {isCameraOn ? (
              <Video className="w-6 h-6 text-white" />
            ) : (
              <VideoOff className="w-6 h-6 text-white" />
            )}
          </button>

          {/* Microphone */}
          <button
            onClick={toggleMic}
            className={`p-4 rounded-full transition-colors ${
              isMicOn
                ? 'bg-gray-700 hover:bg-gray-600'
                : 'bg-red-600 hover:bg-red-700'
            }`}
            title="Toggle microphone (M)"
          >
            {isMicOn ? (
              <Mic className="w-6 h-6 text-white" />
            ) : (
              <MicOff className="w-6 h-6 text-white" />
            )}
          </button>

          {/* Screen Share */}
          <button
            onClick={toggleScreenShare}
            className={`p-4 rounded-full transition-colors ${
              isScreenSharing
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
            title="Share screen (S)"
          >
            {isScreenSharing ? (
              <MonitorOff className="w-6 h-6 text-white" />
            ) : (
              <Monitor className="w-6 h-6 text-white" />
            )}
          </button>

          {/* Raise Hand */}
          <button
            onClick={toggleHandRaise}
            className={`p-4 rounded-full transition-colors ${
              isHandRaised
                ? 'bg-yellow-600 hover:bg-yellow-700'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
            title="Raise hand (R)"
          >
            <Hand className="w-6 h-6 text-white" />
          </button>
          
          {/* ASL Mode Toggle */}
          <button
            onClick={toggleASLMode}
            className={`p-4 rounded-full transition-colors ${
              isASLMode
                ? 'bg-purple-600 hover:bg-purple-700'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
            title="Toggle ASL mode"
          >
            <Eye className="w-6 h-6 text-white" />
          </button>

          {/* Chat */}
          <button
            onClick={() => setIsChatOpen(!isChatOpen)}
            className={`p-4 rounded-full transition-colors relative ${
              isChatOpen
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
            title="Toggle chat (C)"
          >
            <MessageSquare className="w-6 h-6 text-white" />
            {messages.length > 0 && !isChatOpen && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-xs flex items-center justify-center text-white">
                {messages.length}
              </span>
            )}
          </button>

          {/* Participants */}
          <button
            onClick={() => setIsParticipantsOpen(!isParticipantsOpen)}
            className={`p-4 rounded-full transition-colors ${
              isParticipantsOpen
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
            title="Toggle participants (P)"
          >
            <Users className="w-6 h-6 text-white" />
          </button>

          {/* Leave */}
          <button
            onClick={() => setShowLeaveDialog(true)}
            className="p-4 rounded-full bg-red-600 hover:bg-red-700 transition-colors ml-4"
            title="Leave meeting (L)"
          >
            <Phone className="w-6 h-6 text-white transform rotate-135" />
          </button>
        </div>
      </div>

      {/* Chat Panel */}
      <ChatPanel
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        messages={messages}
        onSendMessage={handleSendMessage}
        currentUserId={user?.id || 'local'}
      />

      {/* Participants Panel */}
      <ParticipantsPanel
        isOpen={isParticipantsOpen}
        onClose={() => setIsParticipantsOpen(false)}
        participants={participants}
        isHost={isHost && !!user?.isAdmin}
        onMuteParticipant={handleMuteParticipant}
        onRemoveParticipant={handleRemoveParticipant}
        onMuteAll={handleMuteAll}
      />

      {/* Leave Dialog */}
      {showLeaveDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Leave Meeting?
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Are you sure you want to leave this meeting?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowLeaveDialog(false)}
                className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleLeaveMeeting}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                Leave
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hidden video element for local stream */}
      <video ref={localVideoRef} autoPlay playsInline muted className="hidden" />
      
      {/* ASL Audio Player */}
      {isASLMode && <ASLAudioPlayer />}
    </div>
  );
};

export default VideoCallPage;
