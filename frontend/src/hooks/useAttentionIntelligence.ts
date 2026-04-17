import { useEffect, useRef, useState } from 'react'
import type { AttentionState, ParticipantAttentionState, ParticipantSnapshot } from '../types/app'

interface UseAttentionIntelligenceArgs {
  participants: ParticipantSnapshot[]
  localParticipantId: string
  audioLevelMap: Record<string, number>
  silenceNudgeThresholdMs?: number
  inactivityThresholdMs?: number
}

interface UseAttentionIntelligenceReturn {
  attentionState: AttentionState
  dismissSilenceNudge: () => void
}

const AUDIO_THRESHOLD = 0.1
const POLL_INTERVAL_MS = 5000

export function useAttentionIntelligence({
  participants,
  localParticipantId,
  audioLevelMap,
  silenceNudgeThresholdMs = 600_000,
  inactivityThresholdMs = 300_000,
}: UseAttentionIntelligenceArgs): UseAttentionIntelligenceReturn {
  const lastSpokeRef = useRef<Map<string, number>>(new Map())

  const [attentionState, setAttentionState] = useState<AttentionState>({
    participants: {},
    localSilenceDurationMs: 0,
    showSilenceNudge: false,
  })

  // Watch audioLevelMap — update lastSpokeMs immediately when a participant speaks,
  // and auto-dismiss nudge when local participant speaks
  useEffect(() => {
    const now = Date.now()
    let localSpoke = false

    for (const [id, level] of Object.entries(audioLevelMap)) {
      if (level > AUDIO_THRESHOLD) {
        lastSpokeRef.current.set(id, now)
        if (id === localParticipantId) {
          localSpoke = true
        }
      }
    }

    if (localSpoke) {
      setAttentionState(prev =>
        prev.showSilenceNudge ? { ...prev, showSilenceNudge: false } : prev
      )
    }
  }, [audioLevelMap, localParticipantId])

  // Poll every 5 s to recompute silence durations and inactivity
  useEffect(() => {
    const intervalId = setInterval(() => {
      const now = Date.now()
      const participantStates: Record<string, ParticipantAttentionState> = {}

      for (const p of participants) {
        const id = p.participant_id

        // If currently speaking, update lastSpokeMs
        if ((audioLevelMap[id] ?? 0) > AUDIO_THRESHOLD) {
          lastSpokeRef.current.set(id, now)
        }

        const lastSpokeMs = lastSpokeRef.current.get(id) ?? now
        const silenceDurationMs = now - lastSpokeMs
        const cameraActive = p.camera_enabled
        const audioActive = p.mic_enabled
        const isInactive = !cameraActive && !audioActive && silenceDurationMs > inactivityThresholdMs

        participantStates[id] = {
          participantId: id,
          lastSpokeMs,
          silenceDurationMs,
          cameraActive,
          audioActive,
          isInactive,
        }
      }

      const localState = participantStates[localParticipantId]
      const localSilenceDurationMs = localState?.silenceDurationMs ?? 0

      setAttentionState(prev => ({
        participants: participantStates,
        localSilenceDurationMs,
        showSilenceNudge:
          prev.showSilenceNudge || localSilenceDurationMs > silenceNudgeThresholdMs,
      }))
    }, POLL_INTERVAL_MS)

    return () => clearInterval(intervalId)
  }, [participants, localParticipantId, audioLevelMap, silenceNudgeThresholdMs, inactivityThresholdMs])

  const dismissSilenceNudge = () => {
    setAttentionState(prev => ({ ...prev, showSilenceNudge: false }))
  }

  return { attentionState, dismissSilenceNudge }
}
