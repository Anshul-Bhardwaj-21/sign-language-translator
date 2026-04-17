import { Wifi, WifiOff, Users, Clock, Shield } from 'lucide-react'
import type { RoomSnapshot, ConnectionStatus } from '../../types/app'
import { GlassPanel } from './GlassPanel'
import { getConnectionTone } from '../../utils/meeting'

interface InfoOverlayProps {
  open: boolean
  room: RoomSnapshot | null
  connectionStatus: ConnectionStatus
  networkOnline: boolean
  effectiveNetworkType: string
  onClose: () => void
}

const TONE_COLORS: Record<string, string> = {
  good: 'rgba(34,197,94,0.85)',
  warn: 'rgba(234,179,8,0.85)',
  danger: 'rgba(239,68,68,0.85)',
}

export function InfoOverlay({
  open,
  room,
  connectionStatus,
  networkOnline,
  effectiveNetworkType,
  onClose,
}: InfoOverlayProps) {
  const tone = getConnectionTone(connectionStatus)
  const toneColor = TONE_COLORS[tone]

  return (
    <GlassPanel open={open} title="Room Info" onClose={onClose} fullscreenOnMobile>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

        {/* Network quality */}
        <section>
          <h3 style={sectionHeadingStyle}>Network</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
            <InfoRow
              icon={networkOnline ? <Wifi size={13} color={toneColor} /> : <WifiOff size={13} color={TONE_COLORS.danger} />}
              label="Status"
              value={connectionStatus}
              valueColor={toneColor}
            />
            <InfoRow
              icon={<Wifi size={13} color="rgba(255,255,255,0.4)" />}
              label="Type"
              value={effectiveNetworkType || 'unknown'}
            />
          </div>
        </section>

        {/* Room metadata */}
        {room && (
          <section>
            <h3 style={sectionHeadingStyle}>Room</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
              <InfoRow
                icon={<Users size={13} color="rgba(255,255,255,0.4)" />}
                label="Name"
                value={room.room_name}
              />
              <InfoRow
                icon={<Users size={13} color="rgba(255,255,255,0.4)" />}
                label="Capacity"
                value={`${room.participants.length} / ${room.max_participants}`}
              />
              <InfoRow
                icon={<Clock size={13} color="rgba(255,255,255,0.4)" />}
                label="Created"
                value={new Date(room.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              />
              {room.accessibility_mode && (
                <InfoRow
                  icon={<Shield size={13} color="rgba(99,102,241,0.85)" />}
                  label="Accessibility"
                  value="Enabled"
                  valueColor="rgba(99,102,241,0.85)"
                />
              )}
            </div>
          </section>
        )}

        {/* Participant list */}
        {room && room.participants.length > 0 && (
          <section>
            <h3 style={sectionHeadingStyle}>Participants ({room.participants.length})</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              {room.participants.map((p) => (
                <div
                  key={p.participant_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.375rem 0.5rem',
                    borderRadius: 6,
                    background: 'rgba(255,255,255,0.04)',
                  }}
                >
                  <div
                    style={{
                      width: 24,
                      height: 24,
                      borderRadius: '50%',
                      background: 'rgba(99,102,241,0.35)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.6875rem',
                      fontWeight: 700,
                      color: '#fff',
                      flexShrink: 0,
                    }}
                  >
                    {p.display_name.charAt(0).toUpperCase()}
                  </div>
                  <span style={{ flex: 1, fontSize: '0.8125rem', color: 'rgba(255,255,255,0.8)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {p.display_name}
                  </span>
                  <span style={{ fontSize: '0.6875rem', color: 'rgba(255,255,255,0.35)', textTransform: 'capitalize' }}>
                    {p.role}
                  </span>
                  <div
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background: p.connected ? 'rgba(34,197,94,0.8)' : 'rgba(239,68,68,0.8)',
                      flexShrink: 0,
                    }}
                    aria-label={p.connected ? 'connected' : 'disconnected'}
                  />
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </GlassPanel>
  )
}

function InfoRow({
  icon,
  label,
  value,
  valueColor,
}: {
  icon: React.ReactNode
  label: string
  value: string
  valueColor?: string
}) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      {icon}
      <span style={{ fontSize: '0.8125rem', color: 'rgba(255,255,255,0.45)', flex: 1 }}>{label}</span>
      <span style={{ fontSize: '0.8125rem', color: valueColor ?? 'rgba(255,255,255,0.8)', fontWeight: 500 }}>
        {value}
      </span>
    </div>
  )
}

const sectionHeadingStyle: React.CSSProperties = {
  margin: '0 0 0.5rem',
  fontSize: '0.75rem',
  fontWeight: 600,
  color: 'rgba(255,255,255,0.45)',
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
}
