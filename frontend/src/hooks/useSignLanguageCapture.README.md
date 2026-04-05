# Sign Language Video Capture Hook

## Overview

The `useSignLanguageCapture` hook implements real-time sign language video capture from WebRTC streams. It captures video frames at 30 FPS, buffers them in a sliding window, compresses them to JPEG format, and sends them to the inference service for sign language recognition.

## Requirements

This hook implements the following requirements:

- **35.1**: Capture participant video streams via WebRTC
- **35.2**: Extract frames from video streams at 30 frames per second
- **35.3**: Send frame sequences to Inference_Service for prediction
- **35.4**: Buffer frames in sliding windows of 60 frames (2 seconds)
- **35.5**: Process frame buffers every 500ms for real-time responsiveness
- **35.6**: Handle network interruptions gracefully by queuing frames locally
- **35.7**: Compress frames before transmission to reduce bandwidth usage

## Features

- **Frame Capture**: Captures video frames at 30 FPS from MediaStream
- **Sliding Window Buffer**: Maintains a buffer of 60 frames (2 seconds of video)
- **JPEG Compression**: Compresses frames to JPEG format with 70% quality
- **Batch Processing**: Sends frame batches to inference service every 500ms
- **Network Resilience**: Queues requests locally during network interruptions
- **Automatic Retry**: Retries failed requests with exponential backoff
- **Confidence Filtering**: Only reports predictions with confidence >= 0.7

## Usage

```typescript
import { useSignLanguageCapture } from './hooks/useSignLanguageCapture';

function MeetingRoom() {
  const { localStream } = useWebRTC(meetingId, userId);
  
  const handlePrediction = (prediction) => {
    console.log('Sign language detected:', prediction.gesture);
    console.log('Confidence:', prediction.confidence);
    
    // Display caption to users
    displaySignLanguageCaption(prediction);
  };
  
  const handleError = (error) => {
    console.error('Sign language capture error:', error);
  };
  
  const signLanguageCapture = useSignLanguageCapture(localStream, {
    enabled: signLanguageCaptionsEnabled,
    inferenceServiceUrl: 'http://localhost:8001',
    userId: currentUserId,
    meetingId: meetingId,
    onPrediction: handlePrediction,
    onError: handleError,
  });
  
  return (
    <div>
      <div>Capturing: {signLanguageCapture.isCapturing ? 'Yes' : 'No'}</div>
      <div>Processing: {signLanguageCapture.isProcessing ? 'Yes' : 'No'}</div>
      <div>Frames Captured: {signLanguageCapture.framesCaptured}</div>
      <div>Predictions: {signLanguageCapture.predictionsReceived}</div>
      <div>Queue Size: {signLanguageCapture.queueSize}</div>
      
      {signLanguageCapture.lastPrediction && (
        <div>
          Last Prediction: {signLanguageCapture.lastPrediction.gesture}
          ({(signLanguageCapture.lastPrediction.confidence * 100).toFixed(1)}%)
        </div>
      )}
      
      {signLanguageCapture.error && (
        <div>Error: {signLanguageCapture.error}</div>
      )}
    </div>
  );
}
```

## API

### Options

```typescript
interface UseSignLanguageCaptureOptions {
  enabled: boolean;                    // Enable/disable capture
  inferenceServiceUrl: string;         // URL of inference service
  userId: string;                      // Current user ID
  meetingId: string;                   // Current meeting ID
  onPrediction?: (prediction: SignLanguagePrediction) => void;  // Callback for predictions
  onError?: (error: Error) => void;    // Callback for errors
}
```

### Return Value

```typescript
interface UseSignLanguageCaptureReturn {
  isCapturing: boolean;                // Whether capture is active
  isProcessing: boolean;               // Whether inference request is in progress
  lastPrediction: SignLanguagePrediction | null;  // Last received prediction
  error: string | null;                // Last error message
  queueSize: number;                   // Number of queued inference requests
  framesCaptured: number;              // Total frames captured
  predictionsReceived: number;         // Total predictions received
}
```

### Prediction Object

```typescript
interface SignLanguagePrediction {
  gesture: string;        // Recognized gesture/word
  confidence: number;     // Confidence score (0.0 to 1.0)
  timestamp: number;      // Timestamp of prediction
  latency_ms: number;     // Inference latency in milliseconds
}
```

## Implementation Details

### Frame Capture Process

1. **Video Element Creation**: Creates an off-screen video element to play the MediaStream
2. **Canvas Rendering**: Uses a canvas to capture individual frames from the video
3. **JPEG Compression**: Converts canvas to JPEG blob with 70% quality
4. **Buffer Management**: Maintains sliding window of 60 most recent frames

### Inference Request Process

1. **Buffer Check**: Waits until buffer contains 60 frames
2. **Batch Creation**: Copies current buffer for inference request
3. **Queue Management**: Adds request to queue (max 10 requests)
4. **FormData Creation**: Creates multipart/form-data with all frames
5. **HTTP Request**: Sends POST request to inference service
6. **Response Processing**: Parses prediction and filters by confidence
7. **Callback Invocation**: Calls onPrediction if confidence >= 0.7

### Network Resilience

- **Local Queuing**: Queues up to 10 inference requests during network issues
- **Exponential Backoff**: Retries failed requests with increasing delays (1s, 2s, 4s, 8s, max 10s)
- **Queue Overflow**: Drops oldest request if queue exceeds 10 items
- **Error Reporting**: Calls onError callback for all errors

### Performance Characteristics

- **Frame Rate**: 30 FPS (33.3ms per frame)
- **Buffer Size**: 60 frames (2 seconds)
- **Inference Interval**: 500ms (2 predictions per second)
- **JPEG Quality**: 70% (balance between quality and bandwidth)
- **Typical Frame Size**: 50-200 KB per frame (compressed)
- **Batch Size**: ~3-12 MB per inference request (60 frames)

## Bandwidth Optimization

The hook implements several bandwidth optimizations:

1. **JPEG Compression**: Reduces frame size by 80-90% compared to raw pixels
2. **Batch Processing**: Sends frames in batches rather than individually
3. **Confidence Filtering**: Only processes high-confidence predictions
4. **Queue Management**: Prevents excessive queuing during network issues

## Error Handling

The hook handles various error scenarios:

- **Media Access Errors**: Video element or canvas creation failures
- **Network Errors**: HTTP request failures, timeouts
- **Service Errors**: Inference service returning error responses
- **Queue Overflow**: Too many pending requests

All errors are:
1. Logged to console
2. Stored in `error` state
3. Reported via `onError` callback
4. Automatically retried with backoff

## Testing

The hook includes comprehensive unit tests covering:

- Frame capture at 30 FPS
- Sliding window buffer management
- JPEG compression
- Inference request timing (500ms intervals)
- Network error handling and retry
- Request queuing during interruptions
- Confidence threshold filtering
- Enable/disable functionality

Run tests with:

```bash
npm test useSignLanguageCapture.test.ts
```

## Integration with MeetingRoom

To integrate with the MeetingRoom component:

1. Import the hook
2. Pass the local video stream from useWebRTC
3. Enable when user toggles sign language captions
4. Handle predictions by displaying captions
5. Handle errors by showing error messages

See the usage example above for complete integration code.

## Future Enhancements

Potential improvements for Phase 2:

- **Edge Processing**: Extract landmarks on client-side using MediaPipe
- **Adaptive Quality**: Adjust JPEG quality based on bandwidth
- **Smart Buffering**: Adjust buffer size based on gesture complexity
- **Prediction Smoothing**: Smooth predictions over multiple frames
- **Multi-Language Support**: Support BSL and other sign languages
