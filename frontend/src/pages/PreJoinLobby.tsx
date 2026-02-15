import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../services/api';
import { FormValidation, ValidationErrors } from '../utils/validation';
import { SessionPreferencesImpl } from '../types/navigation';

export default function PreJoinLobby() {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  
  // Form state
  const [displayName, setDisplayName] = useState('');
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [micEnabled, setMicEnabled] = useState(true);
  const [accessibilityMode, setAccessibilityMode] = useState(false);
  
  // Camera and validation state
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string>('');
  const [isValidating, setIsValidating] = useState(true);
  const [isJoining, setIsJoining] = useState(false);
  const [isCameraInitializing, setIsCameraInitializing] = useState(false);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  
  // Camera device selection state
  const [selectedCamera, setSelectedCamera] = useState<string>('');
  
  // Screen reader announcements
  const [announcement, setAnnouncement] = useState<string>('');
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const formValidation = useRef(new FormValidation());

  // Display name validation handlers
  const handleDisplayNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setDisplayName(value);
    
    // Validate on change and update errors
    const result = formValidation.current.validateDisplayName(value);
    setValidationErrors(formValidation.current.getErrors());
    
    // Clear general error if display name becomes valid
    if (result.isValid && error.includes('name')) {
      setError('');
    }
  };

  const handleDisplayNameBlur = () => {
    // Validate on blur for immediate feedback
    formValidation.current.validateDisplayName(displayName);
    setValidationErrors(formValidation.current.getErrors());
  };

  const toggleCameraPreview = async () => {
    if (cameraEnabled) {
      // Stop camera - turn OFF
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
      // Start camera - turn ON (only when user explicitly enables)
      setIsCameraInitializing(true);
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
      let lastError: any = null;
      
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
          lastError = err;
          console.log('Camera attempt failed:', err);
          continue;
        }
      }
      
      if (!success) {
        // Provide specific error messages based on error type
        let errorMessage = 'Could not access camera. ';
        
        if (lastError?.name === 'NotAllowedError') {
          errorMessage = 'Camera access denied. Please allow camera permissions in your browser settings and try again.';
        } else if (lastError?.name === 'NotFoundError') {
          errorMessage = 'No camera found. Please connect a camera device and try again.';
        } else if (lastError?.name === 'NotReadableError') {
          errorMessage = 'Camera is already in use by another application. Please close other apps using the camera (Zoom, Teams, etc.) and try again.';
        } else if (lastError?.name === 'OverconstrainedError') {
          errorMessage = 'Camera does not support the required settings. Try using a different camera.';
        } else {
          errorMessage = 'Could not access camera. It may be in use by another application. Please close other apps using the camera (Zoom, Teams, etc.) and try again.';
        }
        
        setError(errorMessage);
        setCameraEnabled(false);
      }
      
      setIsCameraInitializing(false);
    }
  };

  // Camera retry handler
  const retryCameraAccess = async () => {
    setError('');
    await toggleCameraPreview();
  };

  const handleJoin = () => {
    if (!roomCode) return;

    // Validate form before joining
    const formResult = formValidation.current.validateForm(displayName, roomCode);
    setValidationErrors(formValidation.current.getErrors());

    if (!formResult.isValid) {
      setError('Please fix the errors above before joining');
      return;
    }

    // Additional validation for display name
    if (!displayName.trim()) {
      setError('Please enter your display name');
      return;
    }

    setIsJoining(true);
    setError('');

    // Clean up camera stream before navigation
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
    }

    // Create session preferences and navigate
    const sessionPrefs = new SessionPreferencesImpl(
      displayName.trim(),
      cameraEnabled,
      micEnabled,
      accessibilityMode
    );
    
    navigate(`/call/${roomCode}`, { state: sessionPrefs.toNavigationState() });
  };

  // Announce important state changes
  useEffect(() => {
    if (isJoining) {
      setAnnouncement('Joining meeting, please wait...');
    } else if (isCameraInitializing) {
      setAnnouncement('Starting camera, please wait...');
    } else if (error && !error.includes('Starting camera')) {
      setAnnouncement(`Error: ${error}`);
    } else {
      setAnnouncement('');
    }
  }, [isJoining, isCameraInitializing, error]);

  // Keyboard navigation handler
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Only handle if not typing in input
      if (e.target instanceof HTMLInputElement) return;
      
      switch (e.key.toLowerCase()) {
        case 'enter':
          if (!isJoining && !isCameraInitializing && displayName.trim() && !isValidating) {
            handleJoin();
          }
          break;
        case 'escape':
          if (!isJoining) {
            navigate('/');
          }
          break;
        case 'c':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            navigator.clipboard.writeText(roomCode || '');
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isJoining, isCameraInitializing, displayName, isValidating, navigate, roomCode]);

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
        console.error('Room validation error:', err);
        if (err instanceof Error) {
          if (err.message.includes('fetch')) {
            setError('Failed to validate room - please check your internet connection');
          } else {
            setError('Failed to validate room - server may be unavailable');
          }
        } else {
          setError('Failed to validate room');
        }
      } finally {
        setIsValidating(false);
      }
    };

    validate();
    
    // Get available cameras WITHOUT requesting access
    navigator.mediaDevices.enumerateDevices()
      .then(devices => {
        const cameras = devices.filter(device => device.kind === 'videoinput');
        if (cameras.length > 0) {
          setSelectedCamera(cameras[0].deviceId);
        }
      })
      .catch(err => console.log('Failed to enumerate devices:', err));
  }, [roomCode]);

  useEffect(() => {
    return () => {
      // Cleanup camera resources on component unmount
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => {
          track.stop();
          track.enabled = false;
        });
      }
    };
  }, [cameraStream]);

  // Additional cleanup effect for navigation
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      // Final cleanup
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

  if (error && !error.includes('Camera') && !error.includes('camera') && !error.includes('name') && !error.includes('fix')) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-meet-dark">
        <div className="max-w-md w-full bg-meet-gray rounded-lg shadow-xl p-8 text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <div className="text-red-400 text-xl mb-4">{error}</div>
          <div className="text-gray-400 text-sm mb-6">
            {error.includes('Room not found') && 'Please check the room code and try again.'}
            {error.includes('Room is full') && 'This meeting has reached its participant limit.'}
            {error.includes('internet connection') && 'Please check your internet connection and try again.'}
            {error.includes('server may be unavailable') && 'The server is temporarily unavailable. Please try again in a few moments.'}
            {error.includes('Failed to validate') && !error.includes('internet') && !error.includes('server') && 'Please check your internet connection and try again.'}
          </div>
          <div className="space-y-3">
            <button
              onClick={() => {
                setError('');
                setIsValidating(true);
                // Retry validation
                const validate = async () => {
                  if (!roomCode) return;
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
              }}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={() => navigate('/')}
              className="w-full px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              Back to Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-meet-dark p-8">
      {/* Screen reader announcements */}
      <div 
        aria-live="polite" 
        aria-atomic="true" 
        className="sr-only"
        role="status"
      >
        {announcement}
      </div>
      
      <div 
        className="max-w-2xl w-full bg-meet-gray rounded-lg shadow-xl p-8"
        role="main"
        aria-labelledby="lobby-title"
        aria-describedby="lobby-description"
      >
        <div className="mb-6 text-center">
          <h1 id="lobby-title" className="text-2xl font-bold text-white mb-2">Ready to join?</h1>
          <div 
            id="lobby-description" 
            className="flex items-center justify-center gap-2"
            role="region"
            aria-label="Room information"
          >
            <span className="text-gray-400">Room code:</span>
            <span className="text-blue-400 font-mono text-xl" aria-label={`Room code: ${roomCode}`}>{roomCode}</span>
            <button
              onClick={() => {
                navigator.clipboard.writeText(roomCode || '');
                setAnnouncement('Room code copied to clipboard');
              }}
              className="px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-600 focus:ring-2 focus:ring-blue-400"
              title="Copy room code (Ctrl+C)"
              aria-label="Copy room code to clipboard"
            >
              📋 Copy
            </button>
          </div>
        </div>

        {/* Display Name Input */}
        <div className="mb-6">
          <label htmlFor="displayName" className="block text-white text-sm font-medium mb-2">
            Your name
          </label>
          <input
            id="displayName"
            type="text"
            value={displayName}
            onChange={handleDisplayNameChange}
            onBlur={handleDisplayNameBlur}
            placeholder="Enter your display name"
            className={`w-full px-4 py-3 bg-gray-700 text-white rounded-lg border focus:outline-none focus:ring-2 transition-colors ${
              validationErrors.displayName 
                ? 'border-red-500 focus:ring-red-400 focus:border-red-400' 
                : 'border-gray-600 focus:ring-blue-400 focus:border-blue-500'
            }`}
            maxLength={50}
            required
            aria-describedby={validationErrors.displayName ? 'displayName-error' : undefined}
          />
          {validationErrors.displayName && (
            <div 
              id="displayName-error" 
              className="mt-2 text-red-400 text-sm"
              role="alert"
              aria-live="polite"
            >
              {validationErrors.displayName}
            </div>
          )}
        </div>

        <div className="mb-6" role="region" aria-labelledby="camera-section">
          <h2 id="camera-section" className="sr-only">Camera Preview</h2>
          <div 
            className="aspect-video bg-black rounded-lg overflow-hidden relative"
            role="img"
            aria-label={cameraEnabled && cameraStream ? 'Camera preview active' : 'Camera preview inactive'}
          >
            {cameraEnabled && cameraStream ? (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover mirror"
                style={{ transform: 'scaleX(-1)' }}
                aria-label="Your camera preview"
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="text-6xl mb-4" aria-hidden="true">📷</div>
                  <div className="text-gray-400">
                    {cameraEnabled ? 'Loading camera...' : 'Camera preview off'}
                  </div>
                </div>
              </div>
            )}
          </div>
          
          <button
            onClick={toggleCameraPreview}
            disabled={isCameraInitializing}
            className="mt-3 w-full px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 focus:ring-2 focus:ring-blue-400 disabled:opacity-50"
            aria-label={cameraEnabled ? 'Turn off camera preview' : 'Turn on camera preview'}
            aria-describedby="camera-toggle-help"
          >
            {isCameraInitializing ? '⏳ Starting camera...' : 
             cameraEnabled ? '📹 Turn off camera preview' : '📷 Turn on camera preview'}
          </button>
          <div id="camera-toggle-help" className="sr-only">
            Camera preview is optional and off by default for privacy
          </div>
        </div>

        {error && (error.includes('Camera') || error.includes('camera')) && (
          <div className="mb-4 p-3 bg-yellow-900 border border-yellow-700 rounded-lg">
            <div className="text-yellow-200 text-sm">{error}</div>
            <div className="text-yellow-300 text-xs mt-2">
              {error.includes('denied') && '💡 Tip: Click the camera icon in your browser address bar to allow camera access'}
              {error.includes('in use') && '💡 Tip: Close other apps using camera (Zoom, Teams, Skype) and refresh this page'}
              {error.includes('No camera found') && '💡 Tip: Connect a camera device and refresh this page'}
              {error.includes('does not support') && '💡 Tip: Try using a different camera or update your browser'}
              {!error.includes('denied') && !error.includes('in use') && !error.includes('No camera found') && !error.includes('does not support') && 
               '💡 Tip: Close other apps using camera (Zoom, Teams, Skype) and refresh this page'}
            </div>
            {error.includes('Could not access camera') && (
              <button
                onClick={retryCameraAccess}
                className="mt-3 px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 text-sm"
              >
                Try Again
              </button>
            )}
          </div>
        )}

        {error && !error.includes('Camera') && !error.includes('camera') && (
          <div className="mb-4 p-3 bg-red-900 border border-red-700 rounded-lg">
            <div className="text-red-200 text-sm">{error}</div>
          </div>
        )}

        <fieldset className="space-y-3 mb-6">
          <legend className="sr-only">Meeting preferences</legend>
          
          <label className="flex items-center gap-3 p-3 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-600 focus-within:ring-2 focus-within:ring-blue-400">
            <input
              type="checkbox"
              checked={micEnabled}
              onChange={(e) => setMicEnabled(e.target.checked)}
              className="w-5 h-5 focus:ring-2 focus:ring-blue-400"
              aria-describedby="mic-help"
            />
            <span className="text-white">🎤 Microphone</span>
            <div id="mic-help" className="sr-only">
              Enable microphone for audio communication
            </div>
          </label>

          <label className="flex items-center gap-3 p-3 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-600 focus-within:ring-2 focus-within:ring-blue-400">
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
              className="w-5 h-5 focus:ring-2 focus:ring-blue-400"
              aria-describedby="camera-help"
            />
            <span className="text-white">📹 Camera</span>
            <div id="camera-help" className="sr-only">
              Enable camera for video communication
            </div>
          </label>

          <label className="flex items-center gap-3 p-3 bg-purple-900 rounded-lg cursor-pointer hover:bg-purple-800 focus-within:ring-2 focus-within:ring-purple-400">
            <input
              type="checkbox"
              checked={accessibilityMode}
              onChange={(e) => setAccessibilityMode(e.target.checked)}
              className="w-5 h-5 focus:ring-2 focus:ring-purple-400"
              aria-describedby="accessibility-help"
            />
            <span className="text-white">🧏 Accessibility Mode (Sign Language Recognition)</span>
            <div id="accessibility-help" className="sr-only">
              Enable real-time sign language recognition and translation
            </div>
          </label>
        </fieldset>

        <div className="space-y-4" role="group" aria-labelledby="action-buttons">
          <h2 id="action-buttons" className="sr-only">Actions</h2>
          
          <button
            onClick={handleJoin}
            disabled={isJoining || isCameraInitializing || !displayName.trim() || isValidating}
            className={`w-full px-6 py-4 text-lg font-semibold rounded-lg transition-colors focus:ring-4 focus:ring-blue-400 ${
              isJoining || isCameraInitializing || !displayName.trim() || isValidating
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
            aria-label={
              isJoining ? 'Joining meeting in progress' :
              isCameraInitializing ? 'Camera initializing' :
              !displayName.trim() ? 'Enter display name to join' :
              isValidating ? 'Validating room' :
              'Join meeting'
            }
            aria-describedby="join-button-help"
          >
            {isJoining ? 'Joining Meeting...' : 
             isCameraInitializing ? 'Starting Camera...' :
             isValidating ? 'Validating...' :
             'Join Meeting'}
          </button>
          <div id="join-button-help" className="sr-only">
            Press Enter to join the meeting when ready
          </div>

          <button
            onClick={() => navigate('/')}
            disabled={isJoining}
            className="w-full px-6 py-3 bg-gray-700 text-white font-medium rounded-lg hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:ring-4 focus:ring-gray-400"
            aria-label="Cancel and return to home page"
            aria-describedby="cancel-button-help"
          >
            Cancel
          </button>
          <div id="cancel-button-help" className="sr-only">
            Press Escape to cancel and return to home page
          </div>
        </div>

        <div className="mt-4 text-center text-gray-400 text-sm">
          <p>By joining, you agree to allow camera and microphone access if enabled.</p>
          <div className="mt-2 text-xs">
            <span className="sr-only">Keyboard shortcuts:</span>
            <span aria-hidden="true">Enter: Join | Escape: Cancel | Ctrl+C: Copy room code</span>
          </div>
        </div>
      </div>
    </div>
  );
}