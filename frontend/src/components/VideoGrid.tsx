import { useMemo } from 'react';
import { Participant, LayoutType } from '../contexts/MeetingContext';
import VideoTile from './VideoTile';

/**
 * VideoGrid Component
 * 
 * Renders participant video streams in responsive grid layout.
 * 
 * Requirements:
 * - 1.3: Adapt video quality based on grid size
 * - 1.5: Prioritize active speaker with highest quality
 * - 22.1: Display all participants in grid
 * - 22.2: Highlight active speaker within 300ms
 * - 22.3: Enlarge active speaker's video in layout
 * - 22.4: Provide grid view layout option
 * - 22.5: Provide spotlight view layout option
 * - 22.6: Provide sidebar view layout option
 * - 22.7: Support manual pinning of participant video
 * 
 * Features:
 * - Responsive grid layout that adapts to participant count
 * - Active speaker detection and highlighting
 * - Video quality adaptation based on tile size
 * - Multiple layout modes (grid, spotlight, sidebar)
 * - Manual participant pinning
 */

interface VideoGridProps {
  participants: Participant[];
  localStream: MediaStream | null;
  remoteStreams: Map<string, MediaStream>;
  currentUserId: string;
  layout: LayoutType;
  activeSpeaker: string | null;
  pinnedParticipant: string | null;
  screenSharingParticipant: string | null;
  onPinParticipant: (participantId: string | null) => void;
}

export default function VideoGrid({
  participants,
  localStream,
  remoteStreams,
  currentUserId,
  layout,
  activeSpeaker,
  pinnedParticipant,
  screenSharingParticipant,
  onPinParticipant,
}: VideoGridProps) {
  
  /**
   * Calculate grid layout based on participant count (Requirement 1.3)
   * Returns CSS grid template columns for responsive layout
   */
  const getGridLayout = (count: number): string => {
    if (count === 1) return 'grid-cols-1';
    if (count === 2) return 'grid-cols-2';
    if (count <= 4) return 'grid-cols-2';
    if (count <= 6) return 'grid-cols-3';
    if (count <= 9) return 'grid-cols-3';
    if (count <= 12) return 'grid-cols-4';
    if (count <= 16) return 'grid-cols-4';
    return 'grid-cols-5';
  };
  
  /**
   * Get stream for a participant
   */
  const getStreamForParticipant = (participantId: string): MediaStream | null => {
    if (participantId === currentUserId) {
      return localStream;
    }
    return remoteStreams.get(participantId) || null;
  };
  
  /**
   * Handle pin/unpin participant (Requirement 22.7)
   */
  const handlePinToggle = (participantId: string) => {
    if (pinnedParticipant === participantId) {
      onPinParticipant(null);
    } else {
      onPinParticipant(participantId);
    }
  };
  
  /**
   * Sort participants for display
   * Priority: Pinned > Active Speaker > Host > Others
   */
  const sortedParticipants = useMemo(() => {
    return [...participants].sort((a, b) => {
      // Pinned participant first
      if (a.id === pinnedParticipant) return -1;
      if (b.id === pinnedParticipant) return 1;
      
      // Active speaker second
      if (a.id === activeSpeaker) return -1;
      if (b.id === activeSpeaker) return 1;
      
      // Host third
      if (a.isHost && !b.isHost) return -1;
      if (!a.isHost && b.isHost) return 1;
      
      // Co-host fourth
      if (a.isCoHost && !b.isCoHost) return -1;
      if (!a.isCoHost && b.isCoHost) return 1;
      
      // Sort by join time
      return a.joinedAt.getTime() - b.joinedAt.getTime();
    });
  }, [participants, pinnedParticipant, activeSpeaker]);
  
  /**
   * Grid View Layout (Requirement 22.4)
   * All participants displayed equally in responsive grid
   */
  const renderGridLayout = () => {
    const gridCols = getGridLayout(participants.length);
    
    return (
      <div className={`grid ${gridCols} gap-4 w-full h-full auto-rows-fr`}>
        {sortedParticipants.map((participant) => (
          <VideoTile
            key={participant.id}
            participant={participant}
            stream={getStreamForParticipant(participant.id)}
            isActiveSpeaker={participant.id === activeSpeaker}
            isPinned={participant.id === pinnedParticipant}
            isLocal={participant.id === currentUserId}
            onPin={handlePinToggle}
            className="min-h-0"
          />
        ))}
      </div>
    );
  };
  
  /**
   * Spotlight View Layout (Requirement 22.5)
   * Active speaker or pinned participant displayed large, others hidden or minimized
   * Screen sharing takes priority when active (Requirement 2.4)
   */
  const renderSpotlightLayout = () => {
    // Determine who to spotlight (screen sharing > pinned > active speaker)
    const spotlightParticipantId = screenSharingParticipant || pinnedParticipant || activeSpeaker || participants[0]?.id;
    const spotlightParticipant = participants.find(p => p.id === spotlightParticipantId);
    
    if (!spotlightParticipant) {
      return (
        <div className="flex items-center justify-center w-full h-full">
          <div className="text-gray-400 text-lg">No participants to display</div>
        </div>
      );
    }
    
    // Other participants (excluding spotlight)
    const otherParticipants = participants.filter(p => p.id !== spotlightParticipantId);
    
    return (
      <div className="flex flex-col w-full h-full gap-4">
        {/* Main spotlight video (Requirement 22.3, 2.4) */}
        <div className="flex-1 min-h-0">
          {screenSharingParticipant === spotlightParticipant.id && (
            <div className="absolute top-4 left-4 z-10 px-3 py-1 bg-blue-500/90 backdrop-blur-sm rounded-lg">
              <span className="text-white text-sm font-medium">Screen Sharing</span>
            </div>
          )}
          <VideoTile
            participant={spotlightParticipant}
            stream={getStreamForParticipant(spotlightParticipant.id)}
            isActiveSpeaker={spotlightParticipant.id === activeSpeaker}
            isPinned={spotlightParticipant.id === pinnedParticipant}
            isLocal={spotlightParticipant.id === currentUserId}
            onPin={handlePinToggle}
            className="w-full h-full"
          />
        </div>
        
        {/* Thumbnails of other participants */}
        {otherParticipants.length > 0 && (
          <div className="flex gap-2 overflow-x-auto pb-2">
            {otherParticipants.slice(0, 8).map((participant) => (
              <div key={participant.id} className="flex-shrink-0 w-32 h-24">
                <VideoTile
                  participant={participant}
                  stream={getStreamForParticipant(participant.id)}
                  isActiveSpeaker={participant.id === activeSpeaker}
                  isPinned={participant.id === pinnedParticipant}
                  isLocal={participant.id === currentUserId}
                  onPin={handlePinToggle}
                  className="w-full h-full cursor-pointer hover:ring-2 hover:ring-blue-500"
                />
              </div>
            ))}
            {otherParticipants.length > 8 && (
              <div className="flex-shrink-0 w-32 h-24 bg-navy-800 rounded-xl flex items-center justify-center">
                <span className="text-gray-400 text-sm">
                  +{otherParticipants.length - 8} more
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };
  
  /**
   * Sidebar View Layout (Requirement 22.6)
   * Active speaker large on left, others in sidebar on right
   * Screen sharing takes priority when active (Requirement 2.4)
   */
  const renderSidebarLayout = () => {
    // Determine main participant (screen sharing > pinned > active speaker)
    const mainParticipantId = screenSharingParticipant || pinnedParticipant || activeSpeaker || participants[0]?.id;
    const mainParticipant = participants.find(p => p.id === mainParticipantId);
    
    if (!mainParticipant) {
      return (
        <div className="flex items-center justify-center w-full h-full">
          <div className="text-gray-400 text-lg">No participants to display</div>
        </div>
      );
    }
    
    // Other participants (excluding main)
    const sidebarParticipants = participants.filter(p => p.id !== mainParticipantId);
    
    return (
      <div className="flex w-full h-full gap-4">
        {/* Main video (Requirement 22.3, 2.4) */}
        <div className="flex-1 min-w-0 relative">
          {screenSharingParticipant === mainParticipant.id && (
            <div className="absolute top-4 left-4 z-10 px-3 py-1 bg-blue-500/90 backdrop-blur-sm rounded-lg">
              <span className="text-white text-sm font-medium">Screen Sharing</span>
            </div>
          )}
          <VideoTile
            participant={mainParticipant}
            stream={getStreamForParticipant(mainParticipant.id)}
            isActiveSpeaker={mainParticipant.id === activeSpeaker}
            isPinned={mainParticipant.id === pinnedParticipant}
            isLocal={mainParticipant.id === currentUserId}
            onPin={handlePinToggle}
            className="w-full h-full"
          />
        </div>
        
        {/* Sidebar with other participants */}
        {sidebarParticipants.length > 0 && (
          <div className="w-64 flex flex-col gap-3 overflow-y-auto">
            {sidebarParticipants.map((participant) => (
              <div key={participant.id} className="aspect-video">
                <VideoTile
                  participant={participant}
                  stream={getStreamForParticipant(participant.id)}
                  isActiveSpeaker={participant.id === activeSpeaker}
                  isPinned={participant.id === pinnedParticipant}
                  isLocal={participant.id === currentUserId}
                  onPin={handlePinToggle}
                  className="w-full h-full cursor-pointer hover:ring-2 hover:ring-blue-500"
                />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };
  
  /**
   * Accessibility Layout
   * Optimized for deaf/hard-of-hearing users with large signer video
   */
  const renderAccessibilityLayout = () => {
    // Prioritize active signer, then pinned, then active speaker
    const mainParticipantId = pinnedParticipant || activeSpeaker || participants[0]?.id;
    const mainParticipant = participants.find(p => p.id === mainParticipantId);
    
    if (!mainParticipant) {
      return (
        <div className="flex items-center justify-center w-full h-full">
          <div className="text-gray-400 text-lg">No participants to display</div>
        </div>
      );
    }
    
    // Other participants
    const otherParticipants = participants.filter(p => p.id !== mainParticipantId);
    
    return (
      <div className="flex flex-col w-full h-full gap-4">
        {/* Large main video for sign language visibility */}
        <div className="flex-1 min-h-0 flex items-center justify-center">
          <div className="w-full max-w-4xl h-full">
            <VideoTile
              participant={mainParticipant}
              stream={getStreamForParticipant(mainParticipant.id)}
              isActiveSpeaker={mainParticipant.id === activeSpeaker}
              isPinned={mainParticipant.id === pinnedParticipant}
              isLocal={mainParticipant.id === currentUserId}
              onPin={handlePinToggle}
              className="w-full h-full"
            />
          </div>
        </div>
        
        {/* Compact thumbnails of other participants */}
        {otherParticipants.length > 0 && (
          <div className="flex gap-2 justify-center overflow-x-auto pb-2">
            {otherParticipants.slice(0, 6).map((participant) => (
              <div key={participant.id} className="flex-shrink-0 w-32 h-24">
                <VideoTile
                  participant={participant}
                  stream={getStreamForParticipant(participant.id)}
                  isActiveSpeaker={participant.id === activeSpeaker}
                  isPinned={participant.id === pinnedParticipant}
                  isLocal={participant.id === currentUserId}
                  onPin={handlePinToggle}
                  className="w-full h-full cursor-pointer hover:ring-2 hover:ring-purple-500"
                />
              </div>
            ))}
            {otherParticipants.length > 6 && (
              <div className="flex-shrink-0 w-32 h-24 bg-navy-800 rounded-xl flex items-center justify-center">
                <span className="text-gray-400 text-sm">
                  +{otherParticipants.length - 6} more
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };
  
  // Empty state
  if (participants.length === 0) {
    return (
      <div className="flex items-center justify-center w-full h-full">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-navy-800 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <div className="text-gray-400 text-lg">Waiting for participants...</div>
          <div className="text-gray-500 text-sm mt-2">
            Share the meeting link to invite others
          </div>
        </div>
      </div>
    );
  }
  
  // Render appropriate layout based on layout type
  return (
    <div className="w-full h-full p-4">
      {layout === 'grid' && renderGridLayout()}
      {layout === 'spotlight' && renderSpotlightLayout()}
      {layout === 'sidebar' && renderSidebarLayout()}
      {layout === 'accessibility' && renderAccessibilityLayout()}
    </div>
  );
}
