import { useState, useEffect, useRef, useCallback } from 'react'
import type {
  AppUser,
  UserPreferences,
  RecentRoom,
  MeetingShellState,
  PanelView,
  ReactionBurst,
  SilenceDetectionConfig,
} from '../types/app'
import { useRoomSession } from './useRoomSession'
import { useLocalRecording } from './useLocalRecording'
import { useAudioLevel } from './useAudioLevel'
import { useActiveSpeaker } from './useActiveSpeaker'
import { usePresenceDepth } from './usePresenceDepth'
import { useSmartLayout } from './useSmartLayout'
import { useSilenceDetection } from './useSilenceDetection'
import { useContextualUI } from './useContextualUI'
import { useAIMeetingMemory } from './useAIMeetingMemory'
import { useAttentionIntelligence } from './useAttentionIntelligence'

export interface UseMeetingShellArgs {
  roomId: string
  user: AppUser
  preferences: UserPreferences
  updatePreferences: (updates: Partial<UserPreferences>) => void
  rememberRoom: (room: RecentRoom) => void
  navigate: (path: string) => void
}

export interface Toast {
  id: string
  message: string
}

const DEFAULT_SILENCE_CONFIG: SilenceDetectionConfig = {
  thresholdSeconds: 30,
  audioThreshold: 0.05,
}

export function useMeetingShell({
  roomId,
  user,
  preferences,
  updatePreferences,
  rememberRoom,
  navigate,
}: UseMeetingShellArgs) {
  // Session start timestamp (stable ref)
  const sessionStartMsRef = useRef<number>(Date.now())
  const sessionStartMs = sessionStartMsRef.current

  // ── Room session ──────────────────────────────────────────────────────────
  const roomSession = useRoomSession({ roomId, user, preferences, rememberRoom })
  const {
    room,
    localStream,
    localVideoRef,
    remoteStreams,
    chatMessages,
    captionMessages,
    latestPrediction,
    connectionStatus,
    peerStates,
    otherParticipants,
    loading,
    error,
    sendChat,
    clearCaptions,
    dismissError,
    sendRealtime,
  } = roomSession

  // ── Local recording ───────────────────────────────────────────────────────
  const recording = useLocalRecording(localStream)
  const { isRecording, durationMs: recordingDurationMs, startRecording, stopRecording } = recording

  // ── Audio levels ──────────────────────────────────────────────────────────
  const localAudioLevel = useAudioLevel(localStream, preferences.micEnabled)

  // Remote audio levels: use a ref-based map updated via useEffect
  const [remoteAudioLevels, setRemoteAudioLevels] = useState<Record<string, number>>({})
  const remoteAudioContextsRef = useRef<Map<string, { ctx: AudioContext; cancel: () => void }>>(new Map())

  useEffect(() => {
    const currentIds = new Set(Object.keys(remoteStreams))

    // Clean up contexts for streams that are gone
    for (const [id, entry] of remoteAudioContextsRef.current.entries()) {
      if (!currentIds.has(id)) {
        entry.cancel()
        void entry.ctx.close().catch(() => undefined)
        remoteAudioContextsRef.current.delete(id)
        setRemoteAudioLevels((prev) => {
          const next = { ...prev }
          delete next[id]
          return next
        })
      }
    }

    // Create contexts for new streams
    for (const [id, stream] of Object.entries(remoteStreams)) {
      if (remoteAudioContextsRef.current.has(id)) continue

      const audioTracks = stream.getAudioTracks()
      if (audioTracks.length === 0) {
        setRemoteAudioLevels((prev) => ({ ...prev, [id]: 0 }))
        continue
      }

      try {
        const ctx = new AudioContext()
        const source = ctx.createMediaStreamSource(new MediaStream([audioTracks[0]]))
        const analyser = ctx.createAnalyser()
        analyser.fftSize = 256
        source.connect(analyser)

        const buffer = new Uint8Array(analyser.frequencyBinCount)
        let frameId = 0
        let cancelled = false

        const sample = () => {
          if (cancelled) return
          analyser.getByteTimeDomainData(buffer)
          let sum = 0
          for (let i = 0; i < buffer.length; i++) {
            const n = (buffer[i] - 128) / 128
            sum += n * n
          }
          const rms = Math.sqrt(sum / buffer.length)
          const level = Math.min(1, rms * 3.4)
          setRemoteAudioLevels((prev) => ({ ...prev, [id]: level }))
          frameId = window.requestAnimationFrame(sample)
        }

        frameId = window.requestAnimationFrame(sample)

        remoteAudioContextsRef.current.set(id, {
          ctx,
          cancel: () => {
            cancelled = true
            window.cancelAnimationFrame(frameId)
            source.disconnect()
            analyser.disconnect()
          },
        })
      } catch {
        // AudioContext creation failed — degrade gracefully
        setRemoteAudioLevels((prev) => ({ ...prev, [id]: 0 }))
      }
    }
  }, [remoteStreams])

  // Cleanup all audio contexts on unmount
  useEffect(() => {
    return () => {
      for (const entry of remoteAudioContextsRef.current.values()) {
        entry.cancel()
        void entry.ctx.close().catch(() => undefined)
      }
      remoteAudioContextsRef.current.clear()
    }
  }, [])

  // Aggregate audioLevelMap: local + remote
  const audioLevelMap: Record<string, number> = {
    ...remoteAudioLevels,
    [user.id]: localAudioLevel,
  }

  // ── Subsystem hooks ───────────────────────────────────────────────────────
  const { activeSpeakerId } = useActiveSpeaker({ audioLevelMap })

  const reducedMotion =
    typeof window !== 'undefined'
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false

  const { presenceDepthMap } = usePresenceDepth({ audioLevelMap, activeSpeakerId, reducedMotion })

  // Broadcast is_speaking when local participant becomes active speaker
  useEffect(() => {
    if (activeSpeakerId === user.id) {
      sendRealtime('status.update', { is_speaking: true })
    }
  }, [activeSpeakerId, user.id, sendRealtime])

  // Derive screenShareParticipantId from participants (field may not exist yet)
  const screenShareParticipantId =
    room?.participants.find(
      (p) => (p as ParticipantSnapshotWithScreenShare).screen_sharing === true,
    )?.participant_id ?? null

  const [shellState, setShellState] = useState<MeetingShellState>({
    activePanel: null,
    showSettingsModal: false,
    showShortcutsModal: false,
    showInfoPanel: false,
    showReactionPicker: false,
    controlsVisible: true,
    pinnedParticipantId: null,
    raisedHandIds: {},
    reactionBursts: [],
    chatPreview: null,
    meetingSeconds: 0,
    documentHidden: false,
  })

  const reactionBurstCount = shellState.reactionBursts.length

  const { layout, spotlightId, mode, lockLayout, unlockLayout } = useSmartLayout({
    activeSpeakerId,
    screenShareParticipantId,
    reactionBurstCount,
    manualPinnedId: shellState.pinnedParticipantId,
    participantCount: room?.participants.length ?? 1,
  })

  const { silenceState, resetSilence } = useSilenceDetection({
    audioLevelMap,
    config: DEFAULT_SILENCE_CONFIG,
  })

  const handRaiseActive = Object.values(shellState.raisedHandIds).some(Boolean)

  const { toolbarConfig, captionBreathingRoom } = useContextualUI({
    handRaiseActive,
    captionsActive: captionMessages.length > 0,
    accessibilityMode: preferences.accessibilityMode,
    screenShareActive: screenShareParticipantId !== null,
    silenceActive: silenceState.isSilent,
    isRecording,
    activePanel: shellState.activePanel,
    preferences,
  })

  const { recordHighlight, searchHighlights, generateSummary, highlights, summary, syncHighlights } =
    useAIMeetingMemory({ sessionStartMs, roomId })

  const { attentionState, dismissSilenceNudge } = useAttentionIntelligence({
    participants: room?.participants ?? [],
    localParticipantId: user.id,
    audioLevelMap,
  })

  // ── Toasts ────────────────────────────────────────────────────────────────
  const [toasts, setToasts] = useState<Toast[]>([])

  const pushToast = useCallback((message: string) => {
    const id = `toast-${Date.now()}-${Math.random()}`
    setToasts((prev) => [...prev, { id, message }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4000)
  }, [])

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  // ── Meeting timer ─────────────────────────────────────────────────────────
  useEffect(() => {
    const id = setInterval(() => {
      setShellState((prev) => ({ ...prev, meetingSeconds: prev.meetingSeconds + 1 }))
    }, 1000)
    return () => clearInterval(id)
  }, [])

  // ── Document visibility ───────────────────────────────────────────────────
  useEffect(() => {
    const handler = () => {
      setShellState((prev) => ({ ...prev, documentHidden: document.hidden }))
    }
    document.addEventListener('visibilitychange', handler)
    return () => document.removeEventListener('visibilitychange', handler)
  }, [])

  // ── Auto-hide controls timer ──────────────────────────────────────────────
  const autoHideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const revealControls = useCallback(() => {
    setShellState((prev) => ({ ...prev, controlsVisible: true }))
    if (autoHideTimerRef.current) clearTimeout(autoHideTimerRef.current)
    autoHideTimerRef.current = setTimeout(() => {
      setShellState((prev) => {
        // Keep visible if any panel/modal/picker is open
        if (
          prev.activePanel !== null ||
          prev.showSettingsModal ||
          prev.showShortcutsModal ||
          prev.showInfoPanel ||
          prev.showReactionPicker
        ) {
          return prev
        }
        return { ...prev, controlsVisible: false }
      })
    }, 2600)
  }, [])

  useEffect(() => {
    return () => {
      if (autoHideTimerRef.current) clearTimeout(autoHideTimerRef.current)
    }
  }, [])

  // ── Recording error toast ─────────────────────────────────────────────────
  useEffect(() => {
    if (recording.error) {
      pushToast(recording.error)
    }
  }, [recording.error, pushToast])

  // ── Handlers ──────────────────────────────────────────────────────────────
  const togglePanel = useCallback((panel: PanelView) => {
    setShellState((prev) => ({
      ...prev,
      activePanel: prev.activePanel === panel ? null : panel,
    }))
  }, [])

  const handleReactionSelect = useCallback(
    (emoji: string) => {
      const burst: ReactionBurst = {
        id: `reaction-${Date.now()}-${Math.random()}`,
        emoji,
        participantId: user.id,
      }

      // Record hand raise highlight
      if (emoji === '✋' || emoji === '🖐️') {
        recordHighlight({
          type: 'handRaise',
          participantId: user.id,
          participantName: user.displayName,
          label: `Hand raised by ${user.displayName}`,
        })
        setShellState((prev) => ({
          ...prev,
          raisedHandIds: { ...prev.raisedHandIds, [user.id]: true },
          reactionBursts: [...prev.reactionBursts, burst],
        }))
      } else {
        setShellState((prev) => ({
          ...prev,
          reactionBursts: [...prev.reactionBursts, burst],
        }))
      }

      // Record reaction burst highlight when burst count reaches threshold
      setShellState((prev) => {
        if (prev.reactionBursts.length >= 2) {
          recordHighlight({
            type: 'reactionBurst',
            participantId: user.id,
            participantName: user.displayName,
            label: `Reaction burst: ${emoji}`,
          })
        }
        return prev
      })

      // Auto-clear burst after animation duration
      setTimeout(() => {
        setShellState((prev) => ({
          ...prev,
          reactionBursts: prev.reactionBursts.filter((b) => b.id !== burst.id),
        }))
      }, 2200)
    },
    [user.id, user.displayName, recordHighlight],
  )

  const handleRecordingToggle = useCallback(() => {
    if (isRecording) {
      stopRecording()
    } else {
      const started = startRecording()
      if (started) {
        recordHighlight({
          type: 'sessionStart',
          participantId: user.id,
          participantName: user.displayName,
          label: 'Recording started',
        })
      }
    }
  }, [isRecording, startRecording, stopRecording, recordHighlight, user.id, user.displayName])

  const handleLeave = useCallback(() => {
    generateSummary()
    navigate('/dashboard')
  }, [generateSummary, navigate])

  const pinParticipant = useCallback((id: string) => {
    setShellState((prev) => ({ ...prev, pinnedParticipantId: id }))
  }, [])

  const unpinParticipant = useCallback(() => {
    setShellState((prev) => ({ ...prev, pinnedParticipantId: null }))
  }, [])

  // ── Auto-speak confirmed captions ────────────────────────────────────────
  useEffect(() => {
    if (!preferences.accessibilityMode || !preferences.autoSpeakCaptions) return
    const caption = latestPrediction?.confirmed_caption
    if (!caption) return
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(new SpeechSynthesisUtterance(caption))
  }, [latestPrediction?.confirmed_caption, preferences.accessibilityMode, preferences.autoSpeakCaptions])

  // ── Screen share highlight ────────────────────────────────────────────────
  const prevScreenShareRef = useRef<string | null>(null)
  useEffect(() => {
    if (screenShareParticipantId && screenShareParticipantId !== prevScreenShareRef.current) {
      const participant = room?.participants.find(
        (p) => p.participant_id === screenShareParticipantId,
      )
      recordHighlight({
        type: 'screenShare',
        participantId: screenShareParticipantId,
        participantName: participant?.display_name,
        label: `Screen share started by ${participant?.display_name ?? screenShareParticipantId}`,
      })
    }
    prevScreenShareRef.current = screenShareParticipantId
  }, [screenShareParticipantId, room, recordHighlight])

  // ── Derived values ────────────────────────────────────────────────────────
  const participantCount = room?.participants.length ?? 1
  const latestCaption =
    captionMessages.length > 0 ? captionMessages[captionMessages.length - 1].caption : ''

  return {
    // Session
    room,
    localStream,
    localVideoRef,
    remoteStreams,
    chatMessages,
    captionMessages,
    latestCaption,
    latestPrediction,
    connectionStatus,
    peerStates,
    otherParticipants,
    loading,
    error,
    dismissError,

    // Shell state
    shellState,
    setShellState,

    // Toasts
    toasts,
    pushToast,
    dismissToast,

    // Subsystem outputs
    audioLevelMap,
    activeSpeakerId,
    presenceDepthMap,
    layout,
    spotlightId,
    mode,
    lockLayout,
    unlockLayout,
    silenceState,
    resetSilence,
    toolbarConfig,
    captionBreathingRoom,
    attentionState,
    dismissSilenceNudge,

    // AI Memory
    recordHighlight,
    searchHighlights,
    generateSummary,
    highlights,
    summary,
    syncHighlights,

    // Recording
    isRecording,
    recordingDurationMs,

    // Derived
    participantCount,
    screenShareParticipantId,
    handRaiseActive,

    // Handlers
    togglePanel,
    revealControls,
    handleReactionSelect,
    handleRecordingToggle,
    handleLeave,
    pinParticipant,
    unpinParticipant,
    sendChat: (message: string) => sendChat(message),
    clearCaptions,

    // Preferences
    updatePreferences,
  }
}

// Local type extension for screen_sharing field (may not exist in base type yet)
interface ParticipantSnapshotWithScreenShare {
  screen_sharing?: boolean
}
