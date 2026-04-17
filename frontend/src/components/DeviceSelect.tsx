import type { DeviceOption } from '../types/app'

interface DeviceSelectProps {
  label: string
  value?: string
  options: DeviceOption[]
  disabled?: boolean
  note?: string
  onChange: (value: string) => void
}

export function DeviceSelect({ label, value, options, disabled = false, note, onChange }: DeviceSelectProps) {
  return (
    <label className="device-select">
      <span>{label}</span>
      <select value={value ?? ''} disabled={disabled || !options.length} onChange={(event) => onChange(event.target.value)}>
        {options.length ? (
          options.map((option) => (
            <option key={option.deviceId} value={option.deviceId}>
              {option.label}
            </option>
          ))
        ) : (
          <option value="">Unavailable</option>
        )}
      </select>
      {note ? <small>{note}</small> : null}
    </label>
  )
}
