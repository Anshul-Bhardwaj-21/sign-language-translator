// Feature: premium-video-meeting-ui, Property 10: silence detection correctness
import * as fc from 'fast-check'
import { describe, it } from 'vitest'

/**
 * Validates: Requirements 19.1, 23.1, 23.4
 *
 * Pure logic extracted from useSilenceDetection for property testing.
 */
function computeIsSilent(
  audioLevelMap: Record<string, number>,
  audioThreshold: number,
  silenceDurationSeconds: number,
  thresholdSeconds: number
): boolean {
  const anyActive = Object.values(audioLevelMap).some(level => level > audioThreshold)
  if (anyActive) return false
  return silenceDurationSeconds >= thresholdSeconds
}

describe('Property 10: silence detection correctness', () => {
  it('all levels below threshold for >= thresholdSeconds → isSilent is true', () => {
    // Use a fixed threshold so we can compute max level as threshold - 0.001
    const threshold = Math.fround(0.5)
    fc.assert(
      fc.property(
        fc.record({
          audioLevelMap: fc.dictionary(
            fc.string(),
            fc.float({ min: Math.fround(0), max: Math.fround(threshold - 0.001), noNaN: true })
          ),
          thresholdSeconds: fc.nat({ max: 120 }),
        }),
        ({ audioLevelMap, thresholdSeconds }) => {
          // silenceDurationSeconds equals thresholdSeconds → isSilent must be true
          return computeIsSilent(audioLevelMap, threshold, thresholdSeconds, thresholdSeconds) === true
        }
      )
    )
  })

  it('any level above threshold → isSilent is false', () => {
    // Use a fixed threshold so we can guarantee activeLevel > threshold
    const threshold = Math.fround(0.5)
    fc.assert(
      fc.property(
        fc.record({
          participantId: fc.string({ minLength: 1 }),
          activeLevel: fc.float({ min: Math.fround(threshold + 0.001), max: Math.fround(1), noNaN: true }),
          silenceDurationSeconds: fc.nat({ max: 3600 }),
          thresholdSeconds: fc.nat({ max: 120 }),
        }),
        ({ participantId, activeLevel, silenceDurationSeconds, thresholdSeconds }) => {
          const audioLevelMap: Record<string, number> = { [participantId]: activeLevel }
          return computeIsSilent(audioLevelMap, threshold, silenceDurationSeconds, thresholdSeconds) === false
        }
      )
    )
  })
})
