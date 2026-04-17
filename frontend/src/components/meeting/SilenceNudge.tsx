import { AnimatePresence, motion } from 'framer-motion'
import type { SilenceSuggestion } from '../../types/app'

interface SilenceNudgeProps {
  visible: boolean
  silenceDurationSeconds: number
  suggestions: SilenceSuggestion[]
  onSelectSuggestion: (suggestion: SilenceSuggestion) => void
  onDismiss: () => void
}

function formatSilenceMessage(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  return `You haven't spoken in ${minutes} minute${minutes !== 1 ? 's' : ''}`
}

export function SilenceNudge({
  visible,
  silenceDurationSeconds,
  suggestions,
  onSelectSuggestion,
  onDismiss,
}: SilenceNudgeProps) {
  return (
    <AnimatePresence>
      {visible ? (
        <motion.div
          className="silence-nudge"
          role="status"
          aria-live="polite"
          initial={{ opacity: 0, y: 12, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 8, scale: 0.97 }}
          transition={{ duration: 0.22, ease: 'easeOut' }}
          style={{
            position: 'fixed',
            bottom: '100px',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 50,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '10px',
            padding: '14px 18px',
            background: 'rgba(15, 15, 20, 0.82)',
            backdropFilter: 'blur(12px)',
            borderRadius: 'var(--radius-panel, 14px)',
            border: '1px solid rgba(255,255,255,0.08)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
            minWidth: '260px',
            maxWidth: '420px',
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: '0.85rem',
              color: 'rgba(255,255,255,0.65)',
              textAlign: 'center',
            }}
          >
            {formatSilenceMessage(silenceDurationSeconds)}
          </p>

          {suggestions.length > 0 && (
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '8px',
                justifyContent: 'center',
              }}
            >
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion.id}
                  type="button"
                  onClick={() => onSelectSuggestion(suggestion)}
                  style={{
                    padding: '6px 14px',
                    fontSize: '0.8rem',
                    fontWeight: 500,
                    color: 'rgba(255,255,255,0.85)',
                    background: 'transparent',
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: '999px',
                    cursor: 'pointer',
                    transition: 'var(--transition-ui, background 150ms ease, border-color 150ms ease)',
                  }}
                  onMouseEnter={(e) => {
                    ;(e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.08)'
                    ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(255,255,255,0.35)'
                  }}
                  onMouseLeave={(e) => {
                    ;(e.currentTarget as HTMLButtonElement).style.background = 'transparent'
                    ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(255,255,255,0.2)'
                  }}
                >
                  {suggestion.label}
                </button>
              ))}
            </div>
          )}

          <button
            type="button"
            onClick={onDismiss}
            aria-label="Dismiss silence nudge"
            style={{
              padding: '4px 12px',
              fontSize: '0.75rem',
              color: 'rgba(255,255,255,0.4)',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              borderRadius: '6px',
              transition: 'color 150ms ease',
            }}
            onMouseEnter={(e) => {
              ;(e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.7)'
            }}
            onMouseLeave={(e) => {
              ;(e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.4)'
            }}
          >
            Dismiss
          </button>
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}
