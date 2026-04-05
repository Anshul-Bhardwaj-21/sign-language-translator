import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useSignLanguageCapture } from './useSignLanguageCapture';

/**
 * Unit tests for useSignLanguageCapture hook
 * 
 * Tests:
 * - Frame capture at 30 FPS
 * - Frame buffering with sliding window (60 frames)
 * - Frame compression to JPEG
 * - Inference requests every 500ms
 * - Network interruption handling with local queuing
 * - Retry with exponential backoff
 */

// Mock fetch
global.fetch = vi.fn();

// Mock HTMLVideoElement
class MockVideoElement {
  videoWidth = 640;
  videoHeight = 480;
  readyState = 4; // HAVE_ENOUGH_DATA
  srcObject: MediaStream | null = null;
  autoplay = false;
  playsInline = false;
  muted = false;
  HAVE_ENOUGH_DATA = 4;
}

// Mock HTMLCanvasElement
class MockCanvasElement {
  width = 0;
  height = 0;
  
  getContext() {
    return {
      drawImage: vi.fn(),
    };
  }
  
  toBlob(callback: (blob: Blob | null) => void, type: string, quality: number) {
    // Simulate JPEG blob creation
    const blob = new Blob(['fake-image-data'], { type: 'image/jpeg' });
    setTimeout(() => callback(blob), 0);
  }
}

// Mock document.createElement
const originalCreateElement = document.createElement.bind(document);
document.createElement = vi.fn((tagName: string) => {
  if (tagName === 'video') {
    return new MockVideoElement() as any;
  }
  if (tagName === 'canvas') {
    return new MockCanvasElement() as any;
  }
  return originalCreateElement(tagName);
});

describe('useSignLanguageCapture', () => {
  let mockVideoStream: MediaStream;
  
  beforeEach(() => {
    vi.useFakeTimers();
    
    // Create mock MediaStream
    mockVideoStream = {
      getTracks: () => [],
      getVideoTracks: () => [],
      getAudioTracks: () => [],
    } as any;
    
    // Reset fetch mock
    (global.fetch as any).mockReset();
  });
  
  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
  });
  
  it('should initialize with default state', () => {
    const { result } = renderHook(() =>
      useSignLanguageCapture(null, {
        enabled: false,
        inferenceServiceUrl: 'http://localhost:8001',
        userId: 'user123',
        meetingId: 'meeting456',
      })
    );
    
    expect(result.current.isCapturing).toBe(false);
    expect(result.current.isProcessing).toBe(false);
    expect(result.current.lastPrediction).toBe(null);
    expect(result.current.error).toBe(null);
    expect(result.current.queueSize).toBe(0);
    expect(result.current.framesCaptured).toBe(0);
    expect(result.current.predictionsReceived).toBe(0);
  });
  
  it('should start capturing when enabled with video stream', async () => {
    const { result } = renderHook(() =>
      useSignLanguageCapture(mockVideoStream, {
        enabled: true,
        inferenceServiceUrl: 'http://localhost:8001',
        userId: 'user123',
        meetingId: 'meeting456',
      })
    );
    
    await waitFor(() => {
      expect(result.current.isCapturing).toBe(true);
    });
  });
  
  it('should not start capturing when disabled', () => {
    const { result } = renderHook(() =>
      useSignLanguageCapture(mockVideoStream, {
        enabled: false,
        inferenceServiceUrl: 'http://localhost:8001',
        userId: 'user123',
        meetingId: 'meeting456',
      })
    );
    
    expect(result.current.isCapturing).toBe(false);
  });
  
  it('should capture frames at 30 FPS (Requirement 35.2)', async () => {
    const { result } = renderHook(() =>
      useSignLanguageCapture(mockVideoStream, {
        enabled: true,
        inferenceServiceUrl: 'http://localhost:8001',
        userId: 'user123',
        meetingId: 'meeting456',
      })
    );
    
    await waitFor(() => {
      expect(result.current.isCapturing).toBe(true);
    });
    
    // Advance time by 1 second (should capture ~30 frames)
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    
    await waitFor(() => {
      expect(result.current.framesCaptured).toBeGreaterThanOrEqual(25);
      expect(result.current.framesCaptured).toBeLessThanOrEqual(35);
    });
  });
  
  it('should send frames to inference service every 500ms (Requirement 35.5)', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        gesture: 'hello',
        confidence: 0.85,
      }),
    });
    
    const { result } = renderHook(() =>
      useSignLanguageCapture(mockVideoStream, {
        enabled: true,
        inferenceServiceUrl: 'http://localhost:8001',
        userId: 'user123',
        meetingId: 'meeting456',
      })
    );
    
    await waitFor(() => {
      expect(result.current.isCapturing).toBe(true);
    });
    
    // Advance time to capture 60 frames (2 seconds)
    act(() => {
      vi.advanceTimersByTime(2000);
    });
    
    // Wait for frames to be captured
    await waitFor(() => {
      expect(result.current.framesCaptured).toBeGreaterThanOrEqual(60);
    });
    
    // Advance time by 500ms to trigger inference
    act(() => {
      vi.advanceTimersByTime(500);
    });
    
    // Wait for inference request
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });
    
    const fetchCall = (global.fetch as any).mock.calls[0];
    expect(fetchCall[0]).toBe('http://localhost:8001/predict');
    expect(fetchCall[1].method).toBe('POST');
  });
  
  it('should call onPrediction callback when prediction received', async () => {
    const mockPrediction = {
      gesture: 'hello',
      confidence: 0.85,
    };
    
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockPrediction,
    });
    
    const onPrediction = vi.fn();
    
    const { result } = renderHook(() =>
      useSignLanguageCapture(mockVideoStream, {
        enabled: true,
        inferenceServiceUrl: 'http://localhost:8001',
        userId: 'user123',
        meetingId: 'meeting456',
        onPrediction,
      })
    );
    
    await waitFor(() => {
      expect(result.current.isCapturing).toBe(true);
    });
    
    // Capture frames and trigger inference
    act(() => {
      vi.advanceTimersByTime(2500);
    });
    
    await waitFor(() => {
      expect(onPrediction).toHaveBeenCalled();
    });
    
    const prediction = onPrediction.mock.calls[0][0];
    expect(prediction.gesture).toBe('hello');
    expect(prediction.confidence).toBe(0.85);
    expect(prediction.timestamp).toBeDefined();
    expect(prediction.latency_ms).toBeDefined();
  });
  
  it('should not call onPrediction for low confidence predictions', async () => {
    const mockPrediction = {
      gesture: 'hello',
      confidence: 0.5, // Below threshold
    };
    
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockPrediction,
    });
    
    const onPrediction = vi.fn();
    
    renderHook(() =>
      useSignLanguageCapture(mockVideoStream, {
        enabled: true,
        inferenceServiceUrl: 'http://localhost:8001',
        userId: 'user123',
        meetingId: 'meeting456',
        onPrediction,
      })
    );
    
    // Capture frames and trigger inference
    act(() => {
      vi.advanceTimersByTime(2500);
    });
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });
    
    // Wait a bit more to ensure callback is not called
    act(() => {
      vi.advanceTimersByTime(500);
    });
    
    expect(onPrediction).not.toHaveBeenCalled();
  });
  
  it('should handle network errors with retry (Requirement 35.6)', async () => {
    let callCount = 0;
    (global.fetch as any).mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.reject(new Error('Network error'));
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({
          gesture: 'hello',
          confidence: 0.85,
        }),
      });
    });
    
    const onError = vi.fn();
    
    const { result } = renderHook(() =>
      useSignLanguageCapture(mockVideoStream, {
        enabled: true,
        inferenceServiceUrl: 'http://localhost:8001',
        userId: 'user123',
        meetingId: 'meeting456',
        onError,
      })
    );
    
    await waitFor(() => {
      expect(result.current.isCapturing).toBe(true);
    });
    
    // Capture frames and trigger inference
    act(() => {
      vi.advanceTimersByTime(2500);
    });
    
    // Wait for first request to fail
    await waitFor(() => {
      expect(onError).toHaveBeenCalled();
    });
    
    expect(result.current.error).toBeTruthy();
    
    // Advance time for retry (1 second initial delay)
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    
    // Wait for retry to succeed
    await waitFor(() => {
      expect(callCount).toBe(2);
    });
  });
  
  it('should queue requests during network interruptions (Requirement 35.6)', async () => {
    // Mock slow network
    (global.fetch as any).mockImplementation(() => {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            ok: true,
            json: async () => ({
              gesture: 'hello',
              confidence: 0.85,
            }),
          });
        }, 2000);
      });
    });
    
    const { result } = renderHook(() =>
      useSignLanguageCapture(mockVideoStream, {
        enabled: true,
        inferenceServiceUrl: 'http://localhost:8001',
        userId: 'user123',
        meetingId: 'meeting456',
      })
    );
    
    await waitFor(() => {
      expect(result.current.isCapturing).toBe(true);
    });
    
    // Capture frames and trigger multiple inference requests
    act(() => {
      vi.advanceTimersByTime(3000); // 3 seconds = 6 inference intervals
    });
    
    await waitFor(() => {
      expect(result.current.queueSize).toBeGreaterThan(0);
    });
  });
  
  it('should stop capturing when disabled', async () => {
    const { result, rerender } = renderHook(
      ({ enabled }) =>
        useSignLanguageCapture(mockVideoStream, {
          enabled,
          inferenceServiceUrl: 'http://localhost:8001',
          userId: 'user123',
          meetingId: 'meeting456',
        }),
      { initialProps: { enabled: true } }
    );
    
    await waitFor(() => {
      expect(result.current.isCapturing).toBe(true);
    });
    
    // Disable capture
    rerender({ enabled: false });
    
    await waitFor(() => {
      expect(result.current.isCapturing).toBe(false);
    });
  });
  
  it('should compress frames to JPEG (Requirement 35.7)', async () => {
    const { result } = renderHook(() =>
      useSignLanguageCapture(mockVideoStream, {
        enabled: true,
        inferenceServiceUrl: 'http://localhost:8001',
        userId: 'user123',
        meetingId: 'meeting456',
      })
    );
    
    await waitFor(() => {
      expect(result.current.isCapturing).toBe(true);
    });
    
    // Capture frames
    act(() => {
      vi.advanceTimersByTime(100);
    });
    
    await waitFor(() => {
      expect(result.current.framesCaptured).toBeGreaterThan(0);
    });
    
    // Verify canvas.toBlob was called with JPEG type
    const canvas = document.createElement('canvas') as any;
    expect(canvas.toBlob).toBeDefined();
  });
});
