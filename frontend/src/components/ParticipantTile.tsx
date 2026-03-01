import React, { useRef, useEffect } from 'react';
import { Mic, MicOff, Hand, Video as VideoIcon, VideoOff } from 'lucide-react';
import { getInitials } from '../utils/meetingUtils';

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

interface ParticipantTileProps {
  participant: Participant;
  isAdmin?: boolean;
  onMute?: (id: string) => void;
  onRemove?: (id: string) => void;
}

const ParticipantTile: React.FC<ParticipantTileProps> = ({
  participant,
  isAdmin,
  onMute,
  onRemove,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current && participant.stream && participant.isCameraOn) {
      videoRef.current.srcObject = participant.stream;
    }
  }, [participant.stream, participant.isCameraOn]);

  return (
    <div
      className={`relative bg-gray-900 rounded-lg overflow-hidden aspect-video ${
        participant.isSpeaking ? 'ring-4 ring-blue-500' : ''
      }`}
    >
      {/* Video or Avatar */}
      {participant.isCameraOn && participant.stream ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted={participant.isLocal}
          className="w-full h-full object-cover"
          style={{ transform: participant.isLocal ? 'scaleX(-1)' : 'none' }}
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-blue-600 to-purple-600">
          <div className="text-6xl font-bold text-white">
            {getInitials(participant.name)}
          </div>
        </div>
      )}

      {/* Name Overlay */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
        <div className="flex items-center justify-between">
          <span className="text-white text-sm font-semibold truncate">
            {participant.name} {participant.isLocal && '(You)'}
          </span>
          <div className="flex items-center gap-2">
            {participant.isMuted && (
              <div className="p-1 bg-red-500 rounded-full">
                <MicOff className="w-3 h-3 text-white" />
              </div>
            )}
            {participant.isHandRaised && (
              <div className="p-1 bg-yellow-500 rounded-full animate-bounce">
                <Hand className="w-3 h-3 text-white" />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Camera Off Indicator */}
      {!participant.isCameraOn && (
        <div className="absolute top-3 right-3">
          <div className="p-2 bg-gray-800/80 rounded-full">
            <VideoOff className="w-4 h-4 text-gray-400" />
          </div>
        </div>
      )}

      {/* Admin Controls */}
      {isAdmin && !participant.isLocal && (
        <div className="absolute top-3 left-3 opacity-0 hover:opacity-100 transition-opacity">
          <div className="flex gap-2">
            <button
              onClick={() => onMute?.(participant.id)}
              className="p-2 bg-red-600 hover:bg-red-700 rounded-full text-white text-xs"
              title="Mute participant"
            >
              <MicOff className="w-3 h-3" />
            </button>
            <button
              onClick={() => onRemove?.(participant.id)}
              className="p-2 bg-gray-800 hover:bg-gray-900 rounded-full text-white text-xs"
              title="Remove participant"
            >
              ×
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ParticipantTile;
