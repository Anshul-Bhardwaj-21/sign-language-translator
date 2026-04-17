/**
 * Formats a duration in seconds to MM:SS (< 3600) or HH:MM:SS (>= 3600),
 * with all segments zero-padded to two digits.
 */
export function formatDuration(totalSeconds: number): string {
  const s = Math.floor(totalSeconds);
  const hours = Math.floor(s / 3600);
  const minutes = Math.floor((s % 3600) / 60);
  const seconds = s % 60;

  const mm = String(minutes).padStart(2, '0');
  const ss = String(seconds).padStart(2, '0');

  if (hours > 0) {
    const hh = String(hours).padStart(2, '0');
    return `${hh}:${mm}:${ss}`;
  }

  return `${mm}:${ss}`;
}

/**
 * Formats an ISO date string to a human-readable local date/time string.
 * Returns empty string if value is undefined or empty.
 */
export function formatDateTime(value?: string): string {
  if (!value) return '';
  const date = new Date(value);
  if (isNaN(date.getTime())) return '';
  return date.toLocaleString();
}

/**
 * Maps a connection status string to a tone used for UI colouring.
 */
export function getConnectionTone(status: string): 'good' | 'warn' | 'danger' {
  switch (status) {
    case 'connected':
      return 'good';
    case 'connecting':
    case 'reconnecting':
      return 'warn';
    case 'error':
    case 'disconnected':
      return 'danger';
    default:
      return 'warn';
  }
}
