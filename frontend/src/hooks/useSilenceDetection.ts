import { useCallback, useEffect, useRef, useState } from 'react'
import type { SilenceDetectionConfig, SilenceDetectionState } from '../types/app'

interface UseSilenceDetectionArgs {
  audioLevelMap: Record<string, number>
  config: SilenceDetectionConfig
}

interface UseSilenceDetectionReturn {
  silenceState: SilenceDetectionState
  resetSilence: () => void
}

export function useSilenceDetection({
  audioLevelMap,
  config,
}: UseSilenceDetectionArgs): UseSilenceDetectionReturn {
  const lastActivityMs = useRef<number>(Date.now())

  const [silenceState, setSilenceState] = useState<SilenceDetectionState>({
    isSilent: false,
    silenceDurationSeconds: 0,
    lastActivityMs: lastActivityMs.current,
  })

  // Watch audioLevelMap — reset activity if any participant exceeds threshold
  useEffect(() => {
    const anyActive = Object.values(audioLevelMap).some(
      (level) => level > config.audioThreshold
    )
    if (anyActive) {
      lastActivityMs.current = Date.now()
      setSilenceState((prev) => ({
        ...prev,
        isSilent: false,
        silenceDurationSeconds: 0,
        lastActivityMs: lastActivityMs.current,
      }))
    }
  }, [audioLevelMap, config.audioThreshold])

  // Interval to update silenceDurationSeconds and isSilent
  useEffect(() => {
    const id = setInterval(() => {
      const now = Date.now()
      const silenceDurationSeconds = Math.floor(
        (now - lastActivityMs.current) / 1000
      )
      const isSilent = silenceDurationSeconds >= config.thresholdSeconds
      setSilenceState({
        isSilent,
        silenceDurationSeconds,
        lastActivityMs: lastActivityMs.current,
      })
    }, 1000)

    return () => clearInterval(id)
  }, [config.thresholdSeconds])

  const resetSilence = useCallback(() => {
    lastActivityMs.current = Date.now()
    setSilenceState({
      isSilent: false,
      silenceDurationSeconds: 0,
      lastActivityMs: lastActivityMs.current,
    })
  }, [])

  return { silenceState, resetSilence }
}
