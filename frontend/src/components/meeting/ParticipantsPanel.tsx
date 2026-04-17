import { Mic, MicOff, Video, VideoOff, Wifi, WifiOff } from 'lucide-react'
import type { ParticipantSnapshot } from '../../types/app'
import { GlassPanel } from './GlassPanel'

interface ParticipantsPanelProps {
  open: boolean
  participants: ParticipantSnapshot[]
  peerStates: Record<string, string>
  attentionParticipants: Record<string, { isInactive: boolean }>
  onClose: () => void
}

export function ParticipantsPanel({
  open,
  participants,
  peerStates,
  attentionParticipants,
  onClose,
}: ParticipantsPanelProps) {
  return (
    <GlassPanel open={open} title={`Participants (${participants.length})`} onClose={onClose} fullscreenOnMobile>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
        {participants.length === 0 ? (
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.875rem', textAlign: 'center', marginTop: '2rem' }}>
            No participants
          </p>
        ) : (
          participants.map((p) => {
            const isInactive = attentionParticipants[p.participant_id]?.isInactive ?? false
            const peerState = peerStates[p.participant_id] ?? 'unknown'

            return (
              <div
                key={p.participant_id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.625rem',
                  padding: '0.5rem 0.625rem',
                  borderRadius: 8,
                  background: isInactive ? 'rgba(255,255,255,0.03)' : 'rgba(255,255,255,0.06)',
                  opacity: isInactive ? 0.55 : 1,
                  transition: 'opacity 300ms ease',
                }}
                aria-label={`${p.display_name}${isInactive ? ', inactive' : ''}`}
              >
                {/* Avatar placeholder */}
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    background: 'rgba(99,102,241,0.4)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.8125rem',
                    fontWeight: 700,
                    color: '#fff',
                    flexShrink: 0,
                  }}
                >
                  {p.display_name.charAt(0).toUpperCase()}
                </div>

                {/* Name + role */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      color: 'rgba(255,255,255,0.9)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {p.display_name}
                  </div>
                  <div style={{ fontSize: '0.6875rem', color: 'rgba(255,255,255,0.4)', textTransform: 'capitalize' }}>
                    {p.role}
                  </div>
                </div>

                {/* State icons */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', flexShrink: 0 }}>
                  {p.mic_enabled ? (
                    <Mic size={13} color="rgba(255,255,255,0.6)" />
                  ) : (
                    <MicOff size={13} color="rgba(239,68,68,0.8)" />
                  )}
                  {p.camera_enabled ? (
                    <Video size={13} color="rgba(255,255,255,0.6)" />
                  ) : (
                    <VideoOff size={13} color="rgba(239,68,68,0.8)" />
                  )}
                  {p.connected ? (
                    <Wifi size={13} color="rgba(34,197,94,0.8)" />
                  ) : (
                    <WifiOff size={13} color="rgba(239,68,68,0.8)" />
                  )}
                </div>

                {/* Peer state badge */}
                {peerState !== 'unknown' && (
                  <span
                    style={{
                      fontSize: '0.625rem',
                      padding: '0.125rem 0.375rem',
                      borderRadius: 4,
                      background: 'rgba(255,255,255,0.08)',
                      color: 'rgba(255,255,255,0.5)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      flexShrink: 0,
                    }}
                  >
                    {peerState}
                  </span>
                )}
              </div>
            )
          })
        )}
      </div>
    </GlassPanel>
  )
}
