import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../services/api';

export default function PreJoinLobby() {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [micEnabled, setMicEnabled] = useState(true);
  const [accessibilityMode, setAccessibilityMode] = useState(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string>('');
  const [isValidating, setIsValidating] = useState(true);
  const [cameraDevices, setCameraDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedCamera, setSelectedCamera] = useState<string>('');
  
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const validate = async () => {
      if (!roomCode) {
        setError('Invalid room code');
        setIsValidating(false);
        return;
      }

      try {
        const result = await api.validateRoom(roomCode);
        if (!result.valid) {
          setError('Room not found');
        } else if (result.is_full) {
          setError('Room is full');
        }
      } catch (err) {
        setError('Failed to validate room');
      } finally {
        setIsValidating(false);
      }
    };

    validate();
    
    // Get available cameras
    navigator.mediaDevices.enumerateDevices()
      .then(devices => {
        const cameras = devices.filter(device => device.kind === 'videoinput');
        setCameraDevices(cameras);
        if (cameras.length > 0) {
          setSelectedCamera(cameras[0].deviceId);
        }
      })
      .catch(err => console.log('Failed to enumerate devices:', err));
  }, [roomCode]);

  const toggleCameraPreview = async () => {
    if (cameraEnabled) {
      // Stop camera
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => {
          track.stop();
          track.enabled = false;
        });
        setCameraStream(null);
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      setCameraEnabled(false);
      setError('');
    } else {
      // Start camera with multiple fallback options
      setError('Starting camera...');
      
      const constraints = [
        // Try 1: Specific device
        selectedCamera ? {
          video: { 
            deviceId: { exact: selectedCamera },
            width: { ideal: 640 },
            height: { ideal: 480 }
          },
          audio: false
        } : null,
        // Try 2: Front camera
        {
          video: { 
            facingMode: 'user',
            width: { ideal: 640 },
            height: { ideal: 480 }
          },
          audio: false
        },
        // Try 3: Any camera
        {
          video: true,
          audio: false
        },
        // Try 4: Minimal constraints
        {
          video: { width: 320, height: 240 },
          audio: false
        }
      ].filter(Boolean);
      
      let success = false;
      
      for (const constraint of constraints) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia(constraint as MediaStreamConstraints);
          
          setCameraStream(stream);
          setCameraEnabled(true);
          setError('');
          
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            await videoRef.current.play();
          }
          
          success = true;
          break;
        } catch (err) {
          console.log('Camera attempt failed:', err);
          continue;
        }
      }
      
      if (!success) {
        setError('Could not access camera. It may be in use by another application. Please close other apps using the camera (Zoom, Teams, etc.) and try again.');
        setCameraEnabled(false);
      }
    }
  };

  const handleJoin = () => {
    if (!roomCode) return;

    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
    }

    const state = {
      cameraEnabled,
      micEnabled,
      accessibilityMode
    };
    
    navigate(`/call/${roomCode}`, { state });
  };

  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [cameraStream]);

  if (isValidating) {
    return (
      <div className="flex items-center justify-center h-screen bg-meet-dark">
        <div className="text-white text-xl">Validating room...</div>
      </div>
    );
  }

  if (error && !error.includes('Camera')) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-meet-dark">
        <div className="text-red-500 text-xl mb-4">{error}</div>
        <button
          onClick={() => navigate('/')}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Back to Home
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-meet-dark p-8">
      <div className="max-w-2xl w-full bg-meet-gray rounded-lg shadow-xl p-8">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-white mb-2">Ready to join?</h1>
          <div className="flex items-center justify-center gap-2">
            <span className="text-gray-400">Room code:</span>
            <span className="text-blue-400 font-mono text-xl">{roomCode}</span>
            <button
              onClick={() => navigator.clipboard.writeText(roomCode || '')}
              className="px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-600"
              title="Copy room code"
            >
              📋 Copy
            </button>
          </div>
        </div>

        <div className="mb-6">
          <div className="aspect-video bg-black rounded-lg overflow-hidden relative">
            {cameraEnabled && cameraStream ? (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover mirror"
                style={{ transform: 'scaleX(-1)' }}
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="text-6xl mb-4">📷</div>
                  <div className="text-gray-400">
                    {cameraEnabled ? 'Loading camera...' : 'Camera preview off'}
                  </div>
                </div>
              </div>
            )}
          </div>
          
          <button
            onClick={toggleCameraPreview}
            className="mt-3 w-full px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
          >
            {cameraEnabled ? '📹 Turn off camera preview' : '📷 Turn on camera preview'}
          </button>
        </div>

        {error && (error.includes('Camera') || error.includes('camera')) && (
          <div className="mb-4 p-3 bg-yellow-900 border border-yellow-700 rounded-lg">
            <div className="text-yellow-200 text-sm">{error}</div>
            <div className="text-yellow-300 text-xs mt-2">
              💡 Tip: Close other apps using camera (Zoom, Teams, Skype) and refresh this page
            </div>
          </div>
        )}

        <div className="space-y-3 mb-6">
          <label className="flex items-center gap-3 p-3 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-600">
            <input
              type="checkbox"
              checked={micEnabled}
              onChange={(e) => setMicEnabled(e.target.checked)}
              className="w-5 h-5"
            />
            <span className="text-white">🎤 Microphone</span>
          </label>

          <label className="flex items-center gap-3 p-3 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-600">
            <input
              type="checkbox"
              checked={cameraEnabled}
              onChange={(e) => {
                if (!e.target.checked && cameraStream) {
                  cameraStream.getTracks().forEach(track => track.stop());
                  setCameraStream(null);
                }
                setCameraEnabled(e.target.checked);
              }}
              className="w-5 h-5"
            />
            <span className="text-white">📹 Camera</span>
          </label>

          <label className="flex items-center gap-3 p-3 bg-purple-900 rounded-lg cursor-pointer hover:bg-purple-800">
            <input
              type="checkbox"
              checked={accessibilityMode}
              onChange={(e) => setAccessibilityMode(e.target.checked)}
              className="w-5 h-5"
            />
            <span className="text-white">🧏 Accessibility Mode (Sign Language Recognition)</span>
          </label>
        </div>

        <button
          onClick={handleJoin}
          className="w-full px-6 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 transition-colors"
        >
          Join Meeting
        </button>

        <div className="mt-4 text-center text-gray-400 text-sm">
          By joining, you agree to allow camera and microphone access if enabled.
        </div>
      </div>
    </div>
  );
}
