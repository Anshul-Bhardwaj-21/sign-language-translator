import { describe, it, expect } from 'vitest';
import { formatDuration } from '../meeting';

describe('formatDuration', () => {
  it('formats 0 seconds as "00:00"', () => {
    expect(formatDuration(0)).toBe('00:00');
  });

  it('formats 59 seconds as "00:59"', () => {
    expect(formatDuration(59)).toBe('00:59');
  });

  it('formats 3599 seconds as "59:59"', () => {
    expect(formatDuration(3599)).toBe('59:59');
  });

  it('formats 3600 seconds as "01:00:00"', () => {
    expect(formatDuration(3600)).toBe('01:00:00');
  });

  it('formats 7384 seconds as "02:03:04"', () => {
    expect(formatDuration(7384)).toBe('02:03:04');
  });
});
