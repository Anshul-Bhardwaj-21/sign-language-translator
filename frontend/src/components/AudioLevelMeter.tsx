interface AudioLevelMeterProps {
  level: number
  active?: boolean
  compact?: boolean
}

export function AudioLevelMeter({ level, active = true, compact = false }: AudioLevelMeterProps) {
  const bars = compact ? 10 : 14

  return (
    <div className={`audio-meter${compact ? ' audio-meter--compact' : ''}`} aria-hidden="true">
      {Array.from({ length: bars }, (_, index) => {
        const threshold = (index + 1) / bars
        const energized = active && level >= threshold - 0.08
        return <span key={threshold} className={energized ? 'audio-meter__bar audio-meter__bar--active' : 'audio-meter__bar'} />
      })}
    </div>
  )
}
