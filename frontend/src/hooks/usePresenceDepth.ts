import { useMemo } from 'react'
import type { PresenceDepthStyle } from '../types/app'

interface UsePresenceDepthArgs {
  audioLevelMap: Record<string, number>
  activeSpeakerId: string | null
  reducedMotion: boolean
}

interface UsePresenceDepthReturn {
  presenceDepthMap: Record<string, PresenceDepthStyle>
}

export function usePresenceDepth({
  audioLevelMap,
  activeSpeakerId,
  reducedMotion,
}: UsePresenceDepthArgs): UsePresenceDepthReturn {
  const presenceDepthMap = useMemo(() => {
    const map: Record<string, PresenceDepthStyle> = {}

    for (const [participantId, audioLevel] of Object.entries(audioLevelMap)) {
      const isActiveSpeaker = participantId === activeSpeakerId

      const glowIntensity = reducedMotion
        ? isActiveSpeaker ? 0.4 : 0
        : Math.min(1, audioLevel * 2.5)

      const scale = reducedMotion
        ? 1
        : isActiveSpeaker ? 1.02 : 1.0

      map[participantId] = { glowIntensity, scale, isActiveSpeaker }
    }

    return map
  }, [audioLevelMap, activeSpeakerId, reducedMotion])

  return { presenceDepthMap }
}
