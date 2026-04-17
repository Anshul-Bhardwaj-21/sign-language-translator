// Feature: premium-video-meeting-ui, Property 5: AI Memory highlight recording
// Feature: premium-video-meeting-ui, Property 6: AI Memory search completeness
import * as fc from 'fast-check'
import { describe, it, expect } from 'vitest'

// ── Shared types ──────────────────────────────────────────────────────────────

type HighlightType =
  | 'screenShare'
  | 'handRaise'
  | 'reactionBurst'
  | 'silenceBreak'
  | 'sessionStart'
  | 'sessionEnd'

interface MeetingHighlight {
  id: string
  type: HighlightType
  participantId?: string
  participantName?: string
  timestampMs: number
  wallTime: string
  label: string
}

// ── Pure logic extracted from useAIMeetingMemory ──────────────────────────────

function recordHighlight(
  store: MeetingHighlight[],
  event: Omit<MeetingHighlight, 'id' | 'timestampMs' | 'wallTime'>,
  sessionStartMs: number,
): MeetingHighlight[] {
  const highlight: MeetingHighlight = {
    ...event,
    id: `${Date.now()}-${Math.random()}`,
    timestampMs: Date.now() - sessionStartMs,
    wallTime: new Date().toISOString(),
  }
  return [...store, highlight]
}

function searchHighlights(store: MeetingHighlight[], query: string): MeetingHighlight[] {
  const all = [...store].sort((a, b) => a.timestampMs - b.timestampMs)
  if (!query.trim()) return all
  const tokens = query.toLowerCase().split(/\s+/).filter(Boolean)
  return all.filter((h) => {
    const labelLower = h.label.toLowerCase()
    const typeLower = h.type.toLowerCase()
    return tokens.some((token) => labelLower.includes(token) || typeLower.includes(token))
  })
}

// ── Arbitraries ───────────────────────────────────────────────────────────────

const highlightTypeArb = fc.constantFrom<HighlightType>(
  'screenShare',
  'handRaise',
  'reactionBurst',
  'silenceBreak',
  'sessionStart',
  'sessionEnd',
)

const highlightArb = fc.record<MeetingHighlight>({
  id: fc.string({ minLength: 1 }),
  type: highlightTypeArb,
  timestampMs: fc.nat(),
  wallTime: fc.constant(new Date().toISOString()),
  label: fc.string(),
})

// ── Property 5: AI Memory highlight recording ─────────────────────────────────

/**
 * Validates: Requirements 18.3, 18.4
 *
 * For any supported event type, calling `recordHighlight` on an empty store
 * results in exactly 1 entry whose `type` matches the event type.
 */
describe('Property 5: AI Memory highlight recording', () => {
  it('recordHighlight adds exactly one entry with matching type to an empty store', () => {
    fc.assert(
      fc.property(highlightTypeArb, fc.string(), (type, label) => {
        const sessionStartMs = Date.now() - 1000
        const result = recordHighlight([], { type, label }, sessionStartMs)

        expect(result).toHaveLength(1)
        expect(result[0].type).toBe(type)
      }),
    )
  })
})

// ── Property 6: AI Memory search completeness ─────────────────────────────────

/**
 * Validates: Requirements 18.5
 *
 * For any non-empty highlights array and a query that exactly matches at least
 * one entry's `type`, `searchHighlights` returns all highlights whose label or
 * type contains the query, and no others.
 */
describe('Property 6: AI Memory search completeness', () => {
  it('searchHighlights returns all matching and no non-matching entries when query equals a type', () => {
    fc.assert(
      fc.property(
        fc.array(highlightArb, { minLength: 1 }),
        highlightTypeArb,
        (store, queryType) => {
          const query = queryType // exact type string as query
          const results = searchHighlights(store, query)

          const queryLower = query.toLowerCase()

          // Every returned entry must match
          for (const h of results) {
            const matches =
              h.label.toLowerCase().includes(queryLower) ||
              h.type.toLowerCase().includes(queryLower)
            expect(matches).toBe(true)
          }

          // Every matching entry in the store must be returned
          const expectedIds = new Set(
            store
              .filter(
                (h) =>
                  h.label.toLowerCase().includes(queryLower) ||
                  h.type.toLowerCase().includes(queryLower),
              )
              .map((h) => h.id),
          )
          const resultIds = new Set(results.map((h) => h.id))

          expect(resultIds).toEqual(expectedIds)
        },
      ),
    )
  })
})
