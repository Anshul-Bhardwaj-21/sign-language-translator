import { useState, useEffect, useRef, useCallback } from 'react'
import type { MeetingLayout, SmartLayoutMode } from '../types/app'

interface UseSmartLayoutArgs {
  activeSpeakerId: string | null
  screenShareParticipantId: string | null
  reactionBurstCount: number
  manualPinnedId: string | null
  participantCount: number
}

interface UseSmartLayoutReturn {
  layout: MeetingLayout
  spotlightId: string | null
  mode: SmartLayoutMode
  lockLayout: () => void
  unlockLayout: () => void
}

export function useSmartLayout({
  activeSpeakerId,
  screenShareParticipantId,
  reactionBurstCount,
  manualPinnedId,
  participantCount: _participantCount,
}: UseSmartLayoutArgs): UseSmartLayoutReturn {
  const [layout, setLayout] = useState<MeetingLayout>('grid')
  const [spotlightId, setSpotlightId] = useState<string | null>(null)
  const [mode, setMode] = useState<SmartLayoutMode>('auto')

  // Refs to avoid stale closures
  const preShareLayoutRef = useRef<MeetingLayout | null>(null)
  const speakerDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reactionGridTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const layoutBeforeReactionRef = useRef<MeetingLayout | null>(null)

  // Transition 1 & 6: screen share start/end
  useEffect(() => {
    if (screenShareParticipantId !== null) {
      // Transition 1: screen share starts → focus layout
      preShareLayoutRef.current = layout
      setLayout('focus')
      setSpotlightId(screenShareParticipantId)
    } else {
      // Transition 6: screen share ends → restore pre-share layout (if no manual pin)
      if (manualPinnedId === null && preShareLayoutRef.current !== null) {
        setLayout(preShareLayoutRef.current)
        preShareLayoutRef.current = null
        setSpotlightId(null)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [screenShareParticipantId])

  // Transition 2: active speaker changes → debounce 1500ms → update spotlightId
  useEffect(() => {
    if (screenShareParticipantId !== null) return
    if (manualPinnedId !== null) return
    if (mode !== 'auto') return

    if (speakerDebounceRef.current !== null) {
      clearTimeout(speakerDebounceRef.current)
    }

    speakerDebounceRef.current = setTimeout(() => {
      setSpotlightId(activeSpeakerId)
      speakerDebounceRef.current = null
    }, 1500)

    return () => {
      if (speakerDebounceRef.current !== null) {
        clearTimeout(speakerDebounceRef.current)
        speakerDebounceRef.current = null
      }
    }
  }, [activeSpeakerId, screenShareParticipantId, manualPinnedId, mode])

  // Transition 3: reaction burst >= 3 → grid for 5000ms then restore
  useEffect(() => {
    if (reactionBurstCount < 3) return
    if (mode !== 'auto') return
    if (screenShareParticipantId !== null) return

    // Save current layout before switching to grid
    layoutBeforeReactionRef.current = layout

    setLayout('grid')

    if (reactionGridTimerRef.current !== null) {
      clearTimeout(reactionGridTimerRef.current)
    }

    reactionGridTimerRef.current = setTimeout(() => {
      setLayout(layoutBeforeReactionRef.current ?? 'grid')
      layoutBeforeReactionRef.current = null
      reactionGridTimerRef.current = null
    }, 5000)

    return () => {
      if (reactionGridTimerRef.current !== null) {
        clearTimeout(reactionGridTimerRef.current)
        reactionGridTimerRef.current = null
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reactionBurstCount])

  // Transitions 4 & 5: manual pin/unpin → lock/unlock mode
  useEffect(() => {
    if (manualPinnedId !== null) {
      // Transition 4: manual pin → locked mode
      setMode('locked')
      setSpotlightId(manualPinnedId)
    } else {
      // Transition 5: manual unpin → auto mode
      setMode('auto')
    }
  }, [manualPinnedId])

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      if (speakerDebounceRef.current !== null) clearTimeout(speakerDebounceRef.current)
      if (reactionGridTimerRef.current !== null) clearTimeout(reactionGridTimerRef.current)
    }
  }, [])

  const lockLayout = useCallback(() => {
    setMode('locked')
  }, [])

  const unlockLayout = useCallback(() => {
    setMode('auto')
  }, [])

  return { layout, spotlightId, mode, lockLayout, unlockLayout }
}
