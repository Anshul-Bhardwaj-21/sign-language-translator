import type { ConnectionStatus } from '../../types/app'
import { formatDuration, getConnectionTone } from '../../utils/meeting'
import { StatusPill } from '../StatusPill'

export interface MeetingTopBarProps {
  roomName: string
  roomId: string
  participantCount: number
  meetingSeconds: number
  connectionStatus: ConnectionStatus
  isRecording: boolean
  recordingDurationMs: number
  networkOnline: boolean
  effectiveNetworkType: string
}

export function MeetingTopBar({
  roomName,
  roomId,
  participantCount,
  meetingSeconds,
  connectionStatus,
  isRecording,
  recordingDurationMs,
  networkOnline,
  effectiveNetworkType,
}: MeetingTopBarProps) {
  const displayName = roomName || roomId
  const connectionTone = getConnectionTone(connectionStatus)
  const connectionLabel =
    connectionStatus === 'connected'
      ? 'Connected'
      : connectionStatus === 'connecting'
        ? 'Connecting…'
        : connectionStatus === 'reconnecting'
          ? 'Reconnecting…'
          : connectionStatus === 'disconnected'
            ? 'Disconnected'
            : 'Error'

  const networkLabel = networkOnline
    ? effectiveNetworkType
      ? effectiveNetworkType.toUpperCase()
      : 'Online'
    : 'Offline'

  return (
    <header
      className="meeting-top-bar"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        padding: '0.5rem 1rem',
        background: 'var(--bg-elevated)',
        borderBottom: '1px solid var(--panel-border)',
        color: 'var(--text-primary)',
        flexWrap: 'wrap',
      }}
    >
      {/* Room name */}
      <span
        style={{
          fontWeight: 600,
          fontSize: '0.9375rem',
          color: 'var(--text-primary)',
          marginRight: '0.25rem',
          flexShrink: 0,
        }}
        title={roomId}
      >
        {displayName}
      </span>

      {/* Participant count */}
      <span
        style={{
          fontSize: '0.8125rem',
          color: 'var(--text-muted)',
          flexShrink: 0,
        }}
        aria-label={`${participantCount} participant${participantCount !== 1 ? 's' : ''}`}
      >
        {participantCount} {participantCount === 1 ? 'participant' : 'participants'}
      </span>

      {/* Elapsed timer */}
      <span
        style={{
          fontVariantNumeric: 'tabular-nums',
          fontSize: '0.8125rem',
          color: 'var(--text-secondary)',
          flexShrink: 0,
        }}
        aria-label={`Meeting duration: ${formatDuration(meetingSeconds)}`}
      >
        {formatDuration(meetingSeconds)}
      </span>

      {/* Spacer */}
      <span style={{ flex: 1 }} />

      {/* Recording chip */}
      {isRecording && (
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.375rem',
            padding: '0.1875rem 0.625rem',
            borderRadius: '9999px',
            background: 'rgba(255, 127, 102, 0.18)',
            border: '1px solid rgba(255, 127, 102, 0.4)',
            color: 'var(--danger)',
            fontSize: '0.75rem',
            fontWeight: 600,
            flexShrink: 0,
          }}
          aria-label={`Recording: ${formatDuration(Math.floor(recordingDurationMs / 1000))}`}
        >
          <span
            style={{
              width: '0.5rem',
              height: '0.5rem',
              borderRadius: '50%',
              background: 'var(--danger)',
              display: 'inline-block',
            }}
            aria-hidden="true"
          />
          REC {formatDuration(Math.floor(recordingDurationMs / 1000))}
        </span>
      )}

      {/* Connection status pill */}
      <StatusPill label={connectionLabel} tone={connectionTone} />

      {/* Network pill */}
      <StatusPill
        label={networkLabel}
        tone={networkOnline ? 'good' : 'danger'}
      />
    </header>
  )
}
