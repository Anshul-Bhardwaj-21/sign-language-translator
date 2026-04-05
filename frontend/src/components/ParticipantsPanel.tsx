import React from 'react';
import { X, Mic, MicOff, Hand, UserX, Volume2 } from 'lucide-react';
import { getInitials } from '../utils/meetingUtils';

interface Participant {
  id: string;
  name: string;
  isMuted: boolean;
  isCameraOn: boolean;
  isHandRaised: boolean;
  isLocal?: boolean;
}

interface ParticipantsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  participants: Participant[];
  isHost: boolean;
  onMuteParticipant: (id: string) => void;
  onRemoveParticipant: (id: string) => void;
  onMuteAll: () => void;
}

const ParticipantsPanel: React.FC<ParticipantsPanelProps> = ({
  isOpen,
  onClose,
  participants,
  isHost,
  onMuteParticipant,
  onRemoveParticipant,
  onMuteAll,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 bottom-0 w-80 bg-white dark:bg-gray-800 shadow-2xl border-l border-gray-200 dark:border-gray-700 flex flex-col z-50 animate-slide-in-right">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Participants ({participants.length})
        </h3>
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        </button>
      </div>

      {/* Host Controls */}
      {isHost && (
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-yellow-50 dark:bg-yellow-900/20">
          <p className="text-xs font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
            Host Controls
          </p>
          <button
            onClick={onMuteAll}
            className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-semibold transition-colors flex items-center justify-center gap-2"
          >
            <MicOff className="w-4 h-4" />
            Mute All
          </button>
        </div>
      )}

      {/* Participants List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {participants.map((participant) => (
          <div
            key={participant.id}
            className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <div className="flex items-center gap-3 flex-1 min-w-0">
              {/* Avatar */}
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-semibold flex-shrink-0">
                {getInitials(participant.name)}
              </div>

              {/* Name and Status */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                  {participant.name} {participant.isLocal && '(You)'}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  {participant.isMuted ? (
                    <MicOff className="w-3 h-3 text-red-500" />
                  ) : (
                    <Mic className="w-3 h-3 text-green-500" />
                  )}
                  {participant.isHandRaised && (
                    <Hand className="w-3 h-3 text-yellow-500" />
                  )}
                </div>
              </div>
            </div>

            {/* Admin Controls */}
            {isHost && !participant.isLocal && (
              <div className="flex items-center gap-1">
                <button
                  onClick={() => onMuteParticipant(participant.id)}
                  className="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                  title="Mute participant"
                >
                  <MicOff className="w-4 h-4 text-red-600 dark:text-red-400" />
                </button>
                <button
                  onClick={() => onRemoveParticipant(participant.id)}
                  className="p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
                  title="Remove participant"
                >
                  <UserX className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ParticipantsPanel;
