import type { PredictionOverlay } from '../types/app'

interface VisionAssistOverlayProps {
  overlay?: PredictionOverlay | null
  visible: boolean
  mirrored?: boolean
}

const HAND_CONNECTIONS: Array<[number, number]> = [
  [0, 1],
  [1, 2],
  [2, 3],
  [3, 4],
  [0, 5],
  [5, 6],
  [6, 7],
  [7, 8],
  [5, 9],
  [9, 10],
  [10, 11],
  [11, 12],
  [9, 13],
  [13, 14],
  [14, 15],
  [15, 16],
  [13, 17],
  [17, 18],
  [18, 19],
  [19, 20],
  [0, 17],
]

function toPercent(value: number, mirrored: boolean) {
  const safe = Math.min(1, Math.max(0, value))
  return `${(mirrored ? 1 - safe : safe) * 100}%`
}

export function VisionAssistOverlay({ overlay, visible, mirrored = false }: VisionAssistOverlayProps) {
  if (!visible) {
    return null
  }

  return (
    <div className="vision-overlay" aria-hidden="true">
      <div className="vision-overlay__face-frame">
        <span />
        <span />
        <span />
      </div>

      {overlay?.hand_bounds ? (
        <div
          className="vision-overlay__hand-box"
          style={{
            left: toPercent(overlay.hand_bounds.x_min, mirrored),
            top: `${Math.min(1, Math.max(0, overlay.hand_bounds.y_min)) * 100}%`,
            width: `${Math.max(4, (overlay.hand_bounds.x_max - overlay.hand_bounds.x_min) * 100)}%`,
            height: `${Math.max(6, (overlay.hand_bounds.y_max - overlay.hand_bounds.y_min) * 100)}%`,
          }}
        />
      ) : null}

      {overlay?.hand_landmarks?.length ? (
        <svg className="vision-overlay__svg" viewBox="0 0 100 100" preserveAspectRatio="none">
          {HAND_CONNECTIONS.map(([startIndex, endIndex]) => {
            const start = overlay.hand_landmarks[startIndex]
            const end = overlay.hand_landmarks[endIndex]
            if (!start || !end) {
              return null
            }

            return (
              <line
                key={`${startIndex}-${endIndex}`}
                x1={(mirrored ? 1 - start.x : start.x) * 100}
                y1={start.y * 100}
                x2={(mirrored ? 1 - end.x : end.x) * 100}
                y2={end.y * 100}
              />
            )
          })}
          {overlay.hand_landmarks.map((point, index) => (
            <circle key={index} cx={(mirrored ? 1 - point.x : point.x) * 100} cy={point.y * 100} r="0.9" />
          ))}
        </svg>
      ) : (
        <div className="vision-overlay__hint">Vision assist is ready. Raise your hand into frame for translation guidance.</div>
      )}
    </div>
  )
}
