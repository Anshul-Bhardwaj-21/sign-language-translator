import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../services/api';

export default function PreJoinLobby() {
  const { roomCode: urlRoomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  
  // FIX #1: Use exact session_state field names as specified
  const [room_code, setRoom_code] = useState(urlRoomCode || '');
  const [display_name, setDisplay_name] = useState('');
  const [accessibility_mode, setAccessibility_mode] = useState(false);
  const [camera_preview_granted, setCamera_preview_granted] = useState(false);
  
  // UI state
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState<string>('');
  const [isJoining, setIsJoining] = useState(false);
  const [isLoadingCamera, setIsLoadingCamera] = useState(false);
  
  const videoRef = useRef<HTMLVideoElement>(null);

  // FIX #2: Validate inputs in real-time to enable/disable Join button
  const isRoomCodeValid = room_code.trim().length >= 3; // Minimum length validation
  const isDisplayNameValid = display_name.trim().length >= 1; // Required field
  const canJoin = isRoomCodeValid && isDisplayNameValid && !isJoining;

  // FIX #3: Handle camera preview toggle - only for preview, NOT for meeting
  const handleCameraToggle = async () => {
    if (camera_preview_granted && cameraStream) {
      // Turn OFF camera preview
      cameraStream.getTracks().forEach(track => track.stop());
      setCameraStream(null);
      setCamera_preview_granted(false);
      setCameraError('');
    } else {
      // Turn ON camera preview - request permission
      setIsLoadingCamera(true);
      setCameraError('');
      
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { 
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: 'user'
          },
          audio: false // Preview only needs video
        });
        
        setCameraStream(stream);
        setCamera_preview_granted(true);
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
      } catch (err: any) {
        // FIX #4: Provide friendly error messages for camera permission denial
        let errorMessage = 'Could not access camera. ';
        
        if (err.name === 'NotAllowedError') {
          errorMessage = 'Camera access denied. Please allow camera permissions and try again.';
        } else if (err.name === 'NotFoundError') {
          errorMessage = 'No camera found. Please connect a camera device.';
        } else if (err.name === 'NotReadableError') {
          errorMessage = 'Camera is in use by another application. Please close other apps using the camera.';
        } else {
          errorMessage = 'Camera access failed. Please check your camera settings.';
        }
        
        setCameraError(errorMessage);
        setCamera_preview_granted(false);
      } finally {
        setIsLoadingCamera(false);
      }
    }
  };

  // FIX #5: Handle join meeting - store session state and navigate
  const handleJoin = async () => {
    if (!canJoin) return;
    
    setIsJoining(true);
    
    try {
      // FIX #6: Validate room exists before joining
      const roomValidation = await api.validateRoom(room_code);
      if (!roomValidation.valid) {
        alert('Room not found. Please check the room code.');
        setIsJoining(false);
        return;
      }
      
      // FIX #7: Clean up camera preview before navigation (camera will restart in meeting if needed)
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
      
      // FIX #8: Store session state with exact field names and navigate
      const sessionState = {
        room_code,
        display_name,
        accessibility_mode,
        camera_preview_granted, // This indicates user granted camera permission in lobby
        displayName: display_name, // For compatibility with VideoCallPage
        cameraEnabled: false, // Camera does NOT start until after join
        micEnabled: true,
        accessibilityMode: accessibility_mode
      };
      
      navigate(`/call/${room_code}`, { state: sessionState });
    } catch (error) {
      console.error('Failed to join meeting:', error);
      alert('Failed to join meeting. Please try again.');
      setIsJoining(false);
    }
  };

  // FIX #9: Cleanup camera on component unmount
  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [cameraStream]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-meet-dark p-8">
      <div className="max-w-md w-full bg-meet-gray rounded-lg shadow-xl p-8">
        {/* FIX #10: Clean header matching the ASCII layout */}
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-white mb-2">Meeting Lobby</h1>
        </div>

        {/* FIX #11: Room Code input at top as specified */}
        <div className="mb-6">
          <label htmlFor="room_code" className="block text-white text-sm font-medium mb-2">
            Room Code:
          </label>
          <input
            id="room_code"
            type="text"
            value={room_code}
            onChange={(e) => setRoom_code(e.target.value)}
            placeholder="Enter room code"
            className={`w-full px-4 py-3 bg-gray-700 text-white rounded-lg border focus:outline-none focus:ring-2 transition-colors ${
              room_code && !isRoomCodeValid 
                ? 'border-red-500 focus:ring-red-400' 
                : 'border-gray-600 focus:ring-blue-400'
            }`}
            maxLength={20}
            required
          />
          {room_code && !isRoomCodeValid && (
            <div className="mt-2 text-red-400 text-sm">
              Room code must be at least 3 characters
            </div>
          )}
        </div>

        {/* FIX #12: Name input as specified */}
        <div className="mb-6">
          <label htmlFor="display_name" className="block text-white text-sm font-medium mb-2">
            Name:
          </label>
          <input
            id="display_name"
            type="text"
            value={display_name}
            onChange={(e) => setDisplay_name(e.target.value)}
            placeholder="Enter your name"
            className={`w-full px-4 py-3 bg-gray-700 text-white rounded-lg border focus:outline-none focus:ring-2 transition-colors ${
              display_name && !isDisplayNameValid 
                ? 'border-red-500 focus:ring-red-400' 
                : 'border-gray-600 focus:ring-blue-400'
            }`}
            maxLength={50}
            required
          />
          {display_name && !isDisplayNameValid && (
            <div className="mt-2 text-red-400 text-sm">
              Please enter your name
            </div>
          )}
        </div>

        {/* FIX #13: Clear Accessibility toggle as specified */}
        <div className="mb-6">
          <label className="flex items-center gap-3 cursor-pointer">
            <span className="text-white text-sm font-medium">Accessibility:</span>
            <input
              type="checkbox"
              checked={accessibility_mode}
              onChange={(e) => setAccessibility_mode(e.target.checked)}
              className="w-5 h-5 focus:ring-2 focus:ring-purple-400"
            />
            <span className="text-gray-300 text-sm">
              {accessibility_mode ? 'Enabled' : 'Disabled'}
            </span>
          </label>
        </div>

        {/* FIX #14: Camera Preview section as specified */}
        <div className="mb-6">
          <div className="text-white text-sm font-medium mb-2">Camera Preview:</div>
          
          {/* Video preview window */}
          <div className="aspect-video bg-black rounded-lg overflow-hidden relative mb-3">
            {camera_preview_granted && cameraStream ? (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
                style={{ transform: 'scaleX(-1)' }} // Mirror effect
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="text-4xl mb-2">📷</div>
                  <div className="text-gray-400 text-sm">
                    {isLoadingCamera ? 'Starting camera...' : 'Camera preview off'}
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Camera toggle button */}
          <button
            onClick={handleCameraToggle}
            disabled={isLoadingCamera}
            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 focus:ring-2 focus:ring-blue-400 disabled:opacity-50 text-sm"
          >
            {isLoadingCamera ? 'Starting camera...' : 
             camera_preview_granted ? 'Turn off camera preview' : 'Turn on camera preview'}
          </button>
          
          {/* FIX #15: Friendly camera error messages */}
          {cameraError && (
            <div className="mt-3 p-3 bg-yellow-900 border border-yellow-700 rounded-lg">
              <div className="text-yellow-200 text-sm">{cameraError}</div>
              <div className="text-yellow-300 text-xs mt-2">
                💡 Tip: Check browser permissions or close other apps using the camera
              </div>
            </div>
          )}
        </div>

        {/* FIX #16: Join button disabled until valid as specified */}
        <button
          onClick={handleJoin}
          disabled={!canJoin}
          className={`w-full px-6 py-4 text-lg font-semibold rounded-lg transition-colors ${
            canJoin
              ? 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-4 focus:ring-blue-400'
              : 'bg-gray-600 text-gray-400 cursor-not-allowed'
          }`}
        >
          {isJoining ? 'Joining Meeting...' : 'JOIN MEETING'}
        </button>
        
        {/* Helper text */}
        <div className="mt-4 text-center text-gray-400 text-xs">
          {!canJoin && 'Please fill in all required fields to join'}
        </div>
      </div>
    </div>
  );
}