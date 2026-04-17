import { type CSSProperties, type ReactNode, type RefObject, useEffect, useRef } from 'react'

import { MicOff, Pin, VideoOff, Volume2 } from 'lucide-react'

import { AudioLevelMeter } from './AudioLevelMeter'
import { StatusPill } from './StatusPill'
import { useAudioLevel } from '../hooks/useAudioLevel'
import type { PresenceDepthStyle } from '../types/app'

interface MediaTileProps {
  title: string
  subtitle?: string
  stream: MediaStream | null
  muted?: boolean
  mirrored?: boolean
  micEnabled: boolean
  cameraEnabled: boolean
  accent?: 'primary' | 'secondary'
  videoRef?: RefObject<HTMLVideoElement>
  audioLevel?: number
  compact?: boolean
  selected?: boolean
  raisedHand?: boolean
  audioOutputId?: string
  statusLabel?: string
  footerSlot?: ReactNode
  surfaceChildren?: ReactNode
  presenceDepth?: PresenceDepthStyle
  onSelect?: () => void
}

export function MediaTile({
  title,
  subtitle,
  stream,
  muted = false,
  mirrored = false,
  micEnabled,
  cameraEnabled,
  accent = 'primary',
  videoRef,
  audioLevel,
  compact = false,
  selected = false,
  raisedHand = false,
  audioOutputId,
  statusLabel,
  footerSlot,
  surfaceChildren,
  presenceDepth,
  onSelect,
}: MediaTileProps) {
  const fallbackRef = useRef<HTMLVideoElement>(null)
  const activeRef = videoRef ?? fallbackRef
  const liveAudioLevel = useAudioLevel(stream, !muted && micEnabled)
  const resolvedAudioLevel = audioLevel ?? liveAudioLevel
  const speakerActive = resolvedAudioLevel > 0.16 && micEnabled

  useEffect(() => {
    const element = activeRef.current
    if (!element) {
      return
    }

    element.srcObject = stream
    if (stream) {
      void element.play().catch(() => undefined)
    }

    return () => {
      if (element) {
        element.srcObject = null
      }
    }
  }, [activeRef, stream])

  useEffect(() => {
    const element = activeRef.current as (HTMLVideoElement & { setSinkId?: (sinkId: string) => Promise<void> }) | null
    if (!element || muted || !audioOutputId || typeof element.setSinkId !== 'function') {
      return
    }

    void element.setSinkId(audioOutputId).catch(() => undefined)
  }, [activeRef, audioOutputId, muted])

  return (
    <article
      className={`media-tile media-tile--${accent}${compact ? ' media-tile--compact' : ''}${selected ? ' media-tile--selected' : ''}${speakerActive ? ' media-tile--active' : ''}${raisedHand ? ' media-tile--raised-hand' : ''}${onSelect ? ' media-tile--interactive' : ''}`}
      style={{
        '--glow-intensity': presenceDepth?.glowIntensity ?? 0,
        '--tile-scale': presenceDepth?.scale ?? 1,
      } as CSSProperties}
      onClick={onSelect}
      onKeyDown={(event) => {
        if (!onSelect) {
          return
        }
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          onSelect()
        }
      }}
      role={onSelect ? 'button' : undefined}
      tabIndex={onSelect ? 0 : undefined}
      aria-pressed={onSelect ? selected : undefined}
    >
      <div className="media-tile__surface">
        {stream && cameraEnabled ? (
          <video
            ref={activeRef}
            autoPlay
            playsInline
            muted={muted}
            className={mirrored ? 'media-tile__video media-tile__video--mirrored' : 'media-tile__video'}
          />
        ) : (
          <div className="media-tile__placeholder">
            <VideoOff size={32} />
            <p>Camera unavailable</p>
          </div>
        )}
        {surfaceChildren}
      </div>
      <footer className="media-tile__footer">
        <div>
          <strong>{title}</strong>
          {subtitle ? <span>{subtitle}</span> : null}
        </div>
        <div className="media-tile__meta">
          {statusLabel ? <StatusPill label={statusLabel} tone="neutral" /> : null}
          <AudioLevelMeter level={resolvedAudioLevel} active={micEnabled} compact />
          {!micEnabled ? <MicOff size={16} /> : <Volume2 size={16} />}
          {selected ? <Pin size={16} /> : null}
          {!cameraEnabled ? <StatusPill label="Camera off" tone="warn" /> : null}
          {footerSlot}
        </div>
      </footer>
    </article>
  )
}
