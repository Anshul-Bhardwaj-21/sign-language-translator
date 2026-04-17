// Feature: premium-video-meeting-ui, Property 9: glow intensity monotonicity
import * as fc from 'fast-check'
import { describe, it } from 'vitest'

/**
 * Validates: Requirements 22.2
 *
 * Glow intensity formula (non-reduced-motion):
 *   glowIntensity = Math.min(1, audioLevel * 2.5)
 */
function glowIntensity(level: number): number {
  return Math.min(1, level * 2.5)
}

describe('Property 9: glow intensity monotonicity', () => {
  it('glowIntensity is non-decreasing: for any 0 <= a < b <= 1, glowIntensity(b) >= glowIntensity(a)', () => {
    fc.assert(
      fc.property(
        fc
          .tuple(fc.float({ min: 0, max: 1 }), fc.float({ min: 0, max: 1 }))
          .filter(([a, b]) => a < b),
        ([a, b]) => {
          return glowIntensity(b) >= glowIntensity(a)
        }
      )
    )
  })
})
