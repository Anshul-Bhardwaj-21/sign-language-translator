import { useRef, useEffect } from 'react';
import { Mic, MicOff, Video, VideoOff, MoreVertical, Hand, Crown } from 'lucide-react';

interface ParticipantTileProps {
  participant: {
    id: string;
    name: string;
    isLocal: boolean;
    isHost: boolean;
    videoEnabled: boolean;
    audioEnabled: boolean;
    isHandRaised: boolean;
    isSpeaking: boolean;
    stream?: MediaStream;
  };
  onMuteParticipant?: (participantId: string) => void;
  onRemoveParticipant?: (participantId: string) => void;
  onAskToSpeak?: (participantId: string) => void;
  isCurrentUserHost?: boolean;
}

export default function ParticipantTile({
  participant,
  onMuteParticipant,
  onRemoveParticipant,
  onAskToSpeak,
  isCurrentUserHost
}: ParticipantTileProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current && participant.stream && participant.videoEnabled) {
      videoRef.current.srcObject = participant.stream;
    }
  }, [participant.stream, participant.videoEnabled]);

  return (
    <div className={`relative bg-gray-900 rounded-lg overflow-hidden aspect-video ${
      participant.isSpeaking ? 'ring-4 ring-green-500' : ''
    }`}>
      {/* Video or Avatar */}
      {participant.videoEnabled && participant.stream ? (
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
          <div className="text-white text-4xl font-bold">
            {participant.name.charAt(0).toUpperCase()}
          </div>
        </div>
      )}

      {/* Overlay Info */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {/* Host Badge */}
            {participant.isHost && (
              <Crown className="w-4 h-4 text-yellow-400" />
            )}
            
            {/* Name */}
            <span className="text-white text-sm font-medium truncate">
              {participant.name} {participant.isLocal && '(You)'}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Hand Raised */}
            {participant.isHandRaised && (
              <Hand className="w-4 h-4 text-yellow-400 animate-bounce" />
            )}

            {/* Audio Status */}
            {participant.audioEnabled ? (
              <Mic className="w-4 h-4 text-white" />
            ) : (
              <MicOff className="w-4 h-4 text-red-500" />
            )}

            {/* Video Status */}
            {!participant.videoEnabled && (
              <VideoOff className="w-4 h-4 text-red-500" />
            )}
          </div>
        </div>
      </div>

      {/* Admin Controls (only visible to host for other participants) */}
      {isCurrentUserHost && !participant.isLocal && (
        <div className="absolute top-2 right-2">
          <div className="relative group">
            <button className="p-2 bg-black/50 rounded-full hover:bg-black/70 transition-colors">
              <MoreVertical className="w-4 h-4 text-white" />
            </button>

            {/* Dropdown Menu */}
            <div className="absolute right-0 mt-2 w-48 bg-gray-800 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
              <button
                onClick={() => onMuteParticipant?.(participant.id)}
                className="w-full px-4 py-2 text-left text-white hover:bg-gray-700 rounded-t-lg flex items-center gap-2"
              >
                <MicOff className="w-4 h-4" />
                Mute Participant
              </button>
              
              <button
                onClick={() => onAskToSpeak?.(participant.id)}
                className="w-full px-4 py-2 text-left text-white hover:bg-gray-700 flex items-center gap-2"
              >
                <Mic className="w-4 h-4" />
                Ask to Speak
              </button>
              
              <button
                onClick={() => onRemoveParticipant?.(participant.id)}
                className="w-full px-4 py-2 text-left text-red-400 hover:bg-gray-700 rounded-b-lg flex items-center gap-2"
              >
                <VideoOff className="w-4 h-4" />
                Remove from Call
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
