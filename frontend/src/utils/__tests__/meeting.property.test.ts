// Feature: premium-video-meeting-ui, Property 1: timer format correctness
import * as fc from 'fast-check'
import { describe, it, expect } from 'vitest'
import { formatDuration } from '../meeting'

/**
 * Validates: Requirements 5.2
 *
 * For any non-negative integer `s`:
 * - When `s < 3600`: result matches MM:SS (exactly 2 digits, colon, 2 digits)
 * - When `s >= 3600`: result matches HH:MM:SS (exactly 2 digits, colon, 2 digits, colon, 2 digits)
 * - All segments are zero-padded to exactly 2 digits
 */
describe('Property 1: Timer format correctness', () => {
  it('formatDuration matches MM:SS for s < 3600', () => {
    fc.assert(
      fc.property(fc.nat(3599), (s) => {
        const result = formatDuration(s)
        expect(result).toMatch(/^\d{2}:\d{2}$/)
      }),
    )
  })

  it('formatDuration matches HH:MM:SS for s >= 3600', () => {
    fc.assert(
      fc.property(fc.nat().map((n) => n + 3600), (s) => {
        const result = formatDuration(s)
        // Hours can be 2+ digits; minutes and seconds are always exactly 2 digits
        expect(result).toMatch(/^\d{2,}:\d{2}:\d{2}$/)
      }),
    )
  })

  it('minutes and seconds segments are always exactly 2 digits (zero-padded)', () => {
    fc.assert(
      fc.property(fc.nat(), (s) => {
        const result = formatDuration(s)
        const segments = result.split(':')
        // Last two segments (MM and SS) must always be exactly 2 digits
        const mm = segments[segments.length - 2]
        const ss = segments[segments.length - 1]
        expect(mm).toMatch(/^\d{2}$/)
        expect(ss).toMatch(/^\d{2}$/)
      }),
    )
  })
})
