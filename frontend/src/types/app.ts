export type ConnectionStatus = 'connecting' | 'connected' | 'reconnecting' | 'disconnected' | 'error'
export type MeetingLayout = 'focus' | 'grid'
export type PanelView = 'participants' | 'chat' | 'transcript' | 'translation'
export type PermissionState = 'prompt' | 'granted' | 'denied' | 'unsupported'

export interface AppUser {
  id: string
  displayName: string
  email?: string
  isGuest: boolean
}

export interface UserPreferences {
  cameraEnabled: boolean
  micEnabled: boolean
  translationEnabled: boolean
  accessibilityMode: boolean
  showVisionOverlay: boolean
  autoSpeakCaptions: boolean
  captureIntervalMs: number
  preferredCameraId?: string
  preferredMicId?: string
  preferredSpeakerId?: string
  preferredLayout: MeetingLayout
}

export interface RecentRoom {
  roomId: string
  roomName: string
  lastJoinedAt: string
}

export interface HealthSnapshot {
  service: string
  version: string
  environment: string
  engine: string
  engine_ready: boolean
  rooms_active: number
  connected_participants: number
  uptime_seconds: number
}

export interface ParticipantSnapshot {
  participant_id: string
  display_name: string
  role: string
  joined_at: string
  connected: boolean
  mic_enabled: boolean
  camera_enabled: boolean
}

export interface RoomSnapshot {
  room_id: string
  room_name: string
  accessibility_mode: boolean
  max_participants: number
  created_at: string
  participants: ParticipantSnapshot[]
  recent_chat: ChatMessage[]
  recent_captions: CaptionMessage[]
}

export interface PredictionQuality {
  passed: boolean
  reason: string
  blur_score: number
  luminance: number
  detection_confidence: number
}

export interface OverlayPoint {
  x: number
  y: number
  z: number
}

export interface OverlayBounds {
  x_min: number
  y_min: number
  x_max: number
  y_max: number
}

export interface PredictionOverlay {
  hand_landmarks: OverlayPoint[]
  hand_bounds?: OverlayBounds | null
  guidance_mode: string
  show_face_frame_guide: boolean
}

export interface PredictionSnapshot {
  label: string
  confidence: number
  engine: string
  engine_ready: boolean
  fallback_used: boolean
  hand_detected: boolean
  handedness?: string | null
  live_caption: string
  confirmed_caption?: string | null
  caption_history: string[]
  quality: PredictionQuality
  overlay?: PredictionOverlay | null
  diagnostics: Record<string, string | number | boolean | null>
}

export interface ChatMessage {
  participant_id: string
  display_name: string
  message: string
  timestamp: string
}

export interface CaptionMessage {
  participant_id: string
  display_name: string
  caption: string
  confidence: string
  timestamp: string
}

export interface RealtimeEvent {
  type: string
  payload: Record<string, unknown>
}

export interface DeviceOption {
  deviceId: string
  label: string
}

// --- Premium Video Meeting UI types ---

import type { RefObject, ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'

// Layout and Smart Layout
export type SmartLayoutMode = 'auto' | 'locked'

export interface SmartLayoutState {
  layout: MeetingLayout
  spotlightId: string | null
  mode: SmartLayoutMode
  preShareLayout: MeetingLayout | null
}

// Presence Depth
export interface PresenceDepthStyle {
  glowIntensity: number
  scale: number
  isActiveSpeaker: boolean
}

// Contextual UI
export interface ContextualUIState {
  handRaiseActive: boolean
  captionsActive: boolean
  accessibilityMode: boolean
  screenShareActive: boolean
  silenceActive: boolean
}

// AI Meeting Memory
export interface MeetingHighlight {
  id: string
  type: 'screenShare' | 'handRaise' | 'reactionBurst' | 'silenceBreak' | 'sessionStart' | 'sessionEnd'
  participantId?: string
  participantName?: string
  timestampMs: number
  wallTime: string
  label: string
}

export interface MeetingMemoryState {
  sessionStartMs: number
  highlights: MeetingHighlight[]
  summary: string | null
}

// Attention Intelligence
export interface ParticipantAttentionState {
  participantId: string
  lastSpokeMs: number
  silenceDurationMs: number
  cameraActive: boolean
  audioActive: boolean
  isInactive: boolean
}

export interface AttentionState {
  participants: Record<string, ParticipantAttentionState>
  localSilenceDurationMs: number
  showSilenceNudge: boolean
}

// Silence Detection
export interface SilenceDetectionConfig {
  thresholdSeconds: number
  audioThreshold: number
}

export interface SilenceDetectionState {
  isSilent: boolean
  silenceDurationSeconds: number
  lastActivityMs: number
}

// Reaction
export interface ReactionBurst {
  id: string
  emoji: string
  participantId: string
}

// Chat Preview
export interface ChatPreviewBubble {
  id: string
  participantId: string
  displayName: string
  message: string
}

// Meeting Shell
export interface MeetingShellState {
  activePanel: PanelView | null
  showSettingsModal: boolean
  showShortcutsModal: boolean
  showInfoPanel: boolean
  showReactionPicker: boolean
  controlsVisible: boolean
  pinnedParticipantId: string | null
  raisedHandIds: Record<string, boolean>
  reactionBursts: ReactionBurst[]
  chatPreview: ChatPreviewBubble | null
  meetingSeconds: number
  documentHidden: boolean
}

// Tile configs
export interface LocalTileConfig {
  stream: MediaStream | null
  videoRef: RefObject<HTMLVideoElement>
  micEnabled: boolean
  cameraEnabled: boolean
  isRecording: boolean
  recordingDurationMs: number
  accessibilityMode: boolean
  showVisionOverlay: boolean
  latestPrediction: PredictionSnapshot | null
  raisedHand: boolean
  reactionBursts: ReactionBurst[]
  chatPreview: ChatPreviewBubble | null
}

export interface RemoteTileConfig {
  participantId: string
  displayName: string
  role: string
  peerState: string
  stream: MediaStream | null
  micEnabled: boolean
  cameraEnabled: boolean
  raisedHand: boolean
  reactionBursts: ReactionBurst[]
  chatPreview: ChatPreviewBubble | null
  presenceDepth: PresenceDepthStyle
  audioOutputId?: string
}

export interface MeetingVideoGridProps {
  layout: MeetingLayout
  localTile: LocalTileConfig
  remoteTiles: RemoteTileConfig[]
  pinnedParticipantId: string | null
  presenceDepthMap: Record<string, PresenceDepthStyle>
  onPinParticipant: (id: string) => void
  onUnpinParticipant: () => void
}

// Toolbar
export interface ToolbarButtonConfig {
  id: string
  label: string
  icon: LucideIcon
  active: boolean
  off: boolean
  prominent: boolean
  hidden: boolean
}

export interface ToolbarConfig {
  primaryGroup: ToolbarButtonConfig[]
  secondaryGroup: ToolbarButtonConfig[]
  overflowGroup: ToolbarButtonConfig[]
}

// Silence Suggestion
export interface SilenceSuggestion {
  id: string
  label: string
  action: 'startRecording' | 'shareScreen' | 'addNote' | 'openChat'
}

// Glass Panel
export interface GlassPanelProps {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
  fullscreenOnMobile?: boolean
}

// MeetingFloatingToolbar
export interface MeetingFloatingToolbarProps {
  visible: boolean
  preferences: UserPreferences
  isRecording: boolean
  activePanel: PanelView | null
  showReactionPicker: boolean
  toolbarConfig: ToolbarConfig
  onToggleMic: () => void
  onToggleCamera: () => void
  onToggleRecording: () => void
  onToggleAccessibility: () => void
  onTogglePanel: (panel: PanelView) => void
  onToggleReactionPicker: () => void
  onOpenSettings: () => void
  onOpenShortcuts: () => void
  onOpenInfo: () => void
  onLeave: () => void
  onScreenShare: () => void
  onReactionSelect?: (emoji: string) => void
}
