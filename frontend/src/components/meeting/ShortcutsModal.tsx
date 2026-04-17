import { Modal } from '../Modal'

interface ShortcutsModalProps {
  open: boolean
  onClose: () => void
}

const SHORTCUTS: { keys: string; action: string }[] = [
  { keys: 'M', action: 'Toggle microphone' },
  { keys: 'V', action: 'Toggle camera' },
  { keys: 'A', action: 'Toggle accessibility mode' },
  { keys: 'Ctrl+C', action: 'Clear captions' },
  { keys: 'P', action: 'Toggle participants panel' },
  { keys: 'H / Shift+?', action: 'Open shortcuts help' },
  { keys: 'Escape', action: 'Close panel / modal' },
]

export function ShortcutsModal({ open, onClose }: ShortcutsModalProps) {
  if (!open) return null

  return (
    <Modal title="Keyboard Shortcuts" eyebrow="Reference" onClose={onClose}>
      <table
        style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}
        aria-label="Keyboard shortcuts"
      >
        <thead>
          <tr>
            <th style={thStyle}>Key</th>
            <th style={{ ...thStyle, textAlign: 'left' }}>Action</th>
          </tr>
        </thead>
        <tbody>
          {SHORTCUTS.map(({ keys, action }) => (
            <tr key={keys} style={{ borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
              <td style={tdKeyStyle}>
                {keys.split('+').map((k, i) => (
                  <span key={k}>
                    {i > 0 && <span style={{ color: 'rgba(0,0,0,0.35)', margin: '0 2px' }}>+</span>}
                    <kbd style={kbdStyle}>{k}</kbd>
                  </span>
                ))}
              </td>
              <td style={tdActionStyle}>{action}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Modal>
  )
}

const thStyle: React.CSSProperties = {
  padding: '0.375rem 0.5rem',
  fontSize: '0.6875rem',
  fontWeight: 600,
  color: 'rgba(0,0,0,0.45)',
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
  textAlign: 'left',
  borderBottom: '1px solid rgba(0,0,0,0.1)',
}

const tdKeyStyle: React.CSSProperties = {
  padding: '0.5rem 0.5rem',
  whiteSpace: 'nowrap',
  verticalAlign: 'middle',
}

const tdActionStyle: React.CSSProperties = {
  padding: '0.5rem 0.5rem',
  color: 'rgba(0,0,0,0.75)',
  verticalAlign: 'middle',
}

const kbdStyle: React.CSSProperties = {
  display: 'inline-block',
  padding: '0.125rem 0.375rem',
  borderRadius: 4,
  background: 'rgba(0,0,0,0.07)',
  border: '1px solid rgba(0,0,0,0.12)',
  fontFamily: 'monospace',
  fontSize: '0.8125rem',
  fontWeight: 600,
  color: 'rgba(0,0,0,0.75)',
}
