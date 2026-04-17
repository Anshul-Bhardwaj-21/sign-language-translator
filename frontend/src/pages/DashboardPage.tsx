import { FormEvent, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Clock, Hash, Plus, Wifi, WifiOff } from 'lucide-react'
import { useAppContext } from '../contexts/AppContext'
import { api } from '../services/api'
import type { HealthSnapshot } from '../types/app'

export function DashboardPage() {
  const navigate = useNavigate()
  const { user, preferences, recentRooms, rememberRoom } = useAppContext()
  const [health, setHealth] = useState<HealthSnapshot | null>(null)
  const [code, setCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => { void api.getHealth().then(setHealth).catch(() => undefined) }, [])

  if (!user) return null

  const handleCreate = async () => {
    setBusy(true); setError(null)
    try {
      const room = await api.createRoom({
        displayName: user.displayName,
        participantId: user.id,
        roomName: `${user.displayName}'s room`,
        accessibilityMode: preferences.accessibilityMode,
        maxParticipants: 6,
      })
      rememberRoom({ roomId: room.room_id, roomName: room.room_name, lastJoinedAt: new Date().toISOString() })
      navigate(`/lobby/${room.room_id}`)
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed to create room.') }
    finally { setBusy(false) }
  }

  const handleJoin = (e: FormEvent) => {
    e.preventDefault()
    if (code.trim()) navigate(`/lobby/${code.trim().toUpperCase()}`)
  }

  const engineOk = health?.engine_ready ?? false

  return (
    <div className="dash">
      {/* Header */}
      <div className="dash__header">
        <div className="dash__header-left">
          <h1 className="dash__title">Hi, {user.displayName}</h1>
          <p className="dash__sub">What would you like to do today?</p>
        </div>
        <div className="dash__status-badge">
          {engineOk ? <Wifi size={13} /> : <WifiOff size={13} />}
          <span>{engineOk ? 'AI ready' : 'AI offline'}</span>
        </div>
      </div>

      {error && <div className="dash__error">{error}</div>}

      {/* Main actions */}
      <div className="dash__grid">
        <div className="dash__card dash__card--accent" onClick={busy ? undefined : handleCreate} role="button" tabIndex={0} onKeyDown={e => e.key === 'Enter' && !busy && void handleCreate()}>
          <div className="dash__card-icon"><Plus size={20} /></div>
          <div className="dash__card-title">New meeting</div>
          <div className="dash__card-hint">Start instantly · invite by code</div>
          <button className="dash__card-btn" disabled={busy} onClick={e => { e.stopPropagation(); void handleCreate() }}>
            {busy ? 'Creating…' : 'Create'}
            <ArrowRight size={14} />
          </button>
        </div>

        <div className="dash__card">
          <div className="dash__card-icon"><Hash size={20} /></div>
          <div className="dash__card-title">Join a room</div>
          <div className="dash__card-hint">Enter a 6-character room code</div>
          <form className="dash__join" onSubmit={handleJoin}>
            <input
              className="dash__join-input"
              value={code}
              onChange={e => setCode(e.target.value.toUpperCase())}
              placeholder="ABC123"
              maxLength={8}
              spellCheck={false}
            />
            <button type="submit" className="dash__join-btn" disabled={!code.trim()}>
              <ArrowRight size={15} />
            </button>
          </form>
        </div>
      </div>

      {/* Recent */}
      {recentRooms.length > 0 && (
        <div className="dash__recent">
          <div className="dash__recent-title">
            <Clock size={12} />
            Recent rooms
          </div>
          <div className="dash__recent-list">
            {recentRooms.slice(0, 5).map(r => (
              <button key={r.roomId} className="dash__recent-item" onClick={() => navigate(`/lobby/${r.roomId}`)}>
                <span className="dash__recent-name">{r.roomName}</span>
                <span className="dash__recent-code">{r.roomId}</span>
                <ArrowRight size={12} className="dash__recent-arrow" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
