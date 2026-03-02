/**
 * Bug Condition Exploration Test
 * 
 * **Validates: Requirements 2.1, 2.2, 2.4, 2.5**
 * 
 * CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists
 * 
 * Property 1: Fault Condition - Camera Feed Display
 * 
 * For any camera state where the camera is enabled and a MediaStream is successfully 
 * obtained from getUserMedia, the video element SHALL display the live camera feed 
 * with proper video rendering, ensuring the video element has correct attributes 
 * (autoPlay, playsInline, muted) and the play() method is called after the stream is ready.
 * 
 * This test encodes the EXPECTED behavior. When it passes after the fix, 
 * it confirms the bug is resolved.
 * 
 * SCOPED PBT APPROACH: Testing concrete failing cases - camera enabled with valid 
 * MediaStream but video shows black screen due to timing issues.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup, act } from '@testing-library/react';
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

describe('Bug Condition Exploration - Camera Black Screen', () => {
  let mockStream: MediaStream;
  let mockVideoTrack: MediaStreamTrack;
  let getUserMediaMock: ReturnType<typeof vi.fn>;
  let loadedMetadataCallbacks: Array<() => void> = [];

  beforeEach(() => {
    // Reset callbacks
    loadedMetadataCallbacks = [];

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
    if (!global.navigator.mediaDevices) {
      Object.defineProperty(global.navigator, 'mediaDevices', {
        writable: true,
        configurable: true,
        value: {
          getUserMedia: getUserMediaMock,
        },
      });
    } else {
      global.navigator.mediaDevices.getUserMedia = getUserMediaMock;
    }

    // Mock HTMLVideoElement.prototype.play to always resolve
    HTMLVideoElement.prototype.play = vi.fn().mockResolvedValue(undefined);

    // Track loadedmetadata event listeners (both addEventListener and onloadedmetadata property)
    const originalAddEventListener = HTMLVideoElement.prototype.addEventListener;
    const videoElements: HTMLVideoElement[] = [];
    const onloadedmetadataCallbacks = new WeakMap<HTMLVideoElement, EventListener>();
    
    HTMLVideoElement.prototype.addEventListener = vi.fn(function(
      this: HTMLVideoElement,
      type: string,
      listener: any,
      options?: any
    ) {
      if (type === 'loadedmetadata') {
        loadedMetadataCallbacks.push(listener.bind(this));
      }
      if (!videoElements.includes(this)) {
        videoElements.push(this);
      }
      return originalAddEventListener.call(this, type, listener, options);
    });
    
    // Intercept onloadedmetadata property setter
    Object.defineProperty(HTMLVideoElement.prototype, 'onloadedmetadata', {
      set: function(this: HTMLVideoElement, callback) {
        if (callback) {
          onloadedmetadataCallbacks.set(this, callback);
          loadedMetadataCallbacks.push(callback.bind(this));
        }
        if (!videoElements.includes(this)) {
          videoElements.push(this);
        }
      },
      get: function(this: HTMLVideoElement) {
        return onloadedmetadataCallbacks.get(this) || null;
      },
      configurable: true
    });
    
    // Intercept srcObject setter to automatically trigger loadedmetadata event
    const originalSrcObjectDescriptor = Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype, 'srcObject');
    Object.defineProperty(HTMLVideoElement.prototype, 'srcObject', {
      set: function(this: HTMLVideoElement, stream: MediaStream | null) {
        // Call original setter if it exists
        if (originalSrcObjectDescriptor && originalSrcObjectDescriptor.set) {
          originalSrcObjectDescriptor.set.call(this, stream);
        } else {
          (this as any)._srcObject = stream;
        }
        
        // Automatically trigger loadedmetadata event after srcObject is set
        if (stream) {
          // Use queueMicrotask to ensure onloadedmetadata is set first (it's set after srcObject in the code)
          queueMicrotask(() => {
            const callback = onloadedmetadataCallbacks.get(this);
            if (callback) {
              try {
                // Call the callback directly (it's the resolve function from the promise)
                callback.call(this, { type: 'loadedmetadata', target: this } as Event);
              } catch (e) {
                // Ignore errors
              }
            }
          });
        }
      },
      get: function(this: HTMLVideoElement) {
        if (originalSrcObjectDescriptor && originalSrcObjectDescriptor.get) {
          return originalSrcObjectDescriptor.get.call(this);
        }
        return (this as any)._srcObject || null;
      },
      configurable: true
    });
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  /**
   * Test Case 1: PreJoinLobby Camera Enable - Async Timing Issue
   * 
   * EXPECTED FAILURE: play() is called before 'loadedmetadata' event fires
   * 
   * Bug Condition: camera enabled + MediaStream obtained + play() called too early
   * 
   * This is the CORE bug: the unfixed code calls play() immediately after setting
   * srcObject, without waiting for the video element to be ready (loadedmetadata event).
   */
  it('EXPECTED FAILURE: play() called before loadedmetadata event', async () => {
    const user = userEvent.setup();
    
    let playCalledBeforeMetadata = false;
    let metadataFired = false;

    // Override play() to check timing
    HTMLVideoElement.prototype.play = vi.fn(function(this: HTMLVideoElement) {
      if (!metadataFired) {
        playCalledBeforeMetadata = true;
      }
      return Promise.resolve();
    });

    render(
      <BrowserRouter>
        <PreJoinLobby />
      </BrowserRouter>
    );

    // Click camera toggle button
    const cameraButton = screen.getByRole('button', { name: /turn on camera preview/i });
    await user.click(cameraButton);

    // Wait for getUserMedia to be called
    await waitFor(() => {
      expect(getUserMediaMock).toHaveBeenCalled();
    });

    // Simulate metadata loaded after a delay (realistic scenario)
    setTimeout(() => {
      metadataFired = true;
      loadedMetadataCallbacks.forEach(cb => {
        // Call with a mock event object to avoid React errors
        try {
          cb({ type: 'loadedmetadata', target: {} } as Event);
        } catch (e) {
          // Ignore errors from event handling
        }
      });
    }, 50);

    // Wait a bit for play() to be called
    await new Promise(resolve => setTimeout(resolve, 100));

    // EXPECTED FAILURE: The unfixed code calls play() before loadedmetadata fires
    // This causes the black screen bug because the video element is not ready
    expect(playCalledBeforeMetadata).toBe(false);
  });

  /**
   * Test Case 2: Missing loadedmetadata Event Listener
   * 
   * EXPECTED FAILURE: No loadedmetadata listener is added before play()
   * 
   * The unfixed code does NOT wait for the video to be ready before calling play().
   */
  it('EXPECTED FAILURE: loadedmetadata listener not added before play()', async () => {
    const user = userEvent.setup();
    
    render(
      <BrowserRouter>
        <PreJoinLobby />
      </BrowserRouter>
    );

    const cameraButton = screen.getByRole('button', { name: /turn on camera preview/i });
    await user.click(cameraButton);

    await waitFor(() => {
      expect(getUserMediaMock).toHaveBeenCalled();
    });

    // Wait for video element to be created and srcObject to be set
    await waitFor(() => {
      const videoElement = document.querySelector('video');
      expect(videoElement).toBeTruthy();
    });

    // EXPECTED FAILURE: The unfixed code does NOT add a loadedmetadata listener
    // This means it doesn't wait for the video to be ready before calling play()
    expect(loadedMetadataCallbacks.length).toBeGreaterThan(0);
  });

  /**
   * Test Case 3: Play Promise Rejection Not Handled
   * 
   * EXPECTED FAILURE: play() promise rejection is not caught
   * 
   * When play() fails (e.g., NotAllowedError), the unfixed code doesn't handle it.
   */
  it('EXPECTED FAILURE: play() promise rejection not handled', async () => {
    // Mock play() to reject BEFORE rendering
    const playError = new Error('NotAllowedError: play() failed');
    playError.name = 'NotAllowedError';
    const playMock = vi.fn(() => Promise.reject(playError));
    HTMLVideoElement.prototype.play = playMock;

    // Spy on console.error to check if error is logged
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <PreJoinLobby />
      </BrowserRouter>
    );

    const cameraButton = screen.getByRole('button', { name: /turn on camera preview/i });
    await user.click(cameraButton);

    await waitFor(() => {
      expect(getUserMediaMock).toHaveBeenCalled();
    });

    // Wait for play() to be called (srcObject setter will auto-trigger onloadedmetadata)
    await waitFor(() => {
      expect(playMock).toHaveBeenCalled();
    }, { timeout: 2000 });

    // Give time for error handling to complete
    await new Promise(resolve => setTimeout(resolve, 200));

    // Check if error was logged
    const errorLogged = consoleErrorSpy.mock.calls.some(call => 
      call.some(arg => {
        if (typeof arg === 'string') {
          return arg.toLowerCase().includes('play') || arg.includes('NotAllowed');
        }
        if (arg instanceof Error) {
          return arg.message.includes('play') || arg.name === 'NotAllowedError';
        }
        return false;
      })
    );
    
    // Check if error was displayed to user
    const errorDisplayed = screen.queryByText(/camera access denied/i) !== null ||
                          screen.queryByText(/could not.*camera/i) !== null ||
                          screen.queryByText(/play.*failed/i) !== null ||
                          screen.queryByText(/video playback not allowed/i) !== null ||
                          screen.queryByText(/please check browser permissions/i) !== null;

    consoleErrorSpy.mockRestore();

    // EXPECTED FAILURE: The unfixed code does NOT handle play() errors
    // Neither error display nor logging happens
    expect(errorDisplayed || errorLogged).toBe(true);
  });

  /**
   * Test Case 4: Concurrent Initialization Not Prevented
   * 
   * EXPECTED FAILURE: Multiple rapid clicks cause concurrent getUserMedia calls
   * 
   * The unfixed code lacks an initialization lock (initializingRef).
   */
  it('EXPECTED FAILURE: concurrent initialization not prevented', async () => {
    const user = userEvent.setup();
    
    // Make getUserMedia slow to expose race conditions
    let getUserMediaCallCount = 0;
    getUserMediaMock.mockImplementation(() => {
      getUserMediaCallCount++;
      return new Promise(resolve => {
        setTimeout(() => resolve(mockStream), 200);
      });
    });

    render(
      <BrowserRouter>
        <PreJoinLobby />
      </BrowserRouter>
    );

    const cameraButton = screen.getByRole('button', { name: /turn on camera preview/i });

    // Click multiple times rapidly (before first call completes)
    await user.click(cameraButton);
    await user.click(cameraButton);
    await user.click(cameraButton);

    // Wait for operations to complete
    await new Promise(resolve => setTimeout(resolve, 500));

    // EXPECTED FAILURE: Without initialization lock, getUserMedia is called multiple times
    // The fixed code should have initializingRef to prevent this
    // With proper locking, only 1 call should happen
    expect(getUserMediaCallCount).toBe(1);
  });

  /**
   * Test Case 5: Video Element Attributes Check
   * 
   * This test verifies that video element has correct attributes.
   * This part should PASS even on unfixed code (attributes are set correctly).
   */
  it('Video element has correct attributes (should pass)', async () => {
    const user = userEvent.setup();
    
    render(
      <BrowserRouter>
        <PreJoinLobby />
      </BrowserRouter>
    );

    const cameraButton = screen.getByRole('button', { name: /turn on camera preview/i });
    await user.click(cameraButton);

    await waitFor(() => {
      expect(getUserMediaMock).toHaveBeenCalled();
    });

    // Wait for video element
    await waitFor(() => {
      const videoElement = document.querySelector('video');
      expect(videoElement).toBeTruthy();
    });

    const videoElement = document.querySelector('video') as HTMLVideoElement;

    // These attributes should be set correctly even in unfixed code
    expect(videoElement.autoplay).toBe(true);
    expect(videoElement.playsInline).toBe(true);
    expect(videoElement.muted).toBe(true);
  });

  /**
   * Test Case 6: MediaStream Track State Check
   * 
   * Verifies that MediaStream tracks are in 'live' state.
   * This should PASS even on unfixed code (tracks are live).
   */
  it('MediaStream tracks are live (should pass)', async () => {
    const user = userEvent.setup();
    
    render(
      <BrowserRouter>
        <PreJoinLobby />
      </BrowserRouter>
    );

    const cameraButton = screen.getByRole('button', { name: /turn on camera preview/i });
    await user.click(cameraButton);

    await waitFor(() => {
      expect(getUserMediaMock).toHaveBeenCalled();
    });

    // Verify MediaStream was obtained successfully
    expect(mockStream.active).toBe(true);
    expect(mockStream.getTracks().length).toBeGreaterThan(0);
    expect(mockVideoTrack.readyState).toBe('live');
  });
});
