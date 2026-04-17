import { useRef, useState, useCallback } from 'react'
import type { MeetingHighlight } from '../types/app'
import { formatDuration } from '../utils/meeting'

interface UseAIMeetingMemoryArgs {
  sessionStartMs: number
  roomId?: string
}

interface UseAIMeetingMemoryReturn {
  recordHighlight: (event: Omit<MeetingHighlight, 'id' | 'timestampMs' | 'wallTime'>) => void
  searchHighlights: (query: string) => MeetingHighlight[]
  generateSummary: () => string
  highlights: MeetingHighlight[]
  summary: string | null
  syncHighlights: () => void
}

export function useAIMeetingMemory({
  sessionStartMs,
  roomId,
}: UseAIMeetingMemoryArgs): UseAIMeetingMemoryReturn {
  // Primary store — ref to avoid re-renders on every event
  const storeRef = useRef<MeetingHighlight[]>([])

  // State only for display (lazy sync when AssistPanel opens)
  const [highlights, setHighlights] = useState<MeetingHighlight[]>([])
  const [summary, setSummary] = useState<string | null>(null)

  const recordHighlight = useCallback(
    (event: Omit<MeetingHighlight, 'id' | 'timestampMs' | 'wallTime'>) => {
      const id =
        typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
          ? crypto.randomUUID()
          : `${Date.now()}-${Math.random()}`

      const highlight: MeetingHighlight = {
        ...event,
        id,
        timestampMs: Date.now() - sessionStartMs,
        wallTime: new Date().toISOString(),
      }

      storeRef.current = [...storeRef.current, highlight]
    },
    [sessionStartMs],
  )

  const searchHighlights = useCallback((query: string): MeetingHighlight[] => {
    const all = [...storeRef.current].sort((a, b) => a.timestampMs - b.timestampMs)

    if (!query.trim()) {
      return all
    }

    const tokens = query.toLowerCase().split(/\s+/).filter(Boolean)

    return all.filter((h) => {
      const labelLower = h.label.toLowerCase()
      const typeLower = h.type.toLowerCase()
      return tokens.some((token) => labelLower.includes(token) || typeLower.includes(token))
    })
  }, [])

  const generateSummary = useCallback((): string => {
    const store = storeRef.current

    if (store.length === 0) {
      const result = 'No highlights recorded for this session.'
      setSummary(result)
      if (roomId) {
        try {
          sessionStorage.setItem(`meeting-summary-${roomId}`, result)
        } catch {
          // sessionStorage may be unavailable in some environments
        }
      }
      return result
    }

    // Duration from first to last highlight (or session start to last)
    const lastHighlight = store[store.length - 1]
    const durationSeconds = Math.floor(lastHighlight.timestampMs / 1000)
    const duration = formatDuration(durationSeconds)

    // Collect unique participant names
    const names = Array.from(
      new Set(store.map((h) => h.participantName).filter((n): n is string => Boolean(n))),
    )
    const participantsLine = names.length > 0 ? names.join(', ') : 'Unknown'

    // Key moments sorted by timestamp
    const sorted = [...store].sort((a, b) => a.timestampMs - b.timestampMs)
    const moments = sorted
      .map((h) => {
        const ts = formatDuration(Math.floor(h.timestampMs / 1000))
        return `  ${ts} — ${h.label}`
      })
      .join('\n')

    const result = `Meeting Summary — ${duration}\nParticipants: ${participantsLine}\nKey moments:\n${moments}`

    setSummary(result)

    if (roomId) {
      try {
        sessionStorage.setItem(`meeting-summary-${roomId}`, result)
      } catch {
        // sessionStorage may be unavailable in some environments
      }
    }

    return result
  }, [roomId])

  // Sync ref → state; call this when AssistPanel opens
  const syncHighlights = useCallback(() => {
    setHighlights([...storeRef.current])
  }, [])

  return {
    recordHighlight,
    searchHighlights,
    generateSummary,
    highlights,
    summary,
    syncHighlights,
  }
}
