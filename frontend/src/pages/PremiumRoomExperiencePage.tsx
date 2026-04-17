import { AnimatePresence, motion } from 'framer-motion'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Captions, ChevronDown, Grid2x2, Hand, LayoutDashboard,
  MessageSquare, Mic, MicOff, MoreHorizontal, PhoneOff, Radio,
  Settings2, Sparkles, Users, Video, VideoOff, Volume2, X,
} from 'lucide-react'
import { MediaTile } from '../components/MediaTile'
import { ReactionPicker, type ReactionOption } from '../components/meeting/ReactionPicker'
import { Modal } from '../components/Modal'
import { ToastStack } from '../components/ToastStack'
import { VisionAssistOverlay } from '../components/VisionAssistOverlay'
import { useAppContext } from '../contexts/AppContext'
import { useNetworkStatus } from '../hooks/useNetworkStatus'
import { useLocalRecording } from '../hooks/useLocalRecording'
import { useRoomSession } from '../hooks/useRoomSession'
import type { MeetingLayout, PanelView } from '../types/app'

const REACTIONS: ReactionOption[] = [
  { emoji: '👏', label: 'Applause' },
  { emoji: '🔥', label: 'Fire' },
  { emoji: '✨', label: 'Brilliant' },
  { emoji: '❤️', label: 'Love' },
  { emoji: '✋', label: 'Raise hand' },
]

type ReactionBurst = { id: string; emoji: string; participantId: string }
type ChatBubble = { id: string; participantId: string; displayName: string; message: string }

function fmt(s: number) {
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60
  return h > 0
    ? [h, m, sec].map(v => String(v).padStart(2, '0')).join(':')
    : [m, sec].map(v => String(v).padStart(2, '0')).join(':')
}

export function PremiumRoomExperiencePage() {
  const navigate = useNavigate()
  const { roomId = '' } = useParams()
  const { user, preferences, updatePreferences, rememberRoom } = useAppContext()
  const { online } = useNetworkStatus()

  const [msg, setMsg] = useState('')
  const [panel, setPanel] = useState<PanelView | null>(null)
  const [layout, setLayout] = useState<MeetingLayout>(preferences.preferredLayout)
  const [pinned, setPinned] = useState<string | null>(null)
  const [showSettings, setShowSettings] = useState(false)
  const [showShortcuts, setShowShortcuts] = useState(false)
  const [showReactions, setShowReactions] = useState(false)
  const [ctrlVisible, setCtrlVisible] = useState(true)
  const [toasts, setToasts] = useState<Array<{ id: string; message: string }>>([])
  const [secs, setSecs] = useState(0)
  const [bursts, setBursts] = useState<ReactionBurst[]>([])
  const [raised, setRaised] = useState<Record<string, boolean>>({})
  const [bubble, setBubble] = useState<ChatBubble | null>(null)
  const [docHidden, setDocHidden] = useState(document.visibilityState === 'hidden')

  const hideTimer = useRef<number | null>(null)
  const me = user ?? { id: 'anon', displayName: 'You', isGuest: true }

  const {
    room, localStream, localVideoRef, remoteStreams,
    chatMessages, captionMessages, latestPrediction,
    connectionStatus, peerStates, otherParticipants,
    loading, error, sendChat, clearCaptions, dismissError,
  } = useRoomSession({ roomId, user: me, preferences, rememberRoom })

  const { isRecording, durationMs: recMs, error: recErr, startRecording, stopRecording } =
    useLocalRecording(localStream, room ? `signbridge-${room.room_id}` : 'signbridge')

  const toast = useCallback((t: string) => {
    const id = `${Date.now()}`
    setToasts(c => [...c, { id, message: t }])
    window.setTimeout(() => setToasts(c => c.filter(x => x.id !== id)), 2800)
  }, [])

  const caption = (captionMessages.length ? captionMessages[captionMessages.length - 1].caption : '')
    || latestPrediction?.confirmed_caption || latestPrediction?.live_caption || ''

  const anyOpen = panel !== null || showSettings || showShortcuts || showReactions

  const reveal = useCallback(() => {
    if (hideTimer.current) window.clearTimeout(hideTimer.current)
    setCtrlVisible(true)
    if (!anyOpen) hideTimer.current = window.setTimeout(() => setCtrlVisible(false), 3000)
  }, [anyOpen])

  const openPanel = (p: PanelView) => { reveal(); setShowReactions(false); setPanel(c => c === p ? null : p) }

  const remoteTiles = otherParticipants.map(p => ({
    p, stream: remoteStreams[p.participant_id] ?? null,
    state: peerStates[p.participant_id] ?? 'connecting',
  }))

  const focusTile = remoteTiles.find(t => t.p.participant_id === (pinned ?? remoteTiles[0]?.p.participant_id)) ?? null
  const stripTiles = remoteTiles.filter(t => t.p.participant_id !== focusTile?.p.participant_id)
  const participants = useMemo(() =>
    room?.participants.map(p => ({ ...p, isYou: p.participant_id === me.id })) ?? [],
    [me.id, room?.participants])

  useEffect(() => { if (recErr) toast(recErr) }, [recErr, toast])
  useEffect(() => {
    if (!preferences.autoSpeakCaptions || !latestPrediction?.confirmed_caption) return
    const u = new SpeechSynthesisUtterance(latestPrediction.confirmed_caption)
    window.speechSynthesis.cancel(); window.speechSynthesis.speak(u)
  }, [latestPrediction?.confirmed_caption, preferences.autoSpeakCaptions])
  useEffect(() => {
    const base = room?.created_at ? new Date(room.created_at).getTime() : Date.now()
    const id = window.setInterval(() => setSecs(Math.max(0, Math.floor((Date.now() - base) / 1000))), 1000)
    return () => window.clearInterval(id)
  }, [room?.created_at])
  useEffect(() => {
    const h = () => setDocHidden(document.visibilityState === 'hidden')
    document.addEventListener('visibilitychange', h)
    return () => document.removeEventListener('visibilitychange', h)
  }, [])
  useEffect(() => { if (isRecording && docHidden) toast('Recording continues in background.') }, [docHidden, isRecording, toast])
  useEffect(() => {
    const last = chatMessages[chatMessages.length - 1]
    if (!last) return
    const b = { id: `${last.timestamp}-${last.participant_id}`, participantId: last.participant_id, displayName: last.display_name, message: last.message }
    setBubble(b)
    const t = window.setTimeout(() => setBubble(c => c?.id === b.id ? null : c), 3600)
    return () => window.clearTimeout(t)
  }, [chatMessages])
  useEffect(() => {
    if (anyOpen) { if (hideTimer.current) window.clearTimeout(hideTimer.current); setCtrlVisible(true); return }
    reveal()
    return () => { if (hideTimer.current) window.clearTimeout(hideTimer.current) }
  }, [anyOpen, reveal])
  useEffect(() => {
    const kd = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement
      if (t instanceof HTMLInputElement || t instanceof HTMLTextAreaElement || t.isContentEditable) return
      reveal()
      if (e.ctrlKey && e.key.toLowerCase() === 'c') { e.preventDefault(); clearCaptions(); toast('Captions cleared.'); return }
      if (e.key === 'Escape') { setPanel(null); setShowSettings(false); setShowShortcuts(false); setShowReactions(false); return }
      if ((e.shiftKey && e.key === '?') || e.key.toLowerCase() === 'h') { e.preventDefault(); setShowShortcuts(true); return }
      if (e.key.toLowerCase() === 'm') { updatePreferences({ micEnabled: !preferences.micEnabled }); return }
      if (e.key.toLowerCase() === 'v') { updatePreferences({ cameraEnabled: !preferences.cameraEnabled }); return }
      if (e.key.toLowerCase() === 'a') { const n = !preferences.accessibilityMode; updatePreferences({ accessibilityMode: n, showVisionOverlay: n }); return }
      if (e.key.toLowerCase() === 'p') { setPanel(c => c === 'participants' ? null : 'participants'); return }
      if (e.key.toLowerCase() === 't') { setPanel(c => c === 'transcript' ? null : 'transcript') }
    }
    window.addEventListener('keydown', kd)
    return () => window.removeEventListener('keydown', kd)
  }, [clearCaptions, preferences, reveal, toast, updatePreferences])

  const onReaction = (opt: ReactionOption) => {
    reveal(); setShowReactions(false)
    const id = `${opt.label}-${Date.now()}`
    setBursts(c => [...c, { id, emoji: opt.emoji, participantId: me.id }])
    window.setTimeout(() => setBursts(c => c.filter(x => x.id !== id)), 2200)
    if (opt.label === 'Raise hand') {
      setRaised(c => ({ ...c, [me.id]: true }))
      window.setTimeout(() => setRaised(c => { const n = { ...c }; delete n[me.id]; return n }), 7000)
    }
  }

  const tileExtras = (pid: string, isLocal: boolean) => {
    const tileReactions = bursts.filter(b => b.participantId === pid)
    const showBubble = panel !== 'chat' && bubble?.participantId === pid
    return (
      <>
        {isLocal && <VisionAssistOverlay overlay={latestPrediction?.overlay} visible={preferences.accessibilityMode && preferences.showVisionOverlay} mirrored />}
        <AnimatePresence>
          {showBubble && bubble && (
            <motion.div className="rm-bubble" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 6 }} transition={{ duration: 0.2 }}>
              <span className="rm-bubble__name">{bubble.displayName}</span>
              <span className="rm-bubble__msg">{bubble.message}</span>
            </motion.div>
          )}
        </AnimatePresence>
        <AnimatePresence>
          {tileReactions.map(r => (
            <motion.div key={r.id} className="rm-reaction" initial={{ opacity: 0, y: 20, scale: 0.7 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -30, scale: 0.8 }} transition={{ duration: 0.3 }}>
              {r.emoji}
            </motion.div>
          ))}
        </AnimatePresence>
        {raised[pid] && <div className="rm-hand-chip">✋ Hand raised</div>}
      </>
    )
  }

  const localTile = (compact = false) => (
    <MediaTile
      title={me.displayName}
      subtitle="You"
      stream={localStream}
      muted mirrored
      micEnabled={preferences.micEnabled}
      cameraEnabled={preferences.cameraEnabled}
      accent={compact ? 'secondary' : 'primary'}
      compact={compact}
      videoRef={localVideoRef}
      raisedHand={Boolean(raised[me.id])}
      surfaceChildren={tileExtras(me.id, true)}
    />
  )

  const remoteTile = (pid: string, name: string, _role: string, state: string, stream: MediaStream | null, mic: boolean, cam: boolean, compact = false) => (
    <MediaTile
      key={pid}
      title={name}
      subtitle={state}
      stream={stream}
      micEnabled={mic}
      cameraEnabled={cam}
      accent={compact ? 'secondary' : 'primary'}
      compact={compact}
      selected={pinned === pid}
      raisedHand={Boolean(raised[pid])}
      audioOutputId={preferences.preferredSpeakerId}
      onSelect={() => setPinned(c => c === pid ? null : pid)}
      surfaceChildren={tileExtras(pid, false)}
    />
  )

  if (!user) return null

  return (
    <main
      className={`meet${ctrlVisible ? '' : ' meet--hidden'}`}
      onPointerMove={reveal}
      onPointerDown={reveal}
    >
      <ToastStack items={toasts} />

      {/* ── Top bar ── */}
      <header className="meet-bar">
        <div className="meet-bar__left">
          <div className="meet-bar__logo">SB</div>
          <div className="meet-bar__info">
            <span className="meet-bar__name">{room?.room_name ?? roomId}</span>
            <span className="meet-bar__timer">{fmt(secs)}</span>
          </div>
        </div>
        <div className="meet-bar__center">
          {isRecording && (
            <div className="meet-rec-indicator">
              <span className="meet-rec-dot" />
              REC {fmt(Math.floor(recMs / 1000))}
            </div>
          )}
        </div>
        <div className="meet-bar__right">
          {preferences.accessibilityMode && (
            <div className="meet-bar__chip meet-bar__chip--assist">
              <Hand size={11} /> Assist
            </div>
          )}
          <div className="meet-bar__chip">
            <Users size={11} /> {room?.participants.length ?? 1}
          </div>
          <div className={`meet-bar__conn meet-bar__conn--${connectionStatus === 'connected' ? 'ok' : connectionStatus === 'error' ? 'err' : 'mid'}`}>
            <span className="meet-bar__conn-dot" />
            <span>{connectionStatus}</span>
          </div>
          {!online && <div className="meet-bar__chip meet-bar__chip--warn">Offline</div>}
        </div>
      </header>

      {/* ── Notices ── */}
      {loading && (
        <div className="meet-notice">Joining room and initializing media…</div>
      )}
      {error && (
        <div className="meet-notice meet-notice--error">
          {error}
          <button onClick={dismissError}>Dismiss</button>
        </div>
      )}

      {/* ── Video stage ── */}
      <div className="meet-stage">
        {/* Layout controls */}
        <div className="meet-layout-ctrl">
          <button
            className={`meet-layout-btn${layout === 'grid' ? ' meet-layout-btn--on' : ''}`}
            onClick={() => setLayout('grid')}
            title="Grid view"
          >
            <Grid2x2 size={13} />
          </button>
          <button
            className={`meet-layout-btn${layout === 'focus' ? ' meet-layout-btn--on' : ''}`}
            onClick={() => setLayout('focus')}
            title="Focus view"
          >
            <LayoutDashboard size={13} />
          </button>
        </div>

        {/* Grid layout */}
        {(layout === 'grid' || !focusTile) && (
          <div className={`meet-grid meet-grid--${Math.min(remoteTiles.length + 1, 4)}`}>
            {localTile()}
            {remoteTiles.length > 0
              ? remoteTiles.map(({ p, stream, state }) =>
                  remoteTile(p.participant_id, p.display_name, p.role, state, stream, p.mic_enabled, p.camera_enabled)
                )
              : (
                <div className="meet-waiting">
                  <div className="meet-waiting__icon">
                    <Users size={24} />
                  </div>
                  <p className="meet-waiting__text">Waiting for others to join</p>
                  <div className="meet-waiting__code">{room?.room_id ?? roomId}</div>
                </div>
              )
            }
          </div>
        )}

        {/* Focus layout */}
        {layout === 'focus' && focusTile && (
          <div className="meet-focus">
            <div className="meet-focus__main">
              {remoteTile(focusTile.p.participant_id, focusTile.p.display_name, focusTile.p.role, focusTile.state, focusTile.stream, focusTile.p.mic_enabled, focusTile.p.camera_enabled)}
            </div>
            <div className="meet-focus__strip">
              {localTile(true)}
              {stripTiles.map(({ p, stream, state }) =>
                remoteTile(p.participant_id, p.display_name, p.role, state, stream, p.mic_enabled, p.camera_enabled, true)
              )}
            </div>
          </div>
        )}

        {/* Live caption ribbon */}
        <AnimatePresence>
          {caption && (
            <motion.div
              className="meet-caption"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 12 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
            >
              <span className="meet-caption__badge">Live</span>
              <span className="meet-caption__text">{caption}</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── Floating toolbar ── */}
      <div className="meet-dock">
        <AnimatePresence>
          {showReactions && (
            <motion.div
              className="meet-reactions"
              initial={{ opacity: 0, y: 6, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 6, scale: 0.96 }}
              transition={{ duration: 0.16 }}
            >
              <ReactionPicker open={showReactions} options={REACTIONS} onSelect={onReaction} />
            </motion.div>
          )}
        </AnimatePresence>

        <div className="meet-toolbar">
          {/* Media group */}
          <div className="meet-toolbar__cluster">
            <button
              className={`meet-ctrl${preferences.micEnabled ? '' : ' meet-ctrl--off'}`}
              onClick={() => { updatePreferences({ micEnabled: !preferences.micEnabled }); reveal() }}
              title={`${preferences.micEnabled ? 'Mute' : 'Unmute'} (M)`}
            >
              {preferences.micEnabled ? <Mic size={19} /> : <MicOff size={19} />}
              <span>{preferences.micEnabled ? 'Mic' : 'Muted'}</span>
            </button>
            <button
              className={`meet-ctrl${preferences.cameraEnabled ? '' : ' meet-ctrl--off'}`}
              onClick={() => { updatePreferences({ cameraEnabled: !preferences.cameraEnabled }); reveal() }}
              title={`${preferences.cameraEnabled ? 'Stop' : 'Start'} camera (V)`}
            >
              {preferences.cameraEnabled ? <Video size={19} /> : <VideoOff size={19} />}
              <span>{preferences.cameraEnabled ? 'Camera' : 'Off'}</span>
            </button>
          </div>

          <div className="meet-toolbar__sep" />

          {/* Actions group */}
          <div className="meet-toolbar__cluster">
            <button
              className={`meet-ctrl${isRecording ? ' meet-ctrl--active' : ''}`}
              onClick={() => isRecording ? stopRecording() : startRecording()}
              title="Record"
            >
              <Radio size={19} />
              <span>{isRecording ? 'Stop rec' : 'Record'}</span>
            </button>
            <button
              className={`meet-ctrl${showReactions ? ' meet-ctrl--active' : ''}`}
              onClick={() => { reveal(); setShowReactions(c => !c) }}
              title="Reactions"
            >
              <Sparkles size={19} />
              <span>React</span>
            </button>
            <button
              className={`meet-ctrl${preferences.accessibilityMode ? ' meet-ctrl--assist' : ''}`}
              onClick={() => { reveal(); const n = !preferences.accessibilityMode; updatePreferences({ accessibilityMode: n, showVisionOverlay: n }) }}
              title="Accessibility mode (A)"
            >
              <Hand size={19} />
              <span>Assist</span>
            </button>
          </div>

          <div className="meet-toolbar__sep" />

          {/* Panels group */}
          <div className="meet-toolbar__cluster">
            <button
              className={`meet-ctrl${panel === 'chat' ? ' meet-ctrl--active' : ''}`}
              onClick={() => openPanel('chat')}
              title="Chat"
            >
              <MessageSquare size={19} />
              <span>Chat</span>
            </button>
            <button
              className={`meet-ctrl${panel === 'participants' ? ' meet-ctrl--active' : ''}`}
              onClick={() => openPanel('participants')}
              title="People (P)"
            >
              <Users size={19} />
              <span>People</span>
            </button>
            <button
              className={`meet-ctrl${panel === 'transcript' ? ' meet-ctrl--active' : ''}`}
              onClick={() => openPanel('transcript')}
              title="Captions (T)"
            >
              <Captions size={19} />
              <span>Captions</span>
            </button>
            <button
              className={`meet-ctrl${panel === 'translation' ? ' meet-ctrl--active' : ''}`}
              onClick={() => openPanel('translation')}
              title="AI Assist"
            >
              <Volume2 size={19} />
              <span>AI</span>
            </button>
            <button
              className="meet-ctrl"
              onClick={() => { reveal(); setShowSettings(true) }}
              title="Settings"
            >
              <Settings2 size={19} />
              <span>Settings</span>
            </button>
            <button
              className="meet-ctrl"
              onClick={() => { reveal(); setShowShortcuts(true) }}
              title="Shortcuts (H)"
            >
              <MoreHorizontal size={19} />
              <span>More</span>
            </button>
          </div>

          <div className="meet-toolbar__sep" />

          {/* Leave */}
          <button
            className="meet-leave"
            onClick={() => navigate('/dashboard')}
            title="Leave meeting"
          >
            <PhoneOff size={18} />
            <span>Leave</span>
          </button>
        </div>
      </div>

      {/* ── Side panel drawer ── */}
      <AnimatePresence>
        {panel && (
          <>
            <motion.div
              className="meet-overlay"
              onClick={() => setPanel(null)}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
            />
            <motion.aside
              className="meet-panel"
              initial={{ x: '100%', opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: '100%', opacity: 0 }}
              transition={{ duration: 0.26, ease: [0.25, 0, 0.1, 1] }}
            >
              {/* Panel header */}
              <div className="meet-panel-hdr">
                <span className="meet-panel-hdr__title">
                  {panel === 'chat' && 'Chat'}
                  {panel === 'participants' && 'People'}
                  {panel === 'transcript' && 'Captions'}
                  {panel === 'translation' && 'AI Assist'}
                </span>
                <button className="meet-panel-close" onClick={() => setPanel(null)}>
                  <X size={15} />
                </button>
              </div>

              {/* Chat */}
              {panel === 'chat' && (
                <div className="meet-panel-chat">
                  <div className="meet-chat-feed">
                    {chatMessages.length === 0 && (
                      <div className="meet-panel-empty">
                        <MessageSquare size={20} />
                        <p>No messages yet</p>
                      </div>
                    )}
                    {chatMessages.map(m => (
                      <div key={`${m.timestamp}-${m.participant_id}`} className="meet-chat-entry">
                        <div className="meet-chat-entry__avatar">{m.display_name[0].toUpperCase()}</div>
                        <div className="meet-chat-entry__body">
                          <div className="meet-chat-entry__header">
                            <span className="meet-chat-entry__name">{m.display_name}</span>
                            <span className="meet-chat-entry__time">{new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                          </div>
                          <p className="meet-chat-entry__text">{m.message}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                  <form
                    className="meet-chat-compose"
                    onSubmit={e => { e.preventDefault(); if (msg.trim()) { sendChat(msg); setMsg('') } }}
                  >
                    <input
                      className="meet-chat-input"
                      value={msg}
                      onChange={e => setMsg(e.target.value)}
                      placeholder="Type a message…"
                    />
                    <button type="submit" className="meet-chat-send" disabled={!msg.trim()}>
                      <ChevronDown size={14} style={{ transform: 'rotate(-90deg)' }} />
                    </button>
                  </form>
                </div>
              )}

              {/* People */}
              {panel === 'participants' && (
                <div className="meet-panel-body">
                  {participants.length === 0 && (
                    <div className="meet-panel-empty"><Users size={20} /><p>No participants</p></div>
                  )}
                  <div className="meet-people-list">
                    {participants.map(p => (
                      <div key={p.participant_id} className="meet-person">
                        <div className="meet-person__av">{p.display_name[0].toUpperCase()}</div>
                        <div className="meet-person__info">
                          <span className="meet-person__name">{p.isYou ? `${p.display_name} (You)` : p.display_name}</span>
                          <span className="meet-person__role">{p.role}</span>
                        </div>
                        <div className="meet-person__media">
                          {p.mic_enabled ? <Mic size={13} className="meet-person__icon meet-person__icon--ok" /> : <MicOff size={13} className="meet-person__icon meet-person__icon--off" />}
                          {p.camera_enabled ? <Video size={13} className="meet-person__icon meet-person__icon--ok" /> : <VideoOff size={13} className="meet-person__icon meet-person__icon--off" />}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Captions */}
              {panel === 'transcript' && (
                <div className="meet-panel-body">
                  <div className="meet-panel-actions">
                    <button className="meet-panel-action" onClick={() => { clearCaptions(); toast('Captions cleared.') }}>Clear all</button>
                  </div>
                  {captionMessages.length === 0 && (
                    <div className="meet-panel-empty"><Captions size={20} /><p>No captions yet</p></div>
                  )}
                  <div className="meet-caption-feed">
                    {captionMessages.map(c => (
                      <div key={`${c.timestamp}-${c.participant_id}`} className="meet-caption-item">
                        <span className="meet-caption-item__who">{c.display_name}</span>
                        <p className="meet-caption-item__text">{c.caption}</p>
                        <span className="meet-caption-item__conf">{Math.round(parseFloat(c.confidence) * 100)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Assist */}
              {panel === 'translation' && (
                <div className="meet-panel-body">
                  <div className="meet-assist">
                    <div className="meet-assist__state">
                      <span className={`meet-assist__dot ${latestPrediction?.engine_ready ? 'meet-assist__dot--on' : 'meet-assist__dot--off'}`} />
                      <span className="meet-assist__engine">
                        {latestPrediction?.engine ?? 'heuristic'} · {latestPrediction?.fallback_used ? 'fallback mode' : 'primary mode'}
                      </span>
                    </div>
                    <div className="meet-assist__sign">
                      <div className="meet-assist__sign-label">Detected sign</div>
                      <div className="meet-assist__sign-value">{latestPrediction?.label ?? '—'}</div>
                      <div className="meet-assist__sign-conf">
                        {latestPrediction ? `${Math.round(latestPrediction.confidence * 100)}% confidence` : 'No prediction yet'}
                      </div>
                    </div>
                    {latestPrediction?.live_caption && (
                      <div className="meet-assist__caption">
                        <span className="meet-assist__caption-label">Caption</span>
                        <p>{latestPrediction.live_caption}</p>
                      </div>
                    )}
                    <div className="meet-assist__actions">
                      <button
                        className="meet-assist-btn"
                        onClick={() => {
                          if (caption) {
                            const u = new SpeechSynthesisUtterance(caption)
                            window.speechSynthesis.cancel()
                            window.speechSynthesis.speak(u)
                          }
                        }}
                      >
                        <Volume2 size={14} /> Speak
                      </button>
                      <button
                        className="meet-assist-btn meet-assist-btn--ghost"
                        onClick={() => { clearCaptions(); toast('Captions cleared.') }}
                      >
                        Clear
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* ── Settings modal ── */}
      {showSettings && (
        <Modal title="Settings" eyebrow="Preferences" onClose={() => setShowSettings(false)}>
          <div className="meet-settings">
            {([
              { label: 'Auto-speak captions', sub: 'Read captions aloud automatically', key: 'autoSpeakCaptions' as const },
              { label: 'Accessibility mode', sub: 'Sign language detection + vision overlay', key: 'accessibilityMode' as const },
              { label: 'Vision overlay', sub: 'Hand landmarks on local tile', key: 'showVisionOverlay' as const },
              { label: 'Live captions', sub: 'Publish AI captions to all participants', key: 'translationEnabled' as const },
            ]).map(({ label, sub, key }) => (
              <div key={key} className="meet-setting-row">
                <div>
                  <div className="meet-setting-row__label">{label}</div>
                  <div className="meet-setting-row__sub">{sub}</div>
                </div>
                <button
                  role="switch"
                  aria-checked={preferences[key] as boolean}
                  className={`lobby-toggle ${(preferences[key] as boolean) ? 'lobby-toggle--on' : ''}`}
                  onClick={() => updatePreferences({ [key]: !preferences[key] })}
                >
                  <span className="lobby-toggle__thumb" />
                </button>
              </div>
            ))}
          </div>
        </Modal>
      )}

      {/* ── Shortcuts modal ── */}
      {showShortcuts && (
        <Modal title="Keyboard shortcuts" eyebrow="Quick reference" onClose={() => setShowShortcuts(false)}>
          <div className="meet-shortcuts">
            {[
              ['M', 'Mute / unmute microphone'],
              ['V', 'Camera on / off'],
              ['A', 'Toggle Accessibility mode'],
              ['Ctrl + C', 'Clear all captions'],
              ['P', 'Open People panel'],
              ['T', 'Open Captions panel'],
              ['H', 'Open this help'],
              ['Esc', 'Close any open panel'],
            ].map(([k, v]) => (
              <div key={k} className="meet-shortcut">
                <kbd>{k}</kbd>
                <span>{v}</span>
              </div>
            ))}
          </div>
        </Modal>
      )}
    </main>
  )
}

