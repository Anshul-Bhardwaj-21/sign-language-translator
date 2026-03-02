/**
 * Preservation Property Tests
 * 
 * **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**
 * 
 * Property 2: Preservation - Non-Camera Functionality
 * 
 * For any functionality that does NOT involve camera video display (error handling, 
 * cleanup, ML processing, UI interactions), the fixed code SHALL produce exactly 
 * the same behavior as the original code.
 * 
 * IMPORTANT: These tests observe behavior on UNFIXED code first, then verify
 * the same behavior is preserved after the fix.
 * 
 * EXPECTED OUTCOME: Tests PASS on unfixed code (confirms baseline behavior)
 * 
 * Test Strategy: Observation-first methodology
 * 1. Run tests on UNFIXED code to observe current behavior
 * 2. Document observed behavior patterns
 * 3. After fix is implemented, re-run to ensure behavior is preserved
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import PreJoinLobby from '../pages/PreJoinLobby';

// Mock API
vi.mock('../services/api', () => ({
  api: {
    createRoom: vi.fn().mockResolvedValue({ room_code: 'TEST123' }),
    validateRoom: vi.fn().mockResolvedValue({ valid: true }),
  },
}));

// Mock AuthContext
vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { id: 'test-user', name: 'Test User' } }),
}));

describe('Preservation Property Tests - Non-Camera Functionality', () => {
  let mockStream: MediaStream;
  let mockVideoTrack: MediaStreamTrack;
  let getUserMediaMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    // Create mock video track
    mockVideoTrack = {
      kind: 'video',
      id: 'mock-video-track',
      label: 'Mock Camera',
      enabled: true,
      muted: false,
      readyState: 'live',
      stop: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    } as unknown as MediaStreamTrack;

    // Create mock MediaStream
    mockStream = {
      id: 'mock-stream',
      active: true,
      getTracks: vi.fn(() => [mockVideoTrack]),
      getVideoTracks: vi.fn(() => [mockVideoTrack]),
      getAudioTracks: vi.fn(() => []),
      addTrack: vi.fn(),
      removeTrack: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    } as unknown as MediaStream;

    // Setup getUserMedia mock
    getUserMediaMock = vi.fn().mockResolvedValue(mockStream);
    if (!globalThis.navigator.mediaDevices) {
      Object.defineProperty(globalThis.navigator, 'mediaDevices', {
        writable: true,
        configurable: true,
        value: {
          getUserMedia: getUserMediaMock,
        },
      });
    } else {
      globalThis.navigator.mediaDevices.getUserMedia = getUserMediaMock;
    }

    // Mock HTMLVideoElement.prototype.play
    HTMLVideoElement.prototype.play = vi.fn().mockResolvedValue(undefined);
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  /**
   * Test Case 1: Camera Permission Denied Error Handling
   * 
   * **Validates: Requirement 3.6**
   * 
   * PRESERVATION: When camera permissions are denied, the system SHALL display
   * appropriate error messages without breaking the UI.
   * 
   * Observed Behavior on UNFIXED code:
   * - getUserMedia throws NotAllowedError
   * - Error message is displayed: "Camera access denied. Please allow camera permissions and try again."
   * - UI remains functional (no crash)
   * - Camera preview state is set to false
   * - Error is shown in yellow warning box
   */
  it('PRESERVATION: Camera permission denied error handling', async () => {
    const user = userEvent.setup();
    
    // Mock permission denied error
    const permissionError = new Error('Permission denied');
    permissionError.name = 'NotAllowedError';
    getUserMediaMock.mockRejectedValueOnce(permissionError);

    render(
      <BrowserRouter>
        <PreJoinLobby />
      </BrowserRouter>
    );

    // Click camera toggle button
    const cameraButton = screen.getByRole('button', { name: /turn on camera preview/i });
    await user.click(cameraButton);

    // Wait for error to be displayed
    await waitFor(() => {
      const errorMessage = screen.getByText(/camera access denied/i);
      expect(errorMessage).toBeTruthy();
    });

    // Verify error message content
    expect(screen.getByText(/please allow camera permissions and try again/i)).toBeTruthy();

    // Verify camera preview is NOT granted
    expect(screen.getByRole('button', { name: /turn on camera preview/i })).toBeTruthy();

    // Verify UI is still functional (button is clickable)
    expect(cameraButton).not.toBeDisabled();
  });

  /**
   * Test Case 2: Camera Not Found Error Handling
   * 
   * **Validates: Requirement 3.6**
   * 
   * PRESERVATION: When no camera is found, the system SHALL display appropriate
   * error messages without breaking the UI.
   * 
   * Observed Behavior on UNFIXED code:
   * - getUserMedia throws NotFoundError
   * - Error message is displayed: "No camera found. Please connect a camera device."
   * - UI remains functional
   */
  it('PRESERVATION: Camera not found error handling', async () => {
    const user = userEvent.setup();
    
    // Mock camera not found error
    const notFoundError = new Error('No camera found');
    notFoundError.name = 'NotFoundError';
    getUserMediaMock.mockRejectedValueOnce(notFoundError);

    render(
      <BrowserRouter>
        <PreJoinLobby />
      </BrowserRouter>
    );

    const cameraButton = screen.getByRole('button', { name: /turn on camera preview/i });
    await user.click(cameraButton);

    await waitFor(() => {
      const errorMessage = screen.getByText(/no camera found/i);
      expect(errorMessage).toBeTruthy();
    });

    expect(screen.getByText(/please connect a camera device/i)).toBeTruthy();
    expect(cameraButton).not.toBeDisabled();
  });

  /**
   * Test Case 3: Camera In Use Error Handling
   * 
   * **Validates: Requirement 3.6**
   * 
   * PRESERVATION: When camera is in use by another application, the system SHALL
   * display appropriate error messages without breaking the UI.
   * 
   * Observed Behavior on UNFIXED code:
   * - getUserMedia throws NotReadableError
   * - Error message is displayed: "Camera is in use by another application..."
   * - UI remains functional
   */
  it('PRESERVATION: Camera in use error handling', async () => {
    const user = userEvent.setup();
    
    // Mock camera in use error
    const inUseError = new Error('Camera in use');
    inUseError.name = 'NotReadableError';
    getUserMediaMock.mockRejectedValueOnce(inUseError);

    render(
      <BrowserRouter>
        <PreJoinLobby />
      </BrowserRouter>
    );

    const cameraButton = screen.getByRole('button', { name: /turn on camera preview/i });
    await user.click(cameraButton);

    await waitFor(() => {
      const errorMessage = screen.getByText(/camera is in use by another application/i);
      expect(errorMessage).toBeTruthy();
    });

    expect(screen.getByText(/please close other apps using the camera/i)).toBeTruthy();
    expect(cameraButton).not.toBeDisabled();
  });

  /**
   * Test Case 4: Camera Cleanup on Disable
   * 
   * **Validates: Requirement 3.2**
   * 
   * PRESERVATION: When a user toggles the camera off, the system SHALL properly
   * stop all media tracks and clean up resources.
   * 
   * Observed Behavior on UNFIXED code:
   * - Camera is enabled successfully
   * - User clicks to disable camera
   * - stream.getTracks().forEach(track => track.stop()) is called
   * - Camera preview state is set to false
   * - Video element is cleared
   */
  it('PRESERVATION: Camera cleanup on disable', async () => {
    const user = userEvent.setup();
    
    render(
      <BrowserRouter>
        <PreJoinLobby />
      </BrowserRouter>
    );

    // Enable camera
    const cameraButton = screen.getByRole('button', { name: /turn on camera preview/i });
    await user.click(cameraButton);

    await waitFor(() => {
      expect(getUserMediaMock).toHaveBeenCalled();
    });

    // Wait for camera to be enabled
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /turn off camera preview/i })).toBeTruthy();
    });

    // Disable camera
    const disableButton = screen.getByRole('button', { name: /turn off camera preview/i });
    await user.click(disableButton);

    // Verify track.stop() was called
    await waitFor(() => {
      expect(mockVideoTrack.stop).toHaveBeenCalled();
    });

    // Verify camera preview is off
    expect(screen.getByRole('button', { name: /turn on camera preview/i })).toBeTruthy();
    expect(screen.getByText(/camera preview off/i)).toBeTruthy();
  });

  /**
   * Test Case 5: Input Validation for Room Code
   * 
   * **Validates: Requirement 3.3**
   * 
   * PRESERVATION: When a user fills in room code and display name, the system
   * SHALL validate inputs and enable the join button appropriately.
   * 
   * Observed Behavior on UNFIXED code:
   * - Room code must be at least 3 characters
   * - Display name must be at least 1 character
   * - Join button is disabled until both are valid
   * - Error message shown for invalid room code
   */
  it('PRESERVATION: Input validation for room code and display name', async () => {
    const user = userEvent.setup();
    
    render(
      <BrowserRouter>
        <PreJoinLobby />
      </BrowserRouter>
    );

    const joinButton = screen.getByRole('button', { name: /join meeting/i });
    const roomCodeInput = screen.getByLabelText(/room code/i);
    const displayNameInput = screen.getByLabelText(/your name/i);

    // Initially, join button should be disabled (no room code)
    expect(joinButton).toBeDisabled();

    // Enter invalid room code (too short)
    await user.clear(roomCodeInput);
    await user.type(roomCodeInput, 'AB');

    // Verify error message
    await waitFor(() => {
      expect(screen.getByText(/room code must be at least 3 characters/i)).toBeTruthy();
    });

    // Join button should still be disabled
    expect(joinButton).toBeDisabled();

    // Enter valid room code
    await user.clear(roomCodeInput);
    await user.type(roomCodeInput, 'ABC123');

    // Enter valid display name
    await user.clear(displayNameInput);
    await user.type(displayNameInput, 'John Doe');

    // Join button should now be enabled
    await waitFor(() => {
      expect(joinButton).not.toBeDisabled();
    });
  });

  /**
   * Test Case 6: Accessibility Mode Toggle
   * 
   * **Validates: Requirement 3.4**
   * 
   * PRESERVATION: When a user enables accessibility mode, the system SHALL store
   * and pass this preference to the video call page.
   * 
   * Observed Behavior on UNFIXED code:
   * - Checkbox can be toggled on/off
   * - Icon changes color when enabled (purple)
   * - State is stored for navigation
   */
  it('PRESERVATION: Accessibility mode toggle', async () => {
    const user = userEvent.setup();
    
    render(
      <BrowserRouter>
        <PreJoinLobby />
      </BrowserRouter>
    );

    // Find accessibility checkbox
    const accessibilityCheckbox = screen.getByRole('checkbox', { name: /sign language mode/i });

    // Initially unchecked
    expect(accessibilityCheckbox).not.toBeChecked();

    // Toggle on
    await user.click(accessibilityCheckbox);

    // Verify checked
    await waitFor(() => {
      expect(accessibilityCheckbox).toBeChecked();
    });

    // Toggle off
    await user.click(accessibilityCheckbox);

    // Verify unchecked
    await waitFor(() => {
      expect(accessibilityCheckbox).not.toBeChecked();
    });
  });

  /**
   * Test Case 7: UI Interactions - Button Clicks
   * 
   * **Validates: Requirement 3.3**
   * 
   * PRESERVATION: UI interactions (buttons, toggles, navigation) must continue
   * to work correctly.
   * 
   * Observed Behavior on UNFIXED code:
   * - Buttons are clickable
   * - Loading states are shown
   * - Disabled states work correctly
   */
  it('PRESERVATION: UI interactions - button clicks and states', async () => {
    const user = userEvent.setup();
    
    render(
      <BrowserRouter>
        <PreJoinLobby />
      </BrowserRouter>
    );

    // Test camera button click
    const cameraButton = screen.getByRole('button', { name: /turn on camera preview/i });
    expect(cameraButton).not.toBeDisabled();
    
    await user.click(cameraButton);

    // Verify getUserMedia was called (button worked)
    await waitFor(() => {
      expect(getUserMediaMock).toHaveBeenCalled();
    });

    // Test create room button
    const createRoomButton = screen.getByRole('button', { name: /generate new room code/i });
    expect(createRoomButton).not.toBeDisabled();
  });

  /**
   * Test Case 8: Component Unmount Cleanup
   * 
   * **Validates: Requirement 3.5**
   * 
   * PRESERVATION: When user navigates away, the system SHALL properly clean up
   * camera streams and stop all tracks.
   * 
   * Observed Behavior on UNFIXED code:
   * - useEffect cleanup function is called on unmount
   * - All tracks are stopped
   * - No memory leaks
   */
  it('PRESERVATION: Component unmount cleanup', async () => {
    const user = userEvent.setup();
    
    const { unmount } = render(
      <BrowserRouter>
        <PreJoinLobby />
      </BrowserRouter>
    );

    // Enable camera
    const cameraButton = screen.getByRole('button', { name: /turn on camera preview/i });
    await user.click(cameraButton);

    await waitFor(() => {
      expect(getUserMediaMock).toHaveBeenCalled();
    });

    // Unmount component (simulates navigation away)
    unmount();

    // Verify track.stop() was called during cleanup
    await waitFor(() => {
      expect(mockVideoTrack.stop).toHaveBeenCalled();
    });
  });

  /**
   * Test Case 9: Error Recovery - Retry After Error
   * 
   * **Validates: Requirement 3.6**
   * 
   * PRESERVATION: After an error, user should be able to retry camera access.
   * 
   * Observed Behavior on UNFIXED code:
   * - Error is displayed
   * - Button remains clickable
   * - User can retry
   * - Second attempt can succeed
   */
  it('PRESERVATION: Error recovery - retry after permission denied', async () => {
    const user = userEvent.setup();
    
    // First attempt: permission denied
    const permissionError = new Error('Permission denied');
    permissionError.name = 'NotAllowedError';
    getUserMediaMock.mockRejectedValueOnce(permissionError);

    render(
      <BrowserRouter>
        <PreJoinLobby />
      </BrowserRouter>
    );

    const cameraButton = screen.getByRole('button', { name: /turn on camera preview/i });
    await user.click(cameraButton);

    // Wait for error
    await waitFor(() => {
      expect(screen.getByText(/camera access denied/i)).toBeTruthy();
    });

    // Second attempt: success
    getUserMediaMock.mockResolvedValueOnce(mockStream);
    await user.click(cameraButton);

    // Verify second attempt was made
    await waitFor(() => {
      expect(getUserMediaMock).toHaveBeenCalledTimes(2);
    });
  });

  /**
   * Test Case 10: Multiple Rapid Toggles - State Consistency
   * 
   * **Validates: Requirements 3.2, 3.6**
   * 
   * PRESERVATION: When toggling camera multiple times, state should remain consistent.
   * 
   * Observed Behavior on UNFIXED code:
   * - Each toggle properly starts or stops camera
   * - Cleanup happens on each disable
   * - No state corruption
   */
  it('PRESERVATION: Multiple rapid toggles maintain state consistency', async () => {
    const user = userEvent.setup();
    
    render(
      <BrowserRouter>
        <PreJoinLobby />
      </BrowserRouter>
    );

    // Toggle ON
    let cameraButton = screen.getByRole('button', { name: /turn on camera preview/i });
    await user.click(cameraButton);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /turn off camera preview/i })).toBeTruthy();
    });

    // Toggle OFF
    cameraButton = screen.getByRole('button', { name: /turn off camera preview/i });
    await user.click(cameraButton);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /turn on camera preview/i })).toBeTruthy();
    });

    // Toggle ON again
    cameraButton = screen.getByRole('button', { name: /turn on camera preview/i });
    await user.click(cameraButton);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /turn off camera preview/i })).toBeTruthy();
    });

    // Verify cleanup was called on each disable
    expect(mockVideoTrack.stop).toHaveBeenCalled();
  });
});
