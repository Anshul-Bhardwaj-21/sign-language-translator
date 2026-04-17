import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import type { ChatMessage } from '../../types/app'
import { GlassPanel } from './GlassPanel'

interface ChatPanelProps {
  open: boolean
  chatMessages: ChatMessage[]
  onSend: (message: string) => void
  onClose: () => void
}

export function ChatPanel({ open, chatMessages, onSend, onClose }: ChatPanelProps) {
  const [draft, setDraft] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages, open])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = draft.trim()
    if (!trimmed) return
    onSend(trimmed)
    setDraft('')
  }

  return (
    <GlassPanel open={open} title="Chat" onClose={onClose} fullscreenOnMobile>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '0.75rem' }}>
        {/* Message list */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {chatMessages.length === 0 ? (
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.875rem', textAlign: 'center', marginTop: '2rem' }}>
              No messages yet
            </p>
          ) : (
            chatMessages.map((msg, i) => (
              <div key={`${msg.participant_id}-${msg.timestamp}-${i}`} style={{ display: 'flex', flexDirection: 'column', gap: '0.125rem' }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.8125rem', color: 'rgba(255,255,255,0.85)' }}>
                    {msg.display_name}
                  </span>
                  <span style={{ fontSize: '0.6875rem', color: 'rgba(255,255,255,0.35)' }}>
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '0.875rem', color: 'rgba(255,255,255,0.75)', lineHeight: 1.4 }}>
                  {msg.message}
                </p>
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>

        {/* Send form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
          <input
            type="text"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Type a message…"
            aria-label="Chat message"
            style={{
              flex: 1,
              background: 'rgba(255,255,255,0.07)',
              border: '1px solid rgba(255,255,255,0.12)',
              borderRadius: 8,
              padding: '0.5rem 0.75rem',
              color: '#fff',
              fontSize: '0.875rem',
              outline: 'none',
            }}
          />
          <button
            type="submit"
            aria-label="Send message"
            disabled={!draft.trim()}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 36,
              height: 36,
              borderRadius: 8,
              background: draft.trim() ? 'var(--color-accent-start, #6366f1)' : 'rgba(255,255,255,0.08)',
              border: 'none',
              cursor: draft.trim() ? 'pointer' : 'default',
              color: '#fff',
              flexShrink: 0,
            }}
          >
            <Send size={15} />
          </button>
        </form>
      </div>
    </GlassPanel>
  )
}
