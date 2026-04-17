import { useState } from 'react'
import { Volume2, Trash2, Search } from 'lucide-react'
import type { PredictionSnapshot, CaptionMessage, MeetingHighlight } from '../../types/app'
import { GlassPanel } from './GlassPanel'

interface AssistPanelProps {
  open: boolean
  latestPrediction: PredictionSnapshot | null
  captionMessages: CaptionMessage[]
  highlights: MeetingHighlight[]
  onSearchHighlights: (query: string) => MeetingHighlight[]
  onSpeakCaption: () => void
  onClearCaptions: () => void
  onClose: () => void
}

const HIGHLIGHT_ICONS: Record<string, string> = {
  screenShare: '🖥️',
  handRaise: '✋',
  reactionBurst: '🎉',
  silenceBreak: '🔔',
  sessionStart: '▶️',
  sessionEnd: '⏹️',
}

export function AssistPanel({
  open,
  latestPrediction,
  captionMessages,
  highlights,
  onSearchHighlights,
  onSpeakCaption,
  onClearCaptions,
  onClose,
}: AssistPanelProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const filteredHighlights = searchQuery.trim() ? onSearchHighlights(searchQuery) : highlights

  return (
    <GlassPanel open={open} title="AI Assist" onClose={onClose} fullscreenOnMobile>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

        {/* Prediction output */}
        <section>
          <h3 style={{ margin: '0 0 0.5rem', fontSize: '0.75rem', fontWeight: 600, color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Prediction
          </h3>
          {latestPrediction ? (
            <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: 8, padding: '0.625rem 0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ fontWeight: 700, fontSize: '1rem', color: '#fff' }}>{latestPrediction.label}</span>
                <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>
                  {Math.round(latestPrediction.confidence * 100)}%
                </span>
              </div>
              {latestPrediction.live_caption && (
                <p style={{ margin: 0, fontSize: '0.875rem', color: 'rgba(255,255,255,0.7)', lineHeight: 1.4 }}>
                  {latestPrediction.live_caption}
                </p>
              )}
            </div>
          ) : (
            <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: '0.875rem' }}>No prediction yet</p>
          )}

          {/* Controls */}
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
            <button
              type="button"
              onClick={onSpeakCaption}
              style={controlBtnStyle}
              aria-label="Speak caption"
            >
              <Volume2 size={13} />
              <span>Speak</span>
            </button>
            <button
              type="button"
              onClick={onClearCaptions}
              style={controlBtnStyle}
              aria-label="Clear captions"
            >
              <Trash2 size={13} />
              <span>Clear</span>
            </button>
          </div>
        </section>

        {/* Caption history */}
        <section>
          <h3 style={{ margin: '0 0 0.5rem', fontSize: '0.75rem', fontWeight: 600, color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Captions
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem', maxHeight: 160, overflowY: 'auto' }}>
            {captionMessages.length === 0 ? (
              <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: '0.875rem' }}>No captions yet</p>
            ) : (
              [...captionMessages].sort((a, b) => a.timestamp.localeCompare(b.timestamp)).map((c, i) => (
                <div key={`${c.participant_id}-${c.timestamp}-${i}`} style={{ fontSize: '0.8125rem', color: 'rgba(255,255,255,0.7)' }}>
                  <span style={{ fontWeight: 600, color: 'rgba(255,255,255,0.85)', marginRight: '0.375rem' }}>
                    {c.display_name}:
                  </span>
                  {c.caption}
                </div>
              ))
            )}
          </div>
        </section>

        {/* Highlights */}
        <section>
          <h3 style={{ margin: '0 0 0.5rem', fontSize: '0.75rem', fontWeight: 600, color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Highlights
          </h3>
          <div style={{ position: 'relative', marginBottom: '0.5rem' }}>
            <Search size={13} style={{ position: 'absolute', left: 8, top: '50%', transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.35)' }} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search highlights…"
              aria-label="Search highlights"
              style={{
                width: '100%',
                boxSizing: 'border-box',
                background: 'rgba(255,255,255,0.07)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 6,
                padding: '0.375rem 0.5rem 0.375rem 1.75rem',
                color: '#fff',
                fontSize: '0.8125rem',
                outline: 'none',
              }}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', maxHeight: 160, overflowY: 'auto' }}>
            {filteredHighlights.length === 0 ? (
              <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: '0.875rem' }}>No highlights</p>
            ) : (
              filteredHighlights.map((h) => (
                <div key={h.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8125rem', color: 'rgba(255,255,255,0.7)' }}>
                  <span>{HIGHLIGHT_ICONS[h.type] ?? '📌'}</span>
                  <span style={{ flex: 1 }}>{h.label}</span>
                  <span style={{ fontSize: '0.6875rem', color: 'rgba(255,255,255,0.35)', flexShrink: 0 }}>
                    {new Date(h.wallTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </GlassPanel>
  )
}

const controlBtnStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.25rem',
  padding: '0.3125rem 0.625rem',
  borderRadius: 6,
  background: 'rgba(255,255,255,0.08)',
  border: '1px solid rgba(255,255,255,0.1)',
  color: 'rgba(255,255,255,0.75)',
  fontSize: '0.8125rem',
  cursor: 'pointer',
}
