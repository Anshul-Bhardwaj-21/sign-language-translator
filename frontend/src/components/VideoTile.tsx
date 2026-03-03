import { useEffect, useRef } from 'react';
import { Participant } from '../contexts/MeetingContext';

/**
 * VideoTile Component
 * 
 * Displays individual participant video stream with status indicators.
 * 
 * Requirements:
 * - 1.3: Display video with adaptive quality
 * - 1.5: Prioritize active speaker with highest quality
 * - 22.1: Display participant name and status indicators
 * - 22.2: Highlight active speaker within 300ms
 * 
 * Features:
 * - Display participant video stream
 * - Show participant name overlay
 * - Display audio/video status indicators
 * - Show active speaker highlighting
 * - Show pinned participant indicator
 * - Display reactions and hand raise indicators
 */

interface VideoTileProps {
  participant: Participant;
  stream: MediaStream | null;
  isActiveSpeaker?: boolean;
  isPinned?: boolean;
  isLocal?: boolean;
  className?: string;
  onPin?: (participantId: string) => void;
}

export default function VideoTile({
  participant,
  stream,
  isActiveSpeaker = false,
  isPinned = false,
  isLocal = false,
  className = '',
  onPin,
}: VideoTileProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  
  // Attach stream to video element
  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);
  
  // Get border color based on state (Requirement 22.2)
  const getBorderColor = () => {
    if (isActiveSpeaker) {
      return 'border-blue-500 shadow-lg shadow-blue-500/50';
    }
    if (isPinned) {
      return 'border-purple-500 shadow-lg shadow-purple-500/50';
    }
    return 'border-white/10';
  };
  
  // Get border width based on state
  const getBorderWidth = () => {
    if (isActiveSpeaker || isPinned) {
      return 'border-4';
    }
    return 'border';
  };
  
  return (
    <div
      className={`relative bg-navy-900 rounded-xl overflow-hidden ${getBorderWidth()} ${getBorderColor()} transition-all duration-300 ${className}`}
    >
      {/* Video Element */}
      {participant.videoEnabled && stream ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted={isLocal}
          className="w-full h-full object-cover"
        />
      ) : (
        // Placeholder when video is disabled
        <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-navy-800 to-navy-900">
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-2 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
              <span className="text-white text-2xl font-bold">
                {participant.name.charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="text-white text-sm font-medium">
              {participant.name}
            </div>
          </div>
        </div>
      )}
      
      {/* Active Speaker Indicator (Requirement 22.2) */}
      {isActiveSpeaker && (
        <div className="absolute top-2 left-2 px-2 py-1 bg-blue-500 text-white text-xs font-medium rounded-md flex items-center gap-1 animate-pulse">
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path d="M7 4a3 3 0 016 0v6a3 3 0 11-6 0V4z" />
          </svg>
          Speaking
        </div>
      )}
      
      {/* Pinned Indicator */}
      {isPinned && (
        <div className="absolute top-2 left-2 px-2 py-1 bg-purple-500 text-white text-xs font-medium rounded-md flex items-center gap-1">
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L11 4.323V3a1 1 0 011-1zm-5 8.274l-.818 2.552c-.25.78.409 1.574 1.195 1.574H6.5a1 1 0 01.894.553l.448.894a1 1 0 001.788 0l.448-.894A1 1 0 0111 13.4h1.123c.786 0 1.445-.794 1.195-1.574L12.5 10.274V3.5a1.5 1.5 0 00-3 0v6.774z" />
          </svg>
          Pinned
        </div>
      )}
      
      {/* Hand Raised Indicator */}
      {participant.handRaised && (
        <div className="absolute top-2 right-2 px-2 py-1 bg-yellow-500 text-white text-xs font-medium rounded-md flex items-center gap-1">
          ✋ Hand Raised
        </div>
      )}
      
      {/* Bottom Overlay with Name and Status (Requirement 22.1) */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/50 to-transparent p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <span className="text-white text-sm font-medium truncate">
              {participant.name}
              {isLocal && ' (You)'}
            </span>
            
            {/* Host Badge */}
            {participant.isHost && (
              <span className="px-1.5 py-0.5 bg-blue-500/80 text-white text-xs font-medium rounded">
                Host
              </span>
            )}
            
            {/* Co-Host Badge */}
            {participant.isCoHost && (
              <span className="px-1.5 py-0.5 bg-purple-500/80 text-white text-xs font-medium rounded">
                Co-Host
              </span>
            )}
          </div>
          
          {/* Audio/Video Status Indicators (Requirement 22.1) */}
          <div className="flex items-center gap-1.5">
            {/* Audio Status */}
            {participant.audioEnabled ? (
              participant.isSpeaking ? (
                <div className="p-1.5 bg-blue-500 rounded-full">
                  <svg className="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M7 4a3 3 0 016 0v6a3 3 0 11-6 0V4z" />
                    <path d="M5.5 9.643a.75.75 0 00-1.5 0V10c0 3.06 2.29 5.585 5.25 5.954V17.5h-1.5a.75.75 0 000 1.5h4.5a.75.75 0 000-1.5h-1.5v-1.546A6.001 6.001 0 0016 10v-.357a.75.75 0 00-1.5 0V10a4.5 4.5 0 01-9 0v-.357z" />
                  </svg>
                </div>
              ) : (
                <div className="p-1.5 bg-white/20 rounded-full">
                  <svg className="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M7 4a3 3 0 016 0v6a3 3 0 11-6 0V4z" />
                    <path d="M5.5 9.643a.75.75 0 00-1.5 0V10c0 3.06 2.29 5.585 5.25 5.954V17.5h-1.5a.75.75 0 000 1.5h4.5a.75.75 0 000-1.5h-1.5v-1.546A6.001 6.001 0 0016 10v-.357a.75.75 0 00-1.5 0V10a4.5 4.5 0 01-9 0v-.357z" />
                  </svg>
                </div>
              )
            ) : (
              <div className="p-1.5 bg-red-500 rounded-full">
                <svg className="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3.28 2.22a.75.75 0 00-1.06 1.06l14.5 14.5a.75.75 0 101.06-1.06l-1.5-1.5A6.01 6.01 0 0016 10v-.357a.75.75 0 00-1.5 0V10a4.5 4.5 0 01-.83 2.6l-1.2-1.2A3 3 0 0013 10V4a3 3 0 00-4.93-2.32L6.85 3.9A4.5 4.5 0 017 4v.357a.75.75 0 001.5 0V4a3 3 0 00-3-3c-.36 0-.71.06-1.03.18L3.28 2.22z" />
                </svg>
              </div>
            )}
            
            {/* Video Status */}
            {!participant.videoEnabled && (
              <div className="p-1.5 bg-red-500 rounded-full">
                <svg className="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3.28 2.22a.75.75 0 00-1.06 1.06l14.5 14.5a.75.75 0 101.06-1.06l-1.5-1.5A6.01 6.01 0 0016 10v-.357a.75.75 0 00-1.5 0V10a4.5 4.5 0 01-.83 2.6l-1.2-1.2A3 3 0 0013 10V4a3 3 0 00-4.93-2.32L6.85 3.9A4.5 4.5 0 017 4v.357a.75.75 0 001.5 0V4a3 3 0 00-3-3c-.36 0-.71.06-1.03.18L3.28 2.22z" />
                </svg>
              </div>
            )}
            
            {/* Pin Button */}
            {onPin && (
              <button
                onClick={() => onPin(participant.id)}
                className={`p-1.5 rounded-full transition-colors ${
                  isPinned
                    ? 'bg-purple-500 hover:bg-purple-600'
                    : 'bg-white/20 hover:bg-white/30'
                }`}
                title={isPinned ? 'Unpin' : 'Pin participant'}
              >
                <svg className="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L11 4.323V3a1 1 0 011-1zm-5 8.274l-.818 2.552c-.25.78.409 1.574 1.195 1.574H6.5a1 1 0 01.894.553l.448.894a1 1 0 001.788 0l.448-.894A1 1 0 0111 13.4h1.123c.786 0 1.445-.794 1.195-1.574L12.5 10.274V3.5a1.5 1.5 0 00-3 0v6.774z" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
      
      {/* Sign Language Indicator */}
      {participant.isSigning && (
        <div className="absolute top-2 left-2 px-2 py-1 bg-green-500 text-white text-xs font-medium rounded-md flex items-center gap-1">
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L11 4.323V3a1 1 0 011-1z" />
          </svg>
          Signing
        </div>
      )}
    </div>
  );
}
