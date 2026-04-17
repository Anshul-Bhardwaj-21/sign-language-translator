import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { AlertCircle, ArrowRight, Check, Copy, Mic, MicOff, RefreshCcw, Video, VideoOff } from 'lucide-react'
import { AudioLevelMeter } from '../components/AudioLevelMeter'
import { MediaTile } from '../components/MediaTile'
import { useAppContext } from '../contexts/AppContext'
import { useMediaSetup } from '../hooks/useMediaSetup'
import { useNetworkStatus } from '../hooks/useNetworkStatus'
import { api } from '../services/api'
import type { HealthSnapshot, RoomSnapshot } from '../types/app'

function ToggleSwitch({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      className={`lobby-toggle ${on ? 'lobby-toggle--on' : ''}`}
    >
      <span className="lobby-toggle__thumb" />
    </button>
  )
}

export function LobbyPage() {
  const navigate = useNavigate()
  const { roomId } = useParams()
  const [searchParams] = useSearchParams()
  const { user, preferences, updatePreferences, rememberRoom } = useAppContext()
  const { online } = useNetworkStatus()

  const [camOn, setCamOn] = useState(preferences.cameraEnabled)
  const [micOn, setMicOn] = useState(preferences.micEnabled)
  const [captions, setCaptions] = useState(preferences.translationEnabled)
  const [a11y, setA11y] = useState(preferences.accessibilityMode)
  const [health, setHealth] = useState<HealthSnapshot | null>(null)
  const [room, setRoom] = useState<RoomSnapshot | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const autoRef = useRef(false)

  const {
    previewStream, audioLevel, cameraPermission, micPermission,
    cameraError, micError, isPreparing, videoInputs, audioInputs, audioOutputs,
    selectedCameraId, selectedMicId, selectedSpeakerId,
    setSelectedCameraId, setSelectedMicId, setSelectedSpeakerId,
    refreshDevices, restartPreview, stopPreview, supportsSinkSelection,
  } = useMediaSetup({
    cameraEnabled: camOn, micEnabled: micOn,
    preferredCameraId: preferences.preferredCameraId,
    preferredMicId: preferences.preferredMicId,
    preferredSpeakerId: preferences.preferredSpeakerId,
  })

  useEffect(() => { void api.getHealth().then(setHealth).catch(() => undefined) }, [])

  useEffect(() => {
    if (!user) return
    const autoCreate = searchParams.get('create') === 'true'
    if (!roomId && autoCreate && !autoRef.current) {
      autoRef.current = true
      setBusy(true)
      void api.createRoom({ displayName: user.displayName, participantId: user.id, roomName: `${user.displayName}'s room`, accessibilityMode: a11y, maxParticipants: 6 })
        .then(r => navigate(`/lobby/${r.room_id}`, { replace: true }))
        .catch(e => setErr(e instanceof Error ? e.message : 'Failed.'))
        .finally(() => setBusy(false))
      return
    }
    if (!roomId) { setRoom(null); return }
    setBusy(true)
    void api.getRoom(roomId).then(setRoom).catch(e => setErr(e instanceof Error ? e.message : 'Room not found.')).finally(() => setBusy(false))
  }, [a11y, navigate, roomId, searchParams, user])

  if (!user) return null

  const handleCreate = async () => {
    setBusy(true); setErr(null)
    try {
      const r = await api.createRoom({ displayName: user.displayName, participantId: user.id, roomName: `${user.displayName}'s room`, accessibilityMode: a11y, maxParticipants: 6 })
      navigate(`/lobby/${r.room_id}`)
    } catch (e) { setErr(e instanceof Error ? e.message : 'Failed.') }
    finally { setBusy(false) }
  }

  const handleJoin = () => {
    if (!room) return
    updatePreferences({ cameraEnabled: camOn, micEnabled: micOn, translationEnabled: captions, accessibilityMode: a11y, showVisionOverlay: a11y, preferredCameraId: selectedCameraId, preferredMicId: selectedMicId, preferredSpeakerId: selectedSpeakerId })
    rememberRoom({ roomId: room.room_id, roomName: room.room_name, lastJoinedAt: new Date().toISOString() })
    stopPreview()
    navigate(`/room/${room.room_id}`)
  }

  const copyCode = async () => {
    if (!room) return
    try { await navigator.clipboard.writeText(room.room_id); setCopied(true); setTimeout(() => setCopied(false), 2000) }
    catch { setErr('Copy failed.') }
  }

  const micStatus = micPermission === 'granted' ? 'ok' : micPermission === 'denied' ? 'denied' : 'pending'
  const camStatus = cameraPermission === 'granted' ? 'ok' : cameraPermission === 'denied' ? 'denied' : 'pending'

  return (
    <div className="lobby">
      {/* Header bar */}
      <header className="lobby__bar">
        <div className="lobby__bar-info">
          <span className="lobby__bar-title">{room ? room.room_name : 'New meeting'}</span>
          {room && (
            <button className="lobby__code-pill" onClick={copyCode} title="Copy room code">
              {room.room_id}
              {copied ? <Check size={11} /> : <Copy size={11} />}
            </button>
          )}
        </div>
        <div className="lobby__bar-indicators">
          <span className={`lobby__dot lobby__dot--${online ? 'green' : 'red'}`} title={online ? 'Online' : 'Offline'} />
          <span className={`lobby__dot lobby__dot--${health?.engine_ready ? 'green' : 'amber'}`} title={health?.engine_ready ? 'AI engine ready' : 'AI engine offline'} />
        </div>
      </header>

      {err && (
        <div className="lobby__error">
          <AlertCircle size={14} />
          {err}
        </div>
      )}

      <div className="lobby__body">
        {/* Left — camera preview */}
        <div className="lobby__left">
          <div className="lobby__preview">
            <MediaTile
              title={user.displayName}
              subtitle={isPreparing ? 'Initializing camera…' : room ? `Joining ${room.room_name}` : 'Your preview'}
              stream={previewStream}
              muted
              mirrored
              micEnabled={micOn}
              cameraEnabled={camOn}
              audioLevel={audioLevel}
            />
          </div>

          {/* Camera / mic controls */}
          <div className="lobby__media-row">
            <button className={`lobby__media-btn ${micOn ? '' : 'lobby__media-btn--off'}`} onClick={() => setMicOn(v => !v)} title={micOn ? 'Mute mic' : 'Unmute mic'}>
              {micOn ? <Mic size={17} /> : <MicOff size={17} />}
              <span>{micOn ? 'Mic on' : 'Mic off'}</span>
            </button>
            <button className={`lobby__media-btn ${camOn ? '' : 'lobby__media-btn--off'}`} onClick={() => setCamOn(v => !v)} title={camOn ? 'Stop camera' : 'Start camera'}>
              {camOn ? <Video size={17} /> : <VideoOff size={17} />}
              <span>{camOn ? 'Camera on' : 'Camera off'}</span>
            </button>
            <button className="lobby__media-btn lobby__media-btn--ghost" onClick={() => void restartPreview()} title="Retry devices">
              <RefreshCcw size={15} />
            </button>
          </div>

          {/* Mic level + status */}
          <div className="lobby__diagnostics">
            <div className="lobby__diag-row">
              <span className="lobby__diag-label">Microphone</span>
              <div className="lobby__diag-right">
                <span className={`lobby__perm lobby__perm--${micStatus}`}>{micPermission}</span>
                <AudioLevelMeter level={audioLevel} active={micOn} />
              </div>
            </div>
            <div className="lobby__diag-row">
              <span className="lobby__diag-label">Camera</span>
              <span className={`lobby__perm lobby__perm--${camStatus}`}>{cameraPermission}</span>
            </div>
            {(cameraError || micError) && (
              <div className="lobby__device-error">
                <AlertCircle size={12} />
                {cameraError || micError}
              </div>
            )}
          </div>
        </div>

        {/* Right — settings + join */}
        <div className="lobby__right">
          <div className="lobby__section">
            <div className="lobby__section-label">Devices</div>
            <div className="lobby__devices">
              <div className="lobby__device-row">
                <label>Camera</label>
                <select value={selectedCameraId} onChange={e => setSelectedCameraId(e.target.value)}>
                  {videoInputs.map(d => <option key={d.deviceId} value={d.deviceId}>{d.label || 'Camera'}</option>)}
                </select>
              </div>
              <div className="lobby__device-row">
                <label>Microphone</label>
                <select value={selectedMicId} onChange={e => setSelectedMicId(e.target.value)}>
                  {audioInputs.map(d => <option key={d.deviceId} value={d.deviceId}>{d.label || 'Microphone'}</option>)}
                </select>
              </div>
              <div className="lobby__device-row">
                <label>Speaker</label>
                <select value={selectedSpeakerId} onChange={e => setSelectedSpeakerId(e.target.value)} disabled={!supportsSinkSelection}>
                  {audioOutputs.map(d => <option key={d.deviceId} value={d.deviceId}>{d.label || 'Speaker'}</option>)}
                </select>
              </div>
              <button className="lobby__refresh-btn" onClick={() => void refreshDevices()}>
                <RefreshCcw size={11} /> Refresh
              </button>
            </div>
          </div>

          <div className="lobby__section">
            <div className="lobby__section-label">Options</div>
            <div className="lobby__options">
              <div className="lobby__option-row">
                <div>
                  <div className="lobby__option-title">Live captions</div>
                  <div className="lobby__option-hint">Publish AI captions to all</div>
                </div>
                <ToggleSwitch on={captions} onChange={setCaptions} />
              </div>
              <div className="lobby__option-row">
                <div>
                  <div className="lobby__option-title">Accessibility mode</div>
                  <div className="lobby__option-hint">Sign language detection</div>
                </div>
                <ToggleSwitch on={a11y} onChange={setA11y} />
              </div>
            </div>
          </div>

          <div className="lobby__cta-area">
            {room ? (
              <button className="lobby__join-btn" disabled={busy} onClick={handleJoin}>
                Join meeting
                <ArrowRight size={17} />
              </button>
            ) : (
              <button className="lobby__join-btn" disabled={busy} onClick={() => void handleCreate()}>
                {busy ? 'Creating room…' : 'Create & join'}
                <ArrowRight size={17} />
              </button>
            )}
            <p className="lobby__cta-note">
              {room ? `${room.participants?.length ?? 1} participant${(room.participants?.length ?? 1) !== 1 ? 's' : ''} in room` : 'You will be the host'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
