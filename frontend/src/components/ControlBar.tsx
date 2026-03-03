import { useState, useRef, useEffect } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';

/**
 * ControlBar Component
 * 
 * Requirements:
 * - 2.1: Allow participants to share their screen
 * - 7.1: Allow participants to raise their hand with a single click
 * - 7.6: Provide at least 5 emoji reactions
 * - 15.1: Allow host to mute individual participants
 * 
 * Features:
 * - Audio/video toggle buttons with visual feedback
 * - Screen sharing button
 * - Reactions button with emoji picker popup
 * - Hand raise button
 * - Leave meeting button
 * - UI state updates based on media state
 */

interface ControlBarProps {
  meetingId: string;
  userId: string;
  audioEnabled: boolean;
  videoEnabled: boolean;
  screenSharing: boolean;
  handRaised: boolean;
  onToggleAudio: (enabled: boolean) => void;
  onToggleVideo: (enabled: boolean) => void;
  onToggleScreenShare: () => void;
  onToggleHandRaise: () => void;
  onLeaveMeeting: () => void;
}

// Emoji reactions (Requirement 7.6)
const REACTIONS = [
  { emoji: '👍', label: 'Thumbs up' },
  { emoji: '👏', label: 'Clapping' },
  { emoji: '❤️', label: 'Heart' },
  { emoji: '🤔', label: 'Thinking' },
  { emoji: '😂', label: 'Laughing' },
];

export default function ControlBar({
  meetingId,
  userId,
  audioEnabled,
  videoEnabled,
  screenSharing,
  handRaised,
  onToggleAudio,
  onToggleVideo,
  onToggleScreenShare,
  onToggleHandRaise,
  onLeaveMeeting,
}: ControlBarProps) {
  const { sendMessage } = useWebSocket();
  const [showReactions, setShowReactions] = useState(false);
  const reactionsRef = useRef<HTMLDivElement>(null);

  // Close reactions picker when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (reactionsRef.current && !reactionsRef.current.contains(event.target as Node)) {
        setShowReactions(false);
      }
    };

    if (showReactions) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showReactions]);

  // Handle audio toggle
  const handleAudioToggle = () => {
    const newState = !audioEnabled;
    onToggleAudio(newState);
    
    // Send event to server
    sendMessage('toggle-audio', {
      meetingId,
      userId,
      enabled: newState,
    });
  };

  // Handle video toggle
  const handleVideoToggle = () => {
    const newState = !videoEnabled;
    onToggleVideo(newState);
    
    // Send event to server
    sendMessage('toggle-video', {
      meetingId,
      userId,
      enabled: newState,
    });
  };

  // Handle screen share toggle (Requirement 2.1)
  const handleScreenShareToggle = () => {
    onToggleScreenShare();
    
    // Send event to server
    if (screenSharing) {
      sendMessage('stop-screen-share', {
        meetingId,
        userId,
      });
    } else {
      sendMessage('start-screen-share', {
        meetingId,
        userId,
      });
    }
  };

  // Handle hand raise toggle (Requirement 7.1)
  const handleHandRaiseToggle = () => {
    const newState = !handRaised;
    onToggleHandRaise();
    
    // Send event to server
    sendMessage('raise-hand', {
      meetingId,
      userId,
      raised: newState,
    });
  };

  // Handle reaction send (Requirement 7.6)
  const handleReactionSend = (emoji: string) => {
    sendMessage('send-reaction', {
      meetingId,
      userId,
      reaction: emoji,
    });
    
    setShowReactions(false);
  };

  return (
    <div className="flex items-center justify-center gap-3">
      {/* Audio Toggle Button */}
      <button
        onClick={handleAudioToggle}
        className={`group relative p-4 rounded-full transition-all ${
          audioEnabled
            ? 'bg-navy-800 hover:bg-navy-700'
            : 'bg-red-600 hover:bg-red-700'
        }`}
        title={audioEnabled ? 'Mute microphone' : 'Unmute microphone'}
      >
        {audioEnabled ? (
          <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path d="M7 4a3 3 0 016 0v6a3 3 0 11-6 0V4z" />
            <path d="M5.5 9.643a.75.75 0 00-1.5 0V10c0 3.06 2.29 5.585 5.25 5.954V17.5h-1.5a.75.75 0 000 1.5h4.5a.75.75 0 000-1.5h-1.5v-1.546A6.001 6.001 0 0016 10v-.357a.75.75 0 00-1.5 0V10a4.5 4.5 0 01-9 0v-.357z" />
          </svg>
        ) : (
          <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path d="M3.28 2.22a.75.75 0 00-1.06 1.06l14.5 14.5a.75.75 0 101.06-1.06l-1.5-1.5A6.01 6.01 0 0016 10v-.357a.75.75 0 00-1.5 0V10a4.5 4.5 0 01-.83 2.6l-1.2-1.2A3 3 0 0013 10V4a3 3 0 00-4.93-2.32L6.85 3.9A4.5 4.5 0 017 4v.357a.75.75 0 001.5 0V4a3 3 0 00-3-3c-.36 0-.71.06-1.03.18L3.28 2.22z" />
          </svg>
        )}
        
        {/* Tooltip */}
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1 bg-navy-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
          {audioEnabled ? 'Mute' : 'Unmute'}
        </div>
      </button>

      {/* Video Toggle Button */}
      <button
        onClick={handleVideoToggle}
        className={`group relative p-4 rounded-full transition-all ${
          videoEnabled
            ? 'bg-navy-800 hover:bg-navy-700'
            : 'bg-red-600 hover:bg-red-700'
        }`}
        title={videoEnabled ? 'Turn off camera' : 'Turn on camera'}
      >
        {videoEnabled ? (
          <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
          </svg>
        ) : (
          <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path d="M3.28 2.22a.75.75 0 00-1.06 1.06l14.5 14.5a.75.75 0 101.06-1.06l-1.5-1.5A6.01 6.01 0 0016 10v-.357a.75.75 0 00-1.5 0V10a4.5 4.5 0 01-.83 2.6l-1.2-1.2A3 3 0 0013 10V4a3 3 0 00-4.93-2.32L6.85 3.9A4.5 4.5 0 017 4v.357a.75.75 0 001.5 0V4a3 3 0 00-3-3c-.36 0-.71.06-1.03.18L3.28 2.22z" />
          </svg>
        )}
        
        {/* Tooltip */}
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1 bg-navy-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
          {videoEnabled ? 'Stop video' : 'Start video'}
        </div>
      </button>

      {/* Screen Share Button (Requirement 2.1) */}
      <button
        onClick={handleScreenShareToggle}
        className={`group relative p-4 rounded-full transition-all ${
          screenSharing
            ? 'bg-blue-600 hover:bg-blue-700'
            : 'bg-navy-800 hover:bg-navy-700'
        }`}
        title={screenSharing ? 'Stop sharing' : 'Share screen'}
      >
        <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        
        {/* Tooltip */}
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1 bg-navy-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
          {screenSharing ? 'Stop sharing' : 'Share screen'}
        </div>
      </button>

      {/* Reactions Button (Requirement 7.6) */}
      <div className="relative" ref={reactionsRef}>
        <button
          onClick={() => setShowReactions(!showReactions)}
          className={`group relative p-4 rounded-full transition-all ${
            showReactions
              ? 'bg-blue-600 hover:bg-blue-700'
              : 'bg-navy-800 hover:bg-navy-700'
          }`}
          title="Send reaction"
        >
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1 bg-navy-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            Reactions
          </div>
        </button>

        {/* Reactions Picker */}
        {showReactions && (
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 bg-navy-900 border border-white/10 rounded-xl shadow-2xl p-2 flex gap-1">
            {REACTIONS.map((reaction) => (
              <button
                key={reaction.emoji}
                onClick={() => handleReactionSend(reaction.emoji)}
                className="p-3 hover:bg-navy-800 rounded-lg transition-colors text-2xl"
                title={reaction.label}
              >
                {reaction.emoji}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Hand Raise Button (Requirement 7.1) */}
      <button
        onClick={handleHandRaiseToggle}
        className={`group relative p-4 rounded-full transition-all ${
          handRaised
            ? 'bg-yellow-600 hover:bg-yellow-700'
            : 'bg-navy-800 hover:bg-navy-700'
        }`}
        title={handRaised ? 'Lower hand' : 'Raise hand'}
      >
        <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11m0-5.5a1.5 1.5 0 013 0v3m0 0V11" />
        </svg>
        
        {/* Tooltip */}
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1 bg-navy-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
          {handRaised ? 'Lower hand' : 'Raise hand'}
        </div>
      </button>

      {/* Divider */}
      <div className="w-px h-10 bg-white/10"></div>

      {/* Leave Meeting Button */}
      <button
        onClick={onLeaveMeeting}
        className="group relative px-6 py-4 bg-red-600 hover:bg-red-700 rounded-full transition-all"
        title="Leave meeting"
      >
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span className="text-white font-medium">Leave</span>
        </div>
        
        {/* Tooltip */}
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1 bg-navy-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
          Leave meeting
        </div>
      </button>
    </div>
  );
}
