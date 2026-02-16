import { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Video, VideoOff, Moon, Sun, Eye } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';

export default function PreJoinLobby() {
  const [searchParams] = useSearchParams();
  const roomCode = searchParams.get('room') || '';
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { user } = useAuth();
  
  const [displayName, setDisplayName] = useState(user?.name || '');
  const [accessibilityMode, setAccessibilityMode] = useState(false);
  const [cameraOn, setCameraOn] = useState(false);
  
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState<string>('');
  const [isJoining, setIsJoining] = useState(false);
  const [isLoadingCamera, setIsLoadingCamera] = useState(false);
  
  const videoRef = useRef<HTMLVideoElement>(null);

  const canJoin = displayName.trim().length >= 1 && !isJoining;

  const handleCameraToggle = async () => {
    if (cameraOn && cameraStream) {
      // Turn OFF camera
      cameraStream.getTracks().forEach(track => track.stop());
      setCameraStream(null);
      setCameraOn(false);
      setCameraError('');
    } else {
      // Turn ON camera
      setIsLoadingCamera(true);
      setCameraError('');
      
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { 
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: 'user'
          },
          audio: false
        });
        
        setCameraStream(stream);
        setCameraOn(true);
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
      } catch (err: any) {
        let errorMessage = 'Could not access camera. ';
        
        if (err.name === 'NotAllowedError') {
          errorMessage = 'Camera access denied. Please allow camera permissions in your browser.';
        } else if (err.name === 'NotFoundError') {
          errorMessage = 'No camera found. Please connect a camera device.';
        } else if (err.name === 'NotReadableError') {
          errorMessage = 'Camera is in use by another application.';
        } else {
          errorMessage = 'Camera access failed. Please check your camera settings.';
        }
        
        setCameraError(errorMessage);
        setCameraOn(false);
      } finally {
        setIsLoadingCamera(false);
      }
    }
  };

  const handleJoin = async () => {
    if (!canJoin) return;
    
    setIsJoining(true);
    
    try {
      // Clean up camera preview
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
      
      // Navigate to call
      navigate(`/call/${roomCode}`, {
        state: {
          displayName,
          accessibilityMode,
          cameraEnabled: false, // Camera starts OFF in meeting
          micEnabled: true,
        }
      });
    } catch (error) {
      console.error('Failed to join meeting:', error);
      alert('Failed to join meeting. Please try again.');
      setIsJoining(false);
    }
  };

  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [cameraStream]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors flex items-center justify-center p-4">
      {/* Theme Toggle */}
      <button
        onClick={toggleTheme}
        className="absolute top-6 right-6 p-3 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
        aria-label="Toggle theme"
      >
        {theme === 'dark' ? (
          <Sun className="w-5 h-5 text-yellow-500" />
        ) : (
          <Moon className="w-5 h-5 text-gray-700" />
        )}
      </button>

      <div className="max-w-2xl w-full bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 border border-gray-200 dark:border-gray-700">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Ready to join?</h1>
          <p className="text-gray-600 dark:text-gray-400">Room: {roomCode}</p>
        </div>

        {/* Camera Preview */}
        <div className="mb-6">
          <div className="aspect-video bg-gray-900 rounded-xl overflow-hidden relative mb-4">
            {cameraOn && cameraStream ? (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
                style={{ transform: 'scaleX(-1)' }}
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <VideoOff className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                  <p className="text-gray-400">
                    {isLoadingCamera ? 'Starting camera...' : 'Camera is off'}
                  </p>
                </div>
              </div>
            )}
          </div>
          
          <button
            onClick={handleCameraToggle}
            disabled={isLoadingCamera}
            className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {cameraOn ? <VideoOff className="w-5 h-5" /> : <Video className="w-5 h-5" />}
            {isLoadingCamera ? 'Starting camera...' : 
             cameraOn ? 'Turn off camera' : 'Turn on camera'}
          </button>
          
          {cameraError && (
            <div className="mt-3 p-3 bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 dark:border-yellow-700 rounded-lg">
              <p className="text-yellow-800 dark:text-yellow-200 text-sm">{cameraError}</p>
            </div>
          )}
        </div>

        {/* Name Input */}
        <div className="mb-6">
          <label htmlFor="displayName" className="block text-gray-700 dark:text-gray-300 text-sm font-medium mb-2">
            Your Name
          </label>
          <input
            id="displayName"
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Enter your name"
            className="w-full px-4 py-3 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            maxLength={50}
            required
          />
        </div>

        {/* Accessibility Toggle */}
        <div className="mb-6">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={accessibilityMode}
              onChange={(e) => setAccessibilityMode(e.target.checked)}
              className="w-5 h-5 text-purple-600 focus:ring-2 focus:ring-purple-500 rounded"
            />
            <Eye className="w-5 h-5 text-purple-600" />
            <span className="text-gray-700 dark:text-gray-300 text-sm font-medium">
              Enable Sign Language Recognition
            </span>
          </label>
        </div>

        {/* Join Button */}
        <button
          onClick={handleJoin}
          disabled={!canJoin}
          className={`w-full px-6 py-4 text-lg font-semibold rounded-lg transition-colors ${
            canJoin
              ? 'bg-green-600 text-white hover:bg-green-700'
              : 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
          }`}
        >
          {isJoining ? 'Joining...' : 'Join Meeting'}
        </button>
      </div>
    </div>
  );
}