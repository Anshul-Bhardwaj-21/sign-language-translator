import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { FrameCaptureManager } from '../services/FrameCaptureManager';
import { MLResult } from '../services/api';

export default function VideoCallPage() {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as { cameraEnabled: boolean; micEnabled: boolean; accessibilityMode: boolean } || {};
  
  const [cameraEnabled, setCameraEnabled] = useState(state.cameraEnabled || false);
  const [micEnabled, setMicEnabled] = useState(state.micEnabled || true);
  const [accessibilityMode, setAccessibilityMode] = useState(state.accessibilityMode || false);
  const [isPaused, setIsPaused] = useState(false);
  
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [currentCaption, setCurrentCaption] = useState<string>('');
  const [captionConfidence, setCaptionConfidence] = useState<number>(0);
  const [confirmedCaptions, setConfirmedCaptions] = useState<string[]>([]);
  
  const [fps, setFps] = useState<number>(0);
  const [handDetected, setHandDetected] = useState<boolean>(false);
  const [gestureStable, setGestureStable] = useState<boolean>(false);
  
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const frameCaptureManagerRef = useRef<FrameCaptureManager | null>(null);
  const userIdRef = useRef('user_' + Math.random().toString(36).substr(2, 9));

  useEffect(() => {
    const initializeMedia = async () => {
      if (!cameraEnabled && !micEnabled) return;

      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: cameraEnabled ? {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            frameRate: { ideal: 25, max: 30 },
            facingMode: 'user'
          } : false,
          audio: micEnabled ? {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          } : false
        });

        setLocalStream(stream);
        
        if (localVideoRef.current && stream.getVideoTracks().length > 0) {
          localVideoRef.current.srcObject = stream;
          // Force video to play
          localVideoRef.current.play().catch(e => console.log('Video play error:', e));
        }
      } catch (error) {
        console.error('Failed to get user media:', error);
        alert('Failed to access camera/microphone. Please check permissions.');
      }
    };

    initializeMedia();

    return () => {
      if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  useEffect(() => {
    if (!accessibilityMode || !localVideoRef.current || !roomCode) {
      return;
    }

    const frameCapture = new FrameCaptureManager(userIdRef.current, roomCode);
    frameCaptureManagerRef.current = frameCapture;

    const handleMLResult = (result: MLResult) => {
      if (!result.success) {
        console.error('ML processing failed:', result.error);
        return;
      }

      setHandDetected(result.hand_detected);
      setGestureStable(result.movement_state === 'stable');

      if (result.caption && result.confidence > 0.58) {
        setCurrentCaption(result.caption);
        setCaptionConfidence(result.confidence);
      }
    };

    frameCapture.startProcessing(localVideoRef.current, handleMLResult);

    return () => {
      frameCapture.stopProcessing();
    };
  }, [accessibilityMode, roomCode]);

  useEffect(() => {
    let frameCount = 0;
    let lastTime = Date.now();

    const interval = setInterval(() => {
      const now = Date.now();
      const elapsed = (now - lastTime) / 1000;
      setFps(frameCount / elapsed);
      frameCount = 0;
      lastTime = now;
    }, 1000);

    const countFrame = () => {
      frameCount++;
      requestAnimationFrame(countFrame);
    };
    countFrame();

    return () => clearInterval(interval);
  }, []);

  const handleToggleCamera = async () => {
    if (!cameraEnabled) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { 
            width: { ideal: 1280 }, 
            height: { ideal: 720 },
            facingMode: 'user'
          }
        });
        
        if (localStream) {
          const videoTrack = stream.getVideoTracks()[0];
          localStream.addTrack(videoTrack);
          if (localVideoRef.current) {
            localVideoRef.current.srcObject = localStream;
            localVideoRef.current.play().catch(e => console.log('Video play error:', e));
          }
        } else {
          setLocalStream(stream);
          if (localVideoRef.current) {
            localVideoRef.current.srcObject = stream;
            localVideoRef.current.play().catch(e => console.log('Video play error:', e));
          }
        }
        
        setCameraEnabled(true);
      } catch (error) {
        alert('Failed to enable camera');
      }
    } else {
      if (localStream) {
        localStream.getVideoTracks().forEach(track => track.stop());
      }
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = null;
      }
      setCameraEnabled(false);
    }
  };

  const handleToggleMic = () => {
    if (localStream) {
      localStream.getAudioTracks().forEach(track => {
        track.enabled = !micEnabled;
      });
    }
    setMicEnabled(!micEnabled);
  };

  const handleToggleAccessibility = () => {
    setAccessibilityMode(!accessibilityMode);
  };

  const handlePause = () => {
    setIsPaused(!isPaused);
  };

  const handleClear = () => {
    setCurrentCaption('');
    setConfirmedCaptions([]);
  };

  const handleSpeak = () => {
    const text = [...confirmedCaptions, currentCaption].join(' ');
    if (text && 'speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      speechSynthesis.speak(utterance);
    }
  };

  const handleLeave = () => {
    if (confirm('Are you sure you want to leave the call?')) {
      if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
      }
      navigate('/');
    }
  };

  const handleConfirmCaption = () => {
    if (currentCaption) {
      setConfirmedCaptions(prev => [...prev, currentCaption]);
      setCurrentCaption('');
    }
  };

  return (
    <div className="flex flex-col h-screen bg-meet-dark">
      {/* Status Bar */}
      <div className="bg-meet-gray px-6 py-3 flex justify-between items-center border-b border-gray-700">
        <div className="flex gap-6 text-sm text-gray-300">
          <span>📊 FPS: {fps.toFixed(1)}</span>
          <span>{handDetected ? '✋ Hand Detected' : '👋 No Hand'}</span>
          <span>{gestureStable ? '🔵 Stable' : '⚪ Moving'}</span>
        </div>
        {accessibilityMode && (
          <div className="bg-purple-600 px-4 py-1 rounded-full text-white text-sm font-semibold">
            🧏 Accessibility Mode Active
          </div>
        )}
      </div>

      {/* Video Grid */}
      <div className="flex-1 relative p-4">
        <div className="w-full h-full bg-black rounded-lg overflow-hidden relative">
          {cameraEnabled && localStream ? (
            <video
              ref={localVideoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-contain"
              style={{ transform: 'scaleX(-1)' }}
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="text-8xl mb-4">📷</div>
                <div className="text-gray-400 text-xl">
                  {cameraEnabled ? 'Loading camera...' : 'Camera is off'}
                </div>
              </div>
            </div>
          )}

          {/* Caption Overlay */}
          {accessibilityMode && currentCaption && (
            <div className="absolute bottom-24 left-1/2 transform -translate-x-1/2 max-w-4xl w-full px-8">
              <div className="bg-black bg-opacity-90 rounded-lg p-6">
                <div className="text-white text-3xl font-semibold text-center leading-relaxed">
                  {currentCaption}
                </div>
                {captionConfidence > 0 && (
                  <div className="text-blue-400 text-sm text-center mt-2">
                    {Math.round(captionConfidence * 100)}% confident
                  </div>
                )}
                <div className="flex justify-center gap-4 mt-4">
                  <button
                    onClick={handleConfirmCaption}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    ✓ Confirm
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Confirmed Captions */}
          {confirmedCaptions.length > 0 && (
            <div className="absolute bottom-4 left-4 right-4 bg-gray-800 bg-opacity-80 rounded-lg p-4">
              <div className="text-gray-300 text-lg">
                {confirmedCaptions.join(' ')}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Control Bar */}
      <div className="bg-meet-gray px-6 py-4 border-t border-gray-700">
        <div className="flex justify-center items-center gap-4">
          <button
            onClick={handleToggleMic}
            className={`w-14 h-14 rounded-full flex items-center justify-center text-2xl transition-colors ${
              micEnabled ? 'bg-gray-700 hover:bg-gray-600' : 'bg-red-600 hover:bg-red-700'
            }`}
            title={micEnabled ? 'Mute' : 'Unmute'}
          >
            {micEnabled ? '🎤' : '🔇'}
          </button>

          <button
            onClick={handleToggleCamera}
            className={`w-14 h-14 rounded-full flex items-center justify-center text-2xl transition-colors ${
              cameraEnabled ? 'bg-gray-700 hover:bg-gray-600' : 'bg-red-600 hover:bg-red-700'
            }`}
            title={cameraEnabled ? 'Turn off camera' : 'Turn on camera'}
          >
            {cameraEnabled ? '📹' : '📷'}
          </button>

          <button
            onClick={handleToggleAccessibility}
            className={`w-14 h-14 rounded-full flex items-center justify-center text-2xl transition-colors ${
              accessibilityMode ? 'bg-purple-600 hover:bg-purple-700' : 'bg-gray-700 hover:bg-gray-600'
            }`}
            title="Toggle Accessibility Mode"
          >
            🧏
          </button>

          <button
            onClick={handlePause}
            className="w-14 h-14 rounded-full bg-gray-700 hover:bg-gray-600 flex items-center justify-center text-2xl"
            title={isPaused ? 'Resume' : 'Pause'}
          >
            {isPaused ? '▶️' : '⏸️'}
          </button>

          <button
            onClick={handleClear}
            className="w-14 h-14 rounded-full bg-gray-700 hover:bg-gray-600 flex items-center justify-center text-2xl"
            title="Clear Captions"
          >
            🗑️
          </button>

          <button
            onClick={handleSpeak}
            className="w-14 h-14 rounded-full bg-gray-700 hover:bg-gray-600 flex items-center justify-center text-2xl"
            title="Speak Captions"
          >
            🔊
          </button>

          <button
            onClick={handleLeave}
            className="w-14 h-14 rounded-full bg-red-600 hover:bg-red-700 flex items-center justify-center text-2xl"
            title="Leave Call"
          >
            📞
          </button>
        </div>
      </div>
    </div>
  );
}
