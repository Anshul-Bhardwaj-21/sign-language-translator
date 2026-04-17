import type { PanelView, ToolbarButtonConfig } from '../../types/app'
import type { MeetingFloatingToolbarProps } from '../../types/app'
import { ReactionPicker } from './ReactionPicker'

const REACTION_OPTIONS = [
  { emoji: '👍', label: 'Thumbs up' },
  { emoji: '❤️', label: 'Heart' },
  { emoji: '😂', label: 'Laugh' },
  { emoji: '😮', label: 'Wow' },
  { emoji: '👏', label: 'Clap' },
  { emoji: '✋', label: 'Raise hand' },
]

function getHandler(
  id: string,
  props: MeetingFloatingToolbarProps
): (() => void) | undefined {
  const map: Record<string, () => void> = {
    mic: props.onToggleMic,
    camera: props.onToggleCamera,
    share: props.onScreenShare,
    record: props.onToggleRecording,
    reactions: props.onToggleReactionPicker,
    accessibility: props.onToggleAccessibility,
    chat: () => props.onTogglePanel('chat' as PanelView),
    participants: () => props.onTogglePanel('participants' as PanelView),
    assist: () => props.onTogglePanel('transcript' as PanelView),
    settings: props.onOpenSettings,
    help: props.onOpenShortcuts,
    info: props.onOpenInfo,
    leave: props.onLeave,
  }
  return map[id]
}

function ToolbarButton({
  btn,
  handler,
}: {
  btn: ToolbarButtonConfig
  handler?: () => void
}) {
  if (btn.hidden) return null

  const Icon = btn.icon

  const classNames = [
    'meeting-control',
    btn.off ? 'meeting-control--off' : '',
    btn.prominent ? 'meeting-control--prominent' : '',
    btn.active ? 'meeting-control--accent' : '',
  ]
    .filter(Boolean)
    .join(' ')

  const prominentStyle: React.CSSProperties = btn.prominent
    ? {
        background: 'linear-gradient(135deg, var(--color-accent-start, #6366f1) 0%, var(--color-accent-end, #a855f7) 100%)',
        borderColor: 'transparent',
        color: '#fff',
        transform: 'scale(1.06)',
      }
    : {}

  return (
    <button
      type="button"
      className={classNames}
      style={prominentStyle}
      onClick={handler}
      aria-label={btn.label}
      aria-pressed={btn.active}
      title={btn.label}
    >
      <Icon size={18} aria-hidden="true" />
      <span className="meeting-control__label">{btn.label}</span>
    </button>
  )
}

function ToolbarGroup({
  buttons,
  props,
}: {
  buttons: ToolbarButtonConfig[]
  props: MeetingFloatingToolbarProps
}) {
  const visible = buttons.filter((b) => !b.hidden)
  if (visible.length === 0) return null

  return (
    <div className="meeting-toolbar__group">
      {buttons.map((btn) => (
        <ToolbarButton key={btn.id} btn={btn} handler={getHandler(btn.id, props)} />
      ))}
    </div>
  )
}

export function MeetingFloatingToolbar(props: MeetingFloatingToolbarProps) {
  const { visible, showReactionPicker, toolbarConfig, onReactionSelect } = props

  const wrapStyle: React.CSSProperties = {
    opacity: visible ? 1 : 0,
    pointerEvents: visible ? 'auto' : 'none',
    transition: 'opacity 280ms ease, transform 280ms ease',
  }

  return (
    <div className="meeting-toolbar-wrap" style={wrapStyle} aria-hidden={!visible}>
      {showReactionPicker && (
        <ReactionPicker
          open={showReactionPicker}
          options={REACTION_OPTIONS}
          onSelect={(option) => onReactionSelect?.(option.emoji)}
        />
      )}
      <div className="meeting-toolbar">
        <ToolbarGroup buttons={toolbarConfig.primaryGroup} props={props} />
        <ToolbarGroup buttons={toolbarConfig.secondaryGroup} props={props} />
        {toolbarConfig.overflowGroup.length > 0 && (
          <ToolbarGroup buttons={toolbarConfig.overflowGroup} props={props} />
        )}
      </div>
    </div>
  )
}
