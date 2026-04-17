import type { UserPreferences } from '../../types/app'
import { Modal } from '../Modal'

interface SettingsModalProps {
  open: boolean
  preferences: UserPreferences
  onUpdatePreferences: (updates: Partial<UserPreferences>) => void
  onClose: () => void
}

export function SettingsModal({ open, preferences, onUpdatePreferences, onClose }: SettingsModalProps) {
  if (!open) return null

  return (
    <Modal title="Settings" eyebrow="Meeting" onClose={onClose}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', minWidth: 280 }}>

        <ToggleRow
          label="Translation"
          description="Auto-translate captions"
          checked={preferences.translationEnabled}
          onChange={(v) => onUpdatePreferences({ translationEnabled: v })}
        />

        <ToggleRow
          label="Auto-speak captions"
          description="Read captions aloud via speech synthesis"
          checked={preferences.autoSpeakCaptions}
          onChange={(v) => onUpdatePreferences({ autoSpeakCaptions: v })}
        />

        <ToggleRow
          label="Vision overlay"
          description="Show hand-detection overlay on local tile"
          checked={preferences.showVisionOverlay}
          onChange={(v) => onUpdatePreferences({ showVisionOverlay: v })}
        />

        <ToggleRow
          label="Accessibility mode"
          description="Enhanced contrast and larger UI elements"
          checked={preferences.accessibilityMode}
          onChange={(v) => onUpdatePreferences({ accessibilityMode: v })}
        />

        {/* Capture interval slider */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <label htmlFor="capture-interval" style={labelStyle}>
              Capture interval
            </label>
            <span style={{ fontSize: '0.8125rem', color: 'rgba(0,0,0,0.55)' }}>
              {preferences.captureIntervalMs} ms
            </span>
          </div>
          <p style={descStyle}>How often to capture frames for AI analysis (500–2000 ms)</p>
          <input
            id="capture-interval"
            type="range"
            min={500}
            max={2000}
            step={100}
            value={preferences.captureIntervalMs}
            onChange={(e) => onUpdatePreferences({ captureIntervalMs: Number(e.target.value) })}
            style={{ width: '100%', accentColor: 'var(--color-accent-start, #6366f1)' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6875rem', color: 'rgba(0,0,0,0.4)' }}>
            <span>500 ms</span>
            <span>2000 ms</span>
          </div>
        </div>
      </div>
    </Modal>
  )
}

function ToggleRow({
  label,
  description,
  checked,
  onChange,
}: {
  label: string
  description: string
  checked: boolean
  onChange: (value: boolean) => void
}) {
  const id = `toggle-${label.toLowerCase().replace(/\s+/g, '-')}`
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
      <div>
        <label htmlFor={id} style={labelStyle}>{label}</label>
        <p style={descStyle}>{description}</p>
      </div>
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        style={{
          width: 40,
          height: 22,
          borderRadius: 11,
          background: checked ? 'var(--color-accent-start, #6366f1)' : 'rgba(0,0,0,0.15)',
          border: 'none',
          cursor: 'pointer',
          position: 'relative',
          flexShrink: 0,
          transition: 'background 150ms ease',
        }}
        aria-label={label}
      >
        <span
          style={{
            position: 'absolute',
            top: 3,
            left: checked ? 21 : 3,
            width: 16,
            height: 16,
            borderRadius: '50%',
            background: '#fff',
            transition: 'left 150ms ease',
          }}
        />
      </button>
    </div>
  )
}

const labelStyle: React.CSSProperties = {
  fontSize: '0.875rem',
  fontWeight: 500,
  color: 'rgba(0,0,0,0.85)',
  display: 'block',
}

const descStyle: React.CSSProperties = {
  margin: '0.125rem 0 0',
  fontSize: '0.75rem',
  color: 'rgba(0,0,0,0.45)',
}
