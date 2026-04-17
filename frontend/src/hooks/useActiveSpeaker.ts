import { useState, useEffect, useRef } from 'react'

interface UseActiveSpeakerArgs {
  audioLevelMap: Record<string, number>
  hysteresisMs?: number
  threshold?: number
}

interface UseActiveSpeakerReturn {
  activeSpeakerId: string | null
}

export function useActiveSpeaker({
  audioLevelMap,
  hysteresisMs = 800,
  threshold = 0.12,
}: UseActiveSpeakerArgs): UseActiveSpeakerReturn {
  const [activeSpeakerId, setActiveSpeakerId] = useState<string | null>(null)
  const candidateRef = useRef<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    // Find participant with highest audio level exceeding threshold
    let topId: string | null = null
    let topLevel = threshold

    for (const [id, level] of Object.entries(audioLevelMap)) {
      if (level > topLevel) {
        topLevel = level
        topId = id
      }
    }

    // If the candidate hasn't changed, nothing to do
    if (topId === candidateRef.current) return

    // New candidate — clear existing timer and start hysteresis window
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }

    candidateRef.current = topId

    timerRef.current = setTimeout(() => {
      setActiveSpeakerId(candidateRef.current)
      timerRef.current = null
    }, hysteresisMs)
  }, [audioLevelMap, hysteresisMs, threshold])

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current !== null) {
        clearTimeout(timerRef.current)
      }
    }
  }, [])

  return { activeSpeakerId }
}
