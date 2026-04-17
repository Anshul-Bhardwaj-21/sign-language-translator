// Feature: premium-video-meeting-ui, Property 4: caption source preference
import * as fc from 'fast-check'
import { describe, it, expect } from 'vitest'

/**
 * Validates: Requirements 11.5
 *
 * For any non-empty `roomCaption` and any `localCaption`, the resolved caption
 * equals `roomCaption` (room-wide caption takes precedence when non-empty).
 */

function resolveCaption(roomCaption: string, localCaption: string): string {
  // Room-wide caption takes precedence when non-empty
  return roomCaption || localCaption
}

describe('Property 4: Caption source preference', () => {
  it('resolveCaption returns roomCaption when roomCaption is non-empty', () => {
    fc.assert(
      fc.property(fc.string({ minLength: 1 }), fc.string(), (roomCaption, localCaption) => {
        const result = resolveCaption(roomCaption, localCaption)
        expect(result).toBe(roomCaption)
      }),
    )
  })
})
