/**
 * Integration smoke test for MeetingShellPage
 * Validates: Requirements 2.1–2.9
 *
 * Renders MeetingShellPage with all hooks mocked; asserts no crash and key elements present.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

// ── Mock react-router-dom ─────────────────────────────────────────────────────
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>()
  return {
    ...actual,
    useParams: () => ({ roomId: 'test-room' }),
    useNavigate: () => vi.fn(),
  }
})

// ── Mock AppContext ────────────────────────────────────────────────────────────
vi.mock('../../contexts/AppContext', () => ({
  useAppContext: () => ({
    user: {
      id: 'user-1',
      displayName: 'Test User',
      email: 'test@example.com',
      isGuest: false,
    },
    preferences: {
      cameraEnabled: true,
      micEnabled: true,
      translationEnabled: true,
      accessibilityMode: false,
      showVisionOverlay: false,
      autoSpeakCaptions: false,
      captureIntervalMs: 1200,
      preferredLayout: 'grid',
    },
    updatePreferences: vi.fn(),
    rememberRoom: vi.fn(),
    recentRooms: [],
    login: vi.fn(),
    logout: vi.fn(),
  }),
}))

// ── Mock useNetworkStatus ─────────────────────────────────────────────────────
vi.mock('../../hooks/useNetworkStatus', () => ({
  useNetworkStatus: () => ({ online: true, effectiveType: '4g' }),
}))

// ── Mock useMeetingShell ──────────────────────────────────────────────────────
vi.mock('../../hooks/useMeetingShell', () => ({
  useMeetingShell: () => ({
    room: null,
    localStream: null,
    localVideoRef: { current: null },
    remoteStreams: {},
    chatMessages: [],
    captionMessages: [],
    latestCaption: '',
    latestPrediction: null,
    connectionStatus: 'connected',
    peerStates: {},
    otherParticipants: [],
    loading: false,
    error: null,
    dismissError: vi.fn(),
    shellState: {
      activePanel: null,
      showSettingsModal: false,
      showShortcutsModal: false,
      showInfoPanel: false,
      showReactionPicker: false,
      controlsVisible: true,
      pinnedParticipantId: null,
      raisedHandIds: {},
      reactionBursts: [],
      chatPreview: null,
      meetingSeconds: 0,
      documentHidden: false,
    },
    setShellState: vi.fn(),
    toasts: [],
    pushToast: vi.fn(),
    dismissToast: vi.fn(),
    audioLevelMap: {},
    activeSpeakerId: null,
    presenceDepthMap: {},
    layout: 'grid',
    spotlightId: null,
    mode: 'auto',
    lockLayout: vi.fn(),
    unlockLayout: vi.fn(),
    silenceState: { isSilent: false, silenceDurationSeconds: 0, lastActivityMs: 0 },
    resetSilence: vi.fn(),
    toolbarConfig: { primaryGroup: [], secondaryGroup: [], overflowGroup: [] },
    captionBreathingRoom: false,
    attentionState: { participants: {}, localSilenceDurationMs: 0, showSilenceNudge: false },
    dismissSilenceNudge: vi.fn(),
    recordHighlight: vi.fn(),
    searchHighlights: vi.fn(() => []),
    generateSummary: vi.fn(() => ''),
    highlights: [],
    summary: null,
    syncHighlights: vi.fn(),
    isRecording: false,
    recordingDurationMs: 0,
    participantCount: 1,
    screenShareParticipantId: null,
    handRaiseActive: false,
    togglePanel: vi.fn(),
    revealControls: vi.fn(),
    handleReactionSelect: vi.fn(),
    handleRecordingToggle: vi.fn(),
    handleLeave: vi.fn(),
    pinParticipant: vi.fn(),
    unpinParticipant: vi.fn(),
    sendChat: vi.fn(),
    clearCaptions: vi.fn(),
    updatePreferences: vi.fn(),
  }),
}))

import { MeetingShellPage } from '../MeetingShellPage'

describe('MeetingShellPage smoke test', () => {
  beforeEach(() => {
    // Stub browser APIs that jsdom doesn't provide
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockReturnValue({
        matches: false,
        media: '',
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }),
    })

    Object.defineProperty(window, 'speechSynthesis', {
      writable: true,
      value: { cancel: vi.fn(), speak: vi.fn() },
    })
  })

  it('renders without crashing', () => {
    expect(() =>
      render(
        <MemoryRouter initialEntries={['/room/test-room/premium']}>
          <MeetingShellPage />
        </MemoryRouter>,
      ),
    ).not.toThrow()
  })

  it('renders the <main> element', () => {
    render(
      <MemoryRouter initialEntries={['/room/test-room/premium']}>
        <MeetingShellPage />
      </MemoryRouter>,
    )
    expect(screen.getByRole('main')).toBeInTheDocument()
  })
})
