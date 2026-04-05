import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Sign Language Video Capture Hook
 * 
 * Requirements:
 * - 35.1: Capture participant video streams via WebRTC
 * - 35.2: Extract frames from video streams at 30 frames per second
 * - 35.3: Send frame sequences to Inference_Service for prediction
 * - 35.4: Buffer frames in sliding windows of 60 frames (2 seconds)
 * - 35.5: Process frame buffers every 500ms for real-time responsiveness
 * - 35.6: Handle network interruptions gracefully by queuing frames locally
 * - 35.7: Compress frames before transmission to reduce bandwidth usage
 * 
 * Features:
 * - Captures video frames from MediaStream at 30 FPS
 * - Maintains sliding window buffer of 60 frames
 * - Compresses frames to JPEG format
 * - Sends frame batches to inference service every 500ms
 * - Queues frames locally during network interruptions
 * - Automatic retry with exponential backoff
 */

export interface SignLanguagePrediction {
  gesture: string;
  confidence: number;
  timestamp: number;
  latency_ms: number;
}

export interface UseSignLanguageCaptureOptions {
  enabled: boolean;
  inferenceServiceUrl: string;
  userId: string;
  meetingId: string;
  onPrediction?: (prediction: SignLanguagePrediction) => void;
  onError?: (error: Error) => void;
}

export interface UseSignLanguageCaptureReturn {
  isCapturing: boolean;
  isProcessing: boolean;
  lastPrediction: SignLanguagePrediction | null;
  error: string | null;
  queueSize: number;
  framesCaptured: number;
  predictionsReceived: number;
}

const FRAME_RATE = 30; // FPS (Requirement 35.2)
const BUFFER_SIZE = 60; // frames (Requirement 35.4)
const INFERENCE_INTERVAL = 500; // ms (Requirement 35.5)
const JPEG_QUALITY = 0.7; // Compression quality (Requirement 35.7)
const MAX_QUEUE_SIZE = 10; // Maximum number of queued inference requests
const RETRY_DELAY_MS = 1000; // Initial retry delay
const MAX_RETRY_DELAY_MS = 10000; // Maximum retry delay

export const useSignLanguageCapture = (
  videoStream: MediaStream | null,
  options: UseSignLanguageCaptureOptions
): UseSignLanguageCaptureReturn => {
  const {
    enabled,
    inferenceServiceUrl,
    userId,
    meetingId,
    onPrediction,
    onError,
  } = options;

  // State
  const [isCapturing, setIsCapturing] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastPrediction, setLastPrediction] = useState<SignLanguagePrediction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [queueSize, setQueueSize] = useState(0);
  const [framesCaptured, setFramesCaptured] = useState(0);
  const [predictionsReceived, setPredictionsReceived] = useState(0);

  // Refs
  const videoElementRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const frameBufferRef = useRef<Blob[]>([]);
  const captureIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const inferenceIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const requestQueueRef = useRef<Blob[][]>([]);
  const retryDelayRef = useRef<number>(RETRY_DELAY_MS);
  const isInferringRef = useRef<boolean>(false);

  /**
   * Capture a single frame from the video stream (Requirement 35.2)
   * Compresses frame to JPEG format (Requirement 35.7)
   */
  const captureFrame = useCallback(async (): Promise<Blob | null> => {
    if (!videoElementRef.current || !canvasRef.current) {
      return null;
    }

    const video = videoElementRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    if (!ctx || video.readyState !== video.HAVE_ENOUGH_DATA) {
      return null;
    }

    try {
      // Set canvas size to match video
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      // Draw current video frame to canvas
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert canvas to JPEG blob (Requirement 35.7)
      const blob = await new Promise<Blob | null>((resolve) => {
        canvas.toBlob(
          (blob) => resolve(blob),
          'image/jpeg',
          JPEG_QUALITY
        );
      });

      if (blob) {
        setFramesCaptured((prev) => prev + 1);
      }

      return blob;
    } catch (err) {
      console.error('Error capturing frame:', err);
      return null;
    }
  }, []);

  /**
   * Add frame to sliding window buffer (Requirement 35.4)
   */
  const addFrameToBuffer = useCallback((frame: Blob) => {
    frameBufferRef.current.push(frame);

    // Maintain sliding window of 60 frames
    if (frameBufferRef.current.length > BUFFER_SIZE) {
      frameBufferRef.current.shift();
    }
  }, []);

  /**
   * Send frame buffer to inference service (Requirement 35.3)
   * Handles network interruptions with local queuing (Requirement 35.6)
   */
  const sendFramesToInference = useCallback(async () => {
    // Skip if already processing or buffer is not full
    if (isInferringRef.current || frameBufferRef.current.length < BUFFER_SIZE) {
      return;
    }

    // Check queue size limit
    if (requestQueueRef.current.length >= MAX_QUEUE_SIZE) {
      console.warn('Request queue is full, dropping oldest request');
      requestQueueRef.current.shift();
    }

    // Copy current buffer for inference
    const framesToSend = [...frameBufferRef.current];
    requestQueueRef.current.push(framesToSend);
    setQueueSize(requestQueueRef.current.length);

    // Process queue
    await processInferenceQueue();
  }, []);

  /**
   * Process queued inference requests (Requirement 35.6)
   */
  const processInferenceQueue = useCallback(async () => {
    if (isInferringRef.current || requestQueueRef.current.length === 0) {
      return;
    }

    isInferringRef.current = true;
    setIsProcessing(true);

    const framesToSend = requestQueueRef.current[0];

    try {
      // Create FormData with frames
      const formData = new FormData();
      
      framesToSend.forEach((frame, index) => {
        formData.append('frames', frame, `frame_${index}.jpg`);
      });
      
      formData.append('user_id', userId);
      formData.append('meeting_id', meetingId);
      formData.append('sign_language', 'ASL');
      formData.append('strategy', 'cloud');

      const startTime = Date.now();

      // Send to inference service
      const response = await fetch(`${inferenceServiceUrl}/predict`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Inference service returned ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      const latency = Date.now() - startTime;

      // Check if prediction meets confidence threshold
      if (result.gesture && result.confidence >= 0.7) {
        const prediction: SignLanguagePrediction = {
          gesture: result.gesture,
          confidence: result.confidence,
          timestamp: Date.now(),
          latency_ms: latency,
        };

        setLastPrediction(prediction);
        setPredictionsReceived((prev) => prev + 1);

        if (onPrediction) {
          onPrediction(prediction);
        }

        console.log('Sign language prediction:', prediction);
      }

      // Success - remove from queue and reset retry delay
      requestQueueRef.current.shift();
      setQueueSize(requestQueueRef.current.length);
      retryDelayRef.current = RETRY_DELAY_MS;
      setError(null);

      // Process next item in queue
      isInferringRef.current = false;
      setIsProcessing(false);
      
      if (requestQueueRef.current.length > 0) {
        setTimeout(() => processInferenceQueue(), 0);
      }

    } catch (err) {
      console.error('Error sending frames to inference service:', err);
      
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);

      if (onError) {
        onError(err instanceof Error ? err : new Error(errorMessage));
      }

      // Retry with exponential backoff (Requirement 35.6)
      isInferringRef.current = false;
      setIsProcessing(false);

      setTimeout(() => {
        retryDelayRef.current = Math.min(
          retryDelayRef.current * 2,
          MAX_RETRY_DELAY_MS
        );
        processInferenceQueue();
      }, retryDelayRef.current);
    }
  }, [userId, meetingId, inferenceServiceUrl, onPrediction, onError]);

  /**
   * Start capturing frames at 30 FPS (Requirement 35.2)
   */
  const startCapture = useCallback(() => {
    if (!videoStream || !enabled) {
      return;
    }

    console.log('Starting sign language video capture');

    // Create video element if not exists
    if (!videoElementRef.current) {
      const video = document.createElement('video');
      video.autoplay = true;
      video.playsInline = true;
      video.muted = true;
      videoElementRef.current = video;
    }

    // Create canvas if not exists
    if (!canvasRef.current) {
      canvasRef.current = document.createElement('canvas');
    }

    // Set video source
    videoElementRef.current.srcObject = videoStream;

    // Start frame capture at 30 FPS
    const frameInterval = 1000 / FRAME_RATE;
    captureIntervalRef.current = setInterval(async () => {
      const frame = await captureFrame();
      if (frame) {
        addFrameToBuffer(frame);
      }
    }, frameInterval);

    // Start inference processing every 500ms (Requirement 35.5)
    inferenceIntervalRef.current = setInterval(() => {
      sendFramesToInference();
    }, INFERENCE_INTERVAL);

    setIsCapturing(true);
    setError(null);
  }, [videoStream, enabled, captureFrame, addFrameToBuffer, sendFramesToInference]);

  /**
   * Stop capturing frames
   */
  const stopCapture = useCallback(() => {
    console.log('Stopping sign language video capture');

    // Clear intervals
    if (captureIntervalRef.current) {
      clearInterval(captureIntervalRef.current);
      captureIntervalRef.current = null;
    }

    if (inferenceIntervalRef.current) {
      clearInterval(inferenceIntervalRef.current);
      inferenceIntervalRef.current = null;
    }

    // Clear buffers
    frameBufferRef.current = [];
    requestQueueRef.current = [];

    // Reset state
    setIsCapturing(false);
    setIsProcessing(false);
    setQueueSize(0);

    // Clean up video element
    if (videoElementRef.current) {
      videoElementRef.current.srcObject = null;
    }
  }, []);

  /**
   * Start/stop capture based on enabled state and video stream
   */
  useEffect(() => {
    if (enabled && videoStream) {
      startCapture();
    } else {
      stopCapture();
    }

    return () => {
      stopCapture();
    };
  }, [enabled, videoStream, startCapture, stopCapture]);

  return {
    isCapturing,
    isProcessing,
    lastPrediction,
    error,
    queueSize,
    framesCaptured,
    predictionsReceived,
  };
};
