import type { MeetingVideoGridProps } from '../../types/app'
import { MediaTile } from '../MediaTile'
import { VisionAssistOverlay } from '../VisionAssistOverlay'

function WaitingStatePlaceholder() {
  return (
    <div className="meeting-video-grid__waiting">
      <p>Waiting for others to join…</p>
    </div>
  )
}

export function MeetingVideoGrid({
  layout,
  localTile,
  remoteTiles,
  pinnedParticipantId,
  presenceDepthMap,
  onPinParticipant,
  onUnpinParticipant,
}: MeetingVideoGridProps) {
  const {
    stream: localStream,
    videoRef,
    micEnabled,
    cameraEnabled,
    accessibilityMode,
    showVisionOverlay,
    latestPrediction,
    raisedHand: localRaisedHand,
  } = localTile

  const showVisionAssist = accessibilityMode && showVisionOverlay && latestPrediction !== null

  const localMediaTile = (
    <MediaTile
      key="local"
      title="You"
      stream={localStream}
      muted
      mirrored
      micEnabled={micEnabled}
      cameraEnabled={cameraEnabled}
      videoRef={videoRef}
      raisedHand={localRaisedHand}
      presenceDepth={presenceDepthMap['local']}
      surfaceChildren={
        showVisionAssist ? (
          <VisionAssistOverlay
            overlay={latestPrediction?.overlay}
            visible
            mirrored
          />
        ) : undefined
      }
    />
  )

  if (remoteTiles.length === 0) {
    return (
      <div className="meeting-video-grid meeting-video-grid--waiting">
        <div className="meeting-video-grid__local-solo">{localMediaTile}</div>
        <WaitingStatePlaceholder />
      </div>
    )
  }

  if (layout === 'focus') {
    // Determine spotlight tile
    let spotlightRemote = pinnedParticipantId
      ? remoteTiles.find((t) => t.participantId === pinnedParticipantId) ?? remoteTiles[0]
      : remoteTiles[0]

    const stripRemotes = remoteTiles.filter((t) => t.participantId !== spotlightRemote.participantId)

    return (
      <div className="meeting-video-grid meeting-video-grid--focus">
        {/* Spotlight */}
        <div className="meeting-video-grid__spotlight">
          <MediaTile
            key={spotlightRemote.participantId}
            title={spotlightRemote.displayName}
            subtitle={spotlightRemote.role}
            stream={spotlightRemote.stream}
            micEnabled={spotlightRemote.micEnabled}
            cameraEnabled={spotlightRemote.cameraEnabled}
            raisedHand={spotlightRemote.raisedHand}
            audioOutputId={spotlightRemote.audioOutputId}
            presenceDepth={presenceDepthMap[spotlightRemote.participantId]}
            selected={pinnedParticipantId === spotlightRemote.participantId}
            onSelect={() => {
              if (pinnedParticipantId === spotlightRemote.participantId) {
                onUnpinParticipant()
              } else {
                onPinParticipant(spotlightRemote.participantId)
              }
            }}
          />
        </div>

        {/* Strip */}
        <div className="meeting-video-grid__strip">
          {stripRemotes.map((tile) => (
            <MediaTile
              key={tile.participantId}
              title={tile.displayName}
              subtitle={tile.role}
              stream={tile.stream}
              micEnabled={tile.micEnabled}
              cameraEnabled={tile.cameraEnabled}
              raisedHand={tile.raisedHand}
              audioOutputId={tile.audioOutputId}
              presenceDepth={presenceDepthMap[tile.participantId]}
              compact
              selected={pinnedParticipantId === tile.participantId}
              onSelect={() => {
                if (pinnedParticipantId === tile.participantId) {
                  onUnpinParticipant()
                } else {
                  onPinParticipant(tile.participantId)
                }
              }}
            />
          ))}
          <div className="meeting-video-grid__strip-local">{localMediaTile}</div>
        </div>
      </div>
    )
  }

  // Grid layout — all tiles equal size
  return (
    <div className="meeting-video-grid meeting-video-grid--grid">
      {remoteTiles.map((tile) => (
        <MediaTile
          key={tile.participantId}
          title={tile.displayName}
          subtitle={tile.role}
          stream={tile.stream}
          micEnabled={tile.micEnabled}
          cameraEnabled={tile.cameraEnabled}
          raisedHand={tile.raisedHand}
          audioOutputId={tile.audioOutputId}
          presenceDepth={presenceDepthMap[tile.participantId]}
          selected={pinnedParticipantId === tile.participantId}
          onSelect={() => {
            if (pinnedParticipantId === tile.participantId) {
              onUnpinParticipant()
            } else {
              onPinParticipant(tile.participantId)
            }
          }}
        />
      ))}
      {localMediaTile}
    </div>
  )
}
