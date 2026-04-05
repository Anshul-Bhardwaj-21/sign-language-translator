/**
 * Sign Language Capture Integration Example
 * 
 * This example demonstrates how to integrate the useSignLanguageCapture hook
 * into the MeetingRoom component to enable real-time sign language recognition.
 * 
 * Requirements:
 * - 35.1-35.7: Sign language video capture integration
 * - 36.1-36.8: Real-time sign language captions
 * - 37.1-37.6: Dual caption display system
 */

import { useState } from 'react';
import { useWebRTC } from '../hooks/useWebRTC';
import { useSignLanguageCapture, SignLanguagePrediction } from '../hooks/useSignLanguageCapture';

interface SignLanguageCaption {
  id: string;
  userId: string;
  userName: string;
  gesture: string;
  confidence: number;
  timestamp: number;
}

export function MeetingRoomWithSignLanguage() {
  const meetingId = 'meeting123';
  const userId = 'user456';
  const userName = 'John Doe';
  
  // WebRTC hook for video/audio streams
  const webrtc = useWebRTC(meetingId, userId);
  
  // State for sign language captions
  const [signLanguageCaptionsEnabled, setSignLanguageCaptionsEnabled] = useState(false);
  const [signLanguageCaptions, setSignLanguageCaptions] = useState<SignLanguageCaption[]>([]);
  const [captionError, setCaptionError] = useState<string | null>(null);
  
  // Handle sign language predictions (Requirement 36.1, 36.2)
  const handleSignLanguagePrediction = (prediction: SignLanguagePrediction) => {
    console.log('Sign language prediction received:', prediction);
    
    // Create caption object
    const caption: SignLanguageCaption = {
      id: `caption_${Date.now()}`,
      userId: userId,
      userName: userName,
      gesture: prediction.gesture,
      confidence: prediction.confidence,
      timestamp: prediction.timestamp,
    };
    
    // Add to caption history (Requirement 36.5)
    setSignLanguageCaptions((prev) => [...prev, caption]);
    
    // Broadcast caption to other participants via signaling server
    // sendMessage('sign-language-caption', caption);
    
    // Display caption in UI (Requirement 36.1)
    displaySignLanguageCaption(caption);
  };
  
  // Handle capture errors (Requirement 35.6)
  const handleCaptureError = (error: Error) => {
    console.error('Sign language capture error:', error);
    setCaptionError(error.message);
    
    // Show error notification to user
    showErrorNotification('Sign language recognition error: ' + error.message);
  };
  
  // Sign language capture hook (Requirements 35.1-35.7)
  const signLanguageCapture = useSignLanguageCapture(webrtc.localStream, {
    enabled: signLanguageCaptionsEnabled,
    inferenceServiceUrl: import.meta.env.VITE_INFERENCE_SERVICE_URL || 'http://localhost:8001',
    userId: userId,
    meetingId: meetingId,
    onPrediction: handleSignLanguagePrediction,
    onError: handleCaptureError,
  });
  
  // Toggle sign language captions (Requirement 36.6, 37.4)
  const toggleSignLanguageCaptions = () => {
    setSignLanguageCaptionsEnabled(!signLanguageCaptionsEnabled);
    
    if (!signLanguageCaptionsEnabled) {
      // Clear error when enabling
      setCaptionError(null);
    }
  };
  
  // Display caption in UI (Requirement 36.1, 36.4, 36.7, 36.8)
  const displaySignLanguageCaption = (caption: SignLanguageCaption) => {
    // This would integrate with your caption display component
    // For example, DualCaptionDisplay component
    console.log('Displaying caption:', caption);
  };
  
  // Show error notification
  const showErrorNotification = (message: string) => {
    // This would integrate with your notification system
    console.error('Notification:', message);
  };
  
  return (
    <div className="meeting-room">
      {/* Video Grid */}
      <div className="video-grid">
        {/* Video tiles would go here */}
      </div>
      
      {/* Sign Language Caption Display (Requirements 36.1-36.8, 37.1-37.6) */}
      <div className="caption-container">
        {signLanguageCaptionsEnabled && (
          <div className="sign-language-captions">
            <div className="caption-header">
              <span className="caption-label">Sign Language</span>
              <span className="caption-status">
                {signLanguageCapture.isCapturing ? '🟢 Active' : '🔴 Inactive'}
              </span>
            </div>
            
            {/* Last prediction display (Requirement 36.1, 36.3) */}
            {signLanguageCapture.lastPrediction && (
              <div className="current-caption">
                <span className="caption-text">
                  {signLanguageCapture.lastPrediction.gesture}
                </span>
                <span className="caption-confidence">
                  {(signLanguageCapture.lastPrediction.confidence * 100).toFixed(0)}%
                </span>
              </div>
            )}
            
            {/* Caption history (Requirement 36.5) */}
            <div className="caption-history">
              {signLanguageCaptions.slice(-10).map((caption) => (
                <div key={caption.id} className="caption-item">
                  <span className="caption-user">{caption.userName}:</span>
                  <span className="caption-gesture">{caption.gesture}</span>
                  <span className="caption-confidence">
                    ({(caption.confidence * 100).toFixed(0)}%)
                  </span>
                </div>
              ))}
            </div>
            
            {/* Error display */}
            {captionError && (
              <div className="caption-error">
                ⚠️ {captionError}
              </div>
            )}
            
            {/* Debug info */}
            <div className="caption-debug">
              <div>Frames: {signLanguageCapture.framesCaptured}</div>
              <div>Predictions: {signLanguageCapture.predictionsReceived}</div>
              <div>Queue: {signLanguageCapture.queueSize}</div>
              <div>Processing: {signLanguageCapture.isProcessing ? 'Yes' : 'No'}</div>
            </div>
          </div>
        )}
      </div>
      
      {/* Control Bar */}
      <div className="control-bar">
        {/* Other controls */}
        
        {/* Sign Language Caption Toggle (Requirement 36.6, 37.4) */}
        <button
          onClick={toggleSignLanguageCaptions}
          className={`control-button ${signLanguageCaptionsEnabled ? 'active' : ''}`}
          title="Toggle sign language captions"
        >
          <span className="icon">🤟</span>
          <span className="label">Sign Language</span>
          {signLanguageCaptionsEnabled && signLanguageCapture.isCapturing && (
            <span className="indicator">●</span>
          )}
        </button>
      </div>
    </div>
  );
}

/**
 * Example CSS styles for sign language captions
 */
export const signLanguageCaptionStyles = `
.caption-container {
  position: absolute;
  bottom: 80px;
  left: 20px;
  right: 20px;
  pointer-events: none;
}

.sign-language-captions {
  background: rgba(0, 0, 0, 0.8);
  border-radius: 8px;
  padding: 16px;
  max-width: 600px;
  margin: 0 auto;
  pointer-events: auto;
}

.caption-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.caption-label {
  color: #60a5fa;
  font-weight: 600;
  font-size: 14px;
}

.caption-status {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.current-caption {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: rgba(96, 165, 250, 0.2);
  border-radius: 6px;
  margin-bottom: 12px;
}

.caption-text {
  color: white;
  font-size: 18px;
  font-weight: 600;
}

.caption-confidence {
  color: #60a5fa;
  font-size: 14px;
  font-weight: 500;
}

.caption-history {
  max-height: 150px;
  overflow-y: auto;
  margin-bottom: 12px;
}

.caption-item {
  padding: 6px 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  display: flex;
  gap: 8px;
}

.caption-user {
  color: #60a5fa;
  font-weight: 500;
}

.caption-gesture {
  flex: 1;
}

.caption-error {
  padding: 8px 12px;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.4);
  border-radius: 6px;
  color: #fca5a5;
  font-size: 14px;
  margin-bottom: 12px;
}

.caption-debug {
  display: flex;
  gap: 16px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.control-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.control-button:hover {
  background: rgba(255, 255, 255, 0.2);
}

.control-button.active {
  background: rgba(96, 165, 250, 0.3);
  border: 1px solid rgba(96, 165, 250, 0.5);
}

.control-button .icon {
  font-size: 24px;
}

.control-button .label {
  font-size: 12px;
}

.control-button .indicator {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
`;

/**
 * Example environment variables (.env file)
 */
export const exampleEnvVariables = `
# Inference Service URL
VITE_INFERENCE_SERVICE_URL=http://localhost:8001

# Enable sign language captions by default
VITE_SIGN_LANGUAGE_ENABLED=false

# Confidence threshold (0.0 to 1.0)
VITE_SIGN_LANGUAGE_CONFIDENCE_THRESHOLD=0.7
`;

/**
 * Example integration with signaling server
 */
export const signalingServerIntegration = `
// In your signaling server event handlers:

// Broadcast sign language caption to all participants
socket.on('sign-language-caption', (data) => {
  const { meetingId, caption } = data;
  
  // Broadcast to all participants in the meeting
  io.to(meetingId).emit('sign-language-caption', {
    userId: caption.userId,
    userName: caption.userName,
    gesture: caption.gesture,
    confidence: caption.confidence,
    timestamp: caption.timestamp,
  });
  
  // Store caption in database for transcript
  await storeSignLanguageCaption(meetingId, caption);
});

// In your React component:
useEffect(() => {
  const unsubscribe = subscribe('sign-language-caption', (data) => {
    // Add received caption to state
    setSignLanguageCaptions((prev) => [...prev, {
      id: \`caption_\${Date.now()}\`,
      userId: data.userId,
      userName: data.userName,
      gesture: data.gesture,
      confidence: data.confidence,
      timestamp: data.timestamp,
    }]);
  });
  
  return unsubscribe;
}, [subscribe]);
`;
