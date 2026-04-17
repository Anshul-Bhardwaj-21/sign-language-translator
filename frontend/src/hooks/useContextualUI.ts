import { useMemo } from 'react'
import {
  Mic,
  MicOff,
  Video,
  VideoOff,
  Monitor,
  Circle,
  Smile,
  Accessibility,
  MessageSquare,
  Users,
  BookOpen,
  Settings,
  HelpCircle,
  LogOut,
} from 'lucide-react'
import type {
  ToolbarConfig,
  ToolbarButtonConfig,
  UserPreferences,
} from '../types/app'
import type { PanelView } from '../types/app'

export interface UseContextualUIArgs {
  handRaiseActive: boolean
  captionsActive: boolean
  accessibilityMode: boolean
  screenShareActive: boolean
  silenceActive: boolean
  isRecording: boolean
  activePanel: PanelView | null
  preferences: UserPreferences
}

export interface UseContextualUIReturn {
  toolbarConfig: ToolbarConfig
  captionBreathingRoom: boolean
}

export function useContextualUI(args: UseContextualUIArgs): UseContextualUIReturn {
  const {
    handRaiseActive,
    captionsActive,
    accessibilityMode,
    screenShareActive,
    isRecording,
    activePanel,
    preferences,
  } = args

  const toolbarConfig = useMemo<ToolbarConfig>(() => {
    const micButton: ToolbarButtonConfig = {
      id: 'mic',
      label: preferences.micEnabled ? 'Mute' : 'Unmute',
      icon: preferences.micEnabled ? Mic : MicOff,
      active: preferences.micEnabled,
      off: !preferences.micEnabled,
      prominent: false,
      hidden: false,
    }

    const cameraButton: ToolbarButtonConfig = {
      id: 'camera',
      label: preferences.cameraEnabled ? 'Stop Video' : 'Start Video',
      icon: preferences.cameraEnabled ? Video : VideoOff,
      active: preferences.cameraEnabled,
      off: !preferences.cameraEnabled,
      prominent: false,
      hidden: false,
    }

    const shareButton: ToolbarButtonConfig = {
      id: 'share',
      label: screenShareActive ? 'Stop Share' : 'Share Screen',
      icon: Monitor,
      active: screenShareActive,
      off: false,
      prominent: screenShareActive,
      hidden: false,
    }

    const recordButton: ToolbarButtonConfig = {
      id: 'record',
      label: isRecording ? 'Stop Recording' : 'Record',
      icon: Circle,
      active: isRecording,
      off: false,
      prominent: false,
      hidden: false,
    }

    const reactionsButton: ToolbarButtonConfig = {
      id: 'reactions',
      label: 'Reactions',
      icon: Smile,
      active: handRaiseActive,
      off: false,
      prominent: handRaiseActive,
      hidden: false,
    }

    const accessibilityButton: ToolbarButtonConfig = {
      id: 'accessibility',
      label: 'Accessibility',
      icon: Accessibility,
      active: accessibilityMode,
      off: false,
      prominent: accessibilityMode,
      hidden: false,
    }

    const chatButton: ToolbarButtonConfig = {
      id: 'chat',
      label: 'Chat',
      icon: MessageSquare,
      active: activePanel === 'chat',
      off: false,
      prominent: false,
      hidden: false,
    }

    const participantsButton: ToolbarButtonConfig = {
      id: 'participants',
      label: 'Participants',
      icon: Users,
      active: activePanel === 'participants',
      off: false,
      prominent: false,
      hidden: false,
    }

    const assistButton: ToolbarButtonConfig = {
      id: 'assist',
      label: 'Assist',
      icon: BookOpen,
      active: activePanel === 'transcript',
      off: false,
      prominent: false,
      hidden: false,
    }

    const settingsButton: ToolbarButtonConfig = {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      active: false,
      off: false,
      prominent: false,
      hidden: false,
    }

    const helpButton: ToolbarButtonConfig = {
      id: 'help',
      label: 'Help',
      icon: HelpCircle,
      active: false,
      off: false,
      prominent: false,
      hidden: false,
    }

    const leaveButton: ToolbarButtonConfig = {
      id: 'leave',
      label: 'Leave',
      icon: LogOut,
      active: false,
      off: false,
      prominent: false,
      hidden: false,
    }

    // Build primary group: Mic, Camera, Share, Record, Reactions, Accessibility
    // accessibilityMode surfaces Assist into primary group
    const primaryGroup: ToolbarButtonConfig[] = [
      micButton,
      cameraButton,
      shareButton,
      recordButton,
      reactionsButton,
      accessibilityButton,
    ]

    // Build secondary group: Chat, Participants, Assist, Settings, Help, Leave
    // When accessibilityMode is active, Assist moves to primary — hide from secondary
    const assistInPrimary = accessibilityMode
    const secondaryAssist: ToolbarButtonConfig = {
      ...assistButton,
      hidden: assistInPrimary,
    }

    const secondaryGroup: ToolbarButtonConfig[] = [
      chatButton,
      participantsButton,
      secondaryAssist,
      settingsButton,
      helpButton,
      leaveButton,
    ]

    // When accessibilityMode is active, surface Assist in primary group
    if (assistInPrimary) {
      primaryGroup.push({
        ...assistButton,
        prominent: true,
      })
    }

    return {
      primaryGroup,
      secondaryGroup,
      overflowGroup: [],
    }
  }, [
    handRaiseActive,
    accessibilityMode,
    screenShareActive,
    isRecording,
    activePanel,
    preferences.micEnabled,
    preferences.cameraEnabled,
  ])

  const captionBreathingRoom = captionsActive

  return { toolbarConfig, captionBreathingRoom }
}
