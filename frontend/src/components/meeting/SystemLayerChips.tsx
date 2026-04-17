import type React from 'react'

export interface SystemLayerChipsProps {
  isRecording: boolean
  accessibilityMode: boolean
  documentHidden: boolean
}

const chipBase: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.375rem',
  padding: '0.1875rem 0.625rem',
  borderRadius: '9999px',
  fontSize: '0.75rem',
  fontWeight: 600,
  flexShrink: 0,
  userSelect: 'none',
}

const recordingChipStyle: React.CSSProperties = {
  ...chipBase,
  background: 'rgba(255, 127, 102, 0.18)',
  border: '1px solid rgba(255, 127, 102, 0.4)',
  color: 'var(--danger, #ff7f66)',
}

const neutralChipStyle: React.CSSProperties = {
  ...chipBase,
  background: 'rgba(148, 163, 184, 0.15)',
  border: '1px solid rgba(148, 163, 184, 0.3)',
  color: 'var(--text-secondary, #94a3b8)',
}

const warnChipStyle: React.CSSProperties = {
  ...chipBase,
  background: 'rgba(251, 191, 36, 0.15)',
  border: '1px solid rgba(251, 191, 36, 0.35)',
  color: 'var(--warn, #fbbf24)',
}

export function SystemLayerChips({
  isRecording,
  accessibilityMode,
  documentHidden,
}: SystemLayerChipsProps) {
  const hasChips = isRecording || accessibilityMode || (documentHidden && isRecording)

  if (!hasChips) return null

  return (
    <div
      className="meeting-system-layer"
      role="status"
      aria-live="polite"
      aria-label="System status indicators"
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '0.5rem',
        padding: '0.375rem 1rem',
        pointerEvents: 'none',
      }}
    >
      {isRecording && (
        <span
          className="meeting-system-chip meeting-system-chip--recording"
          style={recordingChipStyle}
          aria-label="Local recording active"
        >
          <span
            style={{
              width: '0.4375rem',
              height: '0.4375rem',
              borderRadius: '50%',
              background: 'var(--danger, #ff7f66)',
              display: 'inline-block',
              flexShrink: 0,
            }}
            aria-hidden="true"
          />
          Local recording active
        </span>
      )}

      {documentHidden && isRecording && (
        <span
          className="meeting-system-chip"
          style={warnChipStyle}
          aria-label="Recording continues in background"
        >
          Recording continues in background
        </span>
      )}

      {accessibilityMode && (
        <span
          className="meeting-system-chip"
          style={neutralChipStyle}
          aria-label="Accessibility overlays are local-only"
        >
          Accessibility overlays are local-only
        </span>
      )}
    </div>
  )
}
