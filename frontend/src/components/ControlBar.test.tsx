import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ControlBar from './ControlBar';
import { WebSocketProvider } from '../contexts/WebSocketContext';

// Mock WebSocket context
vi.mock('../contexts/WebSocketContext', () => ({
  WebSocketProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useWebSocket: () => ({
    isConnected: true,
    socket: null,
    sendMessage: vi.fn(),
    subscribe: vi.fn(() => () => {}),
    connect: vi.fn(),
    disconnect: vi.fn(),
  }),
}));

describe('ControlBar Component', () => {
  const defaultProps = {
    meetingId: 'test-meeting-123',
    userId: 'user-123',
    audioEnabled: true,
    videoEnabled: true,
    screenSharing: false,
    handRaised: false,
    onToggleAudio: vi.fn(),
    onToggleVideo: vi.fn(),
    onToggleScreenShare: vi.fn(),
    onToggleHandRaise: vi.fn(),
    onLeaveMeeting: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all control buttons', () => {
    render(
      <WebSocketProvider>
        <ControlBar {...defaultProps} />
      </WebSocketProvider>
    );

    // Check for buttons by their titles
    expect(screen.getByTitle(/mute microphone/i)).toBeInTheDocument();
    expect(screen.getByTitle(/turn off camera/i)).toBeInTheDocument();
    expect(screen.getByTitle(/share screen/i)).toBeInTheDocument();
    expect(screen.getByTitle(/send reaction/i)).toBeInTheDocument();
    expect(screen.getByTitle(/raise hand/i)).toBeInTheDocument();
    expect(screen.getByTitle(/leave meeting/i)).toBeInTheDocument();
  });

  it('calls onToggleAudio when audio button is clicked', () => {
    render(
      <WebSocketProvider>
        <ControlBar {...defaultProps} />
      </WebSocketProvider>
    );

    const audioButton = screen.getByTitle(/mute microphone/i);
    fireEvent.click(audioButton);

    expect(defaultProps.onToggleAudio).toHaveBeenCalledWith(false);
  });

  it('calls onToggleVideo when video button is clicked', () => {
    render(
      <WebSocketProvider>
        <ControlBar {...defaultProps} />
      </WebSocketProvider>
    );

    const videoButton = screen.getByTitle(/turn off camera/i);
    fireEvent.click(videoButton);

    expect(defaultProps.onToggleVideo).toHaveBeenCalledWith(false);
  });

  it('calls onToggleScreenShare when screen share button is clicked', () => {
    render(
      <WebSocketProvider>
        <ControlBar {...defaultProps} />
      </WebSocketProvider>
    );

    const screenShareButton = screen.getByTitle(/share screen/i);
    fireEvent.click(screenShareButton);

    expect(defaultProps.onToggleScreenShare).toHaveBeenCalled();
  });

  it('calls onToggleHandRaise when hand raise button is clicked', () => {
    render(
      <WebSocketProvider>
        <ControlBar {...defaultProps} />
      </WebSocketProvider>
    );

    const handRaiseButton = screen.getByTitle(/raise hand/i);
    fireEvent.click(handRaiseButton);

    expect(defaultProps.onToggleHandRaise).toHaveBeenCalled();
  });

  it('calls onLeaveMeeting when leave button is clicked', () => {
    render(
      <WebSocketProvider>
        <ControlBar {...defaultProps} />
      </WebSocketProvider>
    );

    const leaveButton = screen.getByTitle(/leave meeting/i);
    fireEvent.click(leaveButton);

    expect(defaultProps.onLeaveMeeting).toHaveBeenCalled();
  });

  it('shows reactions picker when reactions button is clicked', () => {
    render(
      <WebSocketProvider>
        <ControlBar {...defaultProps} />
      </WebSocketProvider>
    );

    const reactionsButton = screen.getByTitle(/send reaction/i);
    fireEvent.click(reactionsButton);

    // Check for emoji reactions
    expect(screen.getByText('👍')).toBeInTheDocument();
    expect(screen.getByText('👏')).toBeInTheDocument();
    expect(screen.getByText('❤️')).toBeInTheDocument();
    expect(screen.getByText('🤔')).toBeInTheDocument();
    expect(screen.getByText('😂')).toBeInTheDocument();
  });

  it('displays correct button states when audio is disabled', () => {
    render(
      <WebSocketProvider>
        <ControlBar {...defaultProps} audioEnabled={false} />
      </WebSocketProvider>
    );

    const audioButton = screen.getByTitle(/unmute microphone/i);
    expect(audioButton).toBeInTheDocument();
  });

  it('displays correct button states when video is disabled', () => {
    render(
      <WebSocketProvider>
        <ControlBar {...defaultProps} videoEnabled={false} />
      </WebSocketProvider>
    );

    const videoButton = screen.getByTitle(/turn on camera/i);
    expect(videoButton).toBeInTheDocument();
  });

  it('displays correct button states when screen sharing is active', () => {
    render(
      <WebSocketProvider>
        <ControlBar {...defaultProps} screenSharing={true} />
      </WebSocketProvider>
    );

    const screenShareButton = screen.getByTitle(/stop sharing/i);
    expect(screenShareButton).toBeInTheDocument();
  });

  it('displays correct button states when hand is raised', () => {
    render(
      <WebSocketProvider>
        <ControlBar {...defaultProps} handRaised={true} />
      </WebSocketProvider>
    );

    const handRaiseButton = screen.getByTitle(/lower hand/i);
    expect(handRaiseButton).toBeInTheDocument();
  });
});
