import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Video, User, Accessibility, Camera, CameraOff, AlertCircle, Plus } from 'lucide-react';

export default function PreJoinLobby() {
  const { roomCode: urlRoomCode } = useParams<{ roomCode: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Get room code from URL params or query params
  const initialRoomCode = urlRoomCode || searchParams.get('room') || '';
  
  // Form state
  const [room_code, setRoom_code] = useState(initialRoomCode);
  const [display_name, setDisplay_name] = useState(user?.name || '');
  const [accessibility_mode, setAccessibility_mode] = useState(false);
  const [camera_preview_granted, setCamera_preview_granted] = useState(false);
  
  // UI state
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState<string>('');
  const [isJoining, setIsJoining] = useState(false);
  const [isLoadingCamera, setIsLoadingCamera] = useState(false);
  const [isCreatingRoom, setIsCreatingRoom] = useState(false);
  const [roomNotFound, setRoomNotFound] = useState(false);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const initializingRef = useRef(false);

  // Validation
  const isRoomCodeValid = room_code.trim().length >= 3;
  const isDisplayNameValid = display_name.trim().length >= 1;
  const canJoin = isRoomCodeValid && isDisplayNameValid && !isJoining;

  // Auto-generate room code if "Create Meeting" was clicked
  useEffect(() => {
    const shouldCreateRoom = searchParams.get('create') === 'true';
    if (shouldCreateRoom && !room_code) {
      handleCreateRoom();
    }
  }, []);

  // Create new room
  const handleCreateRoom = async () => {
    console.log('[PreJoinLobby] Creating new room');
    setIsCreatingRoom(true);
    setRoomNotFound(false);
    try {
      const userId = user?.id || `user_${Date.now()}`;
      console.log('[PreJoinLobby] Calling API to create room', { userId, accessibility_mode });
      const response = await api.createRoom(userId, accessibility_mode);
      console.log('[PreJoinLobby] Room created successfully', response);
      setRoom_code(response.room_code);
      setIsCreatingRoom(false);
    } catch (error) {
      console.error('[PreJoinLobby] Failed to create room:', error);
      alert('Failed to create room. Please check if backend server is running at http://localhost:8001');
      setIsCreatingRoom(false);
    }
  };

  // Create room with specific code
  const handleCreateRoomWithCode = async () => {
    if (!room_code.trim()) return;
    
    console.log('[PreJoinLobby] Creating room with specific code', { room_code });
    setIsCreatingRoom(true);
    setRoomNotFound(false);
    try {
      const userId = user?.id || `user_${Date.now()}`;
      console.log('[PreJoinLobby] Calling API to create room with code');
      const response = await api.createRoom(userId, accessibility_mode);
      // Use the entered code instead of generated one
      console.log('[PreJoinLobby] Room created, using entered code', room_code);
      setRoom_code(room_code.toUpperCase());
      setIsCreatingRoom(false);
    } catch (error) {
      console.error('[PreJoinLobby] Failed to create room:', error);
      alert('Failed to create room. Please try again.');
      setIsCreatingRoom(false);
    }
  };

  // Camera toggle
  const handleCameraToggle = async () => {
    console.log('[PreJoinLobby] Camera toggle clicked', { 
      currentState: camera_preview_granted,
      isInitializing: initializingRef.current 
    });
    
    if (camera_preview_granted && cameraStream) {
      // Turn OFF camera preview
      console.log('[PreJoinLobby] Turning OFF camera');
      cameraStream.getTracks().forEach(track => {
        console.log('[PreJoinLobby] Stopping track', { kind: track.kind, id: track.id });
        track.stop();
      });
      setCameraStream(null);
      setCamera_preview_granted(false);
      setCameraError('');
    } else {
      // Prevent concurrent initialization attempts
      if (initializingRef.current) {
        console.log('[PreJoinLobby] Camera initialization already in progress, ignoring click');
        return;
      }
      
      initializingRef.current = true;
      console.log('[PreJoinLobby] Starting camera initialization');
      
      // Turn ON camera preview
      setIsLoadingCamera(true);
      setCameraError('');
      
      try {
        console.log('[PreJoinLobby] Requesting camera permission');
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { 
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: 'user'
          },
          audio: false
        });
        
        // Verify stream tracks are active
        const tracks = stream.getTracks();
        console.log('[PreJoinLobby] MediaStream obtained', { trackCount: tracks.length });
        
        if (tracks.length === 0) {
          throw new Error('No tracks found in MediaStream');
        }
        
        const videoTrack = tracks.find(track => track.kind === 'video');
        if (!videoTrack || videoTrack.readyState !== 'live') {
          console.error('[PreJoinLobby] Video track not ready', { 
            hasTrack: !!videoTrack, 
            readyState: videoTrack?.readyState 
          });
          throw new Error('Video track is not in live state');
        }
        
        console.log('[PreJoinLobby] Video track is live', { 
          id: videoTrack.id, 
          label: videoTrack.label 
        });
        
        setCameraStream(stream);
        setCamera_preview_granted(true);
        
        if (videoRef.current) {
          console.log('[PreJoinLobby] Setting video element srcObject');
          videoRef.current.srcObject = stream;
          
          // Wait for video element to be ready before playing
          await new Promise<void>((resolve, reject) => {
            if (videoRef.current) {
              console.log('[PreJoinLobby] Waiting for video metadata to load');
              videoRef.current.onloadedmetadata = () => {
                console.log('[PreJoinLobby] Video metadata loaded');
                resolve();
              };
              
              // Timeout after 5 seconds
              setTimeout(() => {
                console.error('[PreJoinLobby] Timeout waiting for video metadata');
                reject(new Error('Timeout waiting for video metadata'));
              }, 5000);
            } else {
              console.error('[PreJoinLobby] videoRef.current is null');
              reject(new Error('Video element not available'));
            }
          });
          
          console.log('[PreJoinLobby] Attempting to play video');
          
          // Call play() with proper error handling
          if (videoRef.current) {
            try {
              await videoRef.current.play();
              console.log('[PreJoinLobby] Video playback started successfully');
            } catch (playError: any) {
              console.error('[PreJoinLobby] Video play() failed:', playError);
              
              if (playError.name === 'NotAllowedError') {
                throw new Error('Video playback not allowed. Please check browser permissions.');
              } else if (playError.name === 'NotSupportedError') {
                throw new Error('Video playback not supported by this browser.');
              } else {
                throw new Error(`Video playback failed: ${playError.message}`);
              }
            }
          } else {
            console.warn('[PreJoinLobby] videoRef.current is null after metadata load');
          }
        } else {
          console.warn('[PreJoinLobby] videoRef.current is null, cannot set srcObject');
        }
      } catch (err: any) {
        console.error('[PreJoinLobby] Camera initialization error:', err);
        
        let errorMessage = 'Could not access camera. ';
        
        if (err.name === 'NotAllowedError') {
          errorMessage = 'Camera access denied. Please allow camera permissions and try again.';
        } else if (err.name === 'NotFoundError') {
          errorMessage = 'No camera found. Please connect a camera device.';
        } else if (err.name === 'NotReadableError') {
          errorMessage = 'Camera is in use by another application. Please close other apps using the camera.';
        } else {
          errorMessage = err.message || 'Camera access failed. Please check your camera settings.';
        }
        
        console.error('[PreJoinLobby] Setting error message:', errorMessage);
        setCameraError(errorMessage);
        setCamera_preview_granted(false);
        
        // Clean up stream if it was created
        if (cameraStream) {
          console.log('[PreJoinLobby] Cleaning up failed stream');
          cameraStream.getTracks().forEach(track => track.stop());
          setCameraStream(null);
        }
      } finally {
        console.log('[PreJoinLobby] Camera initialization complete');
        setIsLoadingCamera(false);
        initializingRef.current = false;
      }
    }
  };

  // Join meeting
  const handleJoin = async () => {
    if (!canJoin) return;
    
    console.log('[PreJoinLobby] Joining meeting', { room_code, display_name });
    setIsJoining(true);
    setRoomNotFound(false);
    
    try {
      // Validate room exists
      console.log('[PreJoinLobby] Validating room');
      const roomValidation = await api.validateRoom(room_code);
      console.log('[PreJoinLobby] Room validation result', roomValidation);
      
      if (!roomValidation.valid) {
        console.warn('[PreJoinLobby] Room not found');
        setRoomNotFound(true);
        setIsJoining(false);
        return;
      }
      
      // Clean up camera preview
      if (cameraStream) {
        console.log('[PreJoinLobby] Cleaning up camera preview before joining');
        cameraStream.getTracks().forEach(track => track.stop());
      }
      
      // Store session state and navigate
      const sessionState = {
        room_code,
        display_name,
        accessibility_mode,
        camera_preview_granted,
        displayName: display_name,
        cameraEnabled: camera_preview_granted,
        micEnabled: true,
        accessibilityMode: accessibility_mode
      };
      
      console.log('[PreJoinLobby] Navigating to call page', sessionState);
      navigate(`/call/${room_code}`, { state: sessionState });
    } catch (error) {
      console.error('[PreJoinLobby] Failed to join meeting:', error);
      setRoomNotFound(true);
      setIsJoining(false);
    }
  };

  // Cleanup camera on unmount
  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [cameraStream]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-navy-950 p-8">
      <div className="max-w-md w-full bg-navy-900/50 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl p-8">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
            <Video className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Meeting Lobby</h1>
          <p className="text-gray-400 text-sm">Prepare to join your meeting</p>
        </div>

        {/* Room Code */}
        <div className="mb-6">
          <label htmlFor="room_code" className="block text-white text-sm font-medium mb-2">
            Room Code
          </label>
          <div className="flex gap-2">
            <input
              id="room_code"
              type="text"
              value={room_code}
              onChange={(e) => {
                setRoom_code(e.target.value.toUpperCase());
                setRoomNotFound(false);
              }}
              placeholder="Enter room code"
              className={`flex-1 px-4 py-3 bg-navy-800 text-white rounded-lg border focus:outline-none focus:ring-2 transition-colors ${
                room_code && !isRoomCodeValid 
                  ? 'border-red-500 focus:ring-red-400' 
                  : roomNotFound
                  ? 'border-yellow-500 focus:ring-yellow-400'
                  : 'border-white/10 focus:ring-blue-400'
              }`}
              maxLength={20}
              required
              disabled={isCreatingRoom}
            />
            <button
              onClick={handleCreateRoom}
              disabled={isCreatingRoom || room_code.length > 0}
              className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Generate new room code"
            >
              <Plus className="w-5 h-5" />
            </button>
          </div>
          {room_code && !isRoomCodeValid && (
            <div className="mt-2 text-red-400 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              Room code must be at least 3 characters
            </div>
          )}
          {roomNotFound && (
            <div className="mt-3 p-3 bg-yellow-900/30 border border-yellow-700/50 rounded-lg">
              <div className="text-yellow-200 text-sm mb-2 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                Room not found
              </div>
              <button
                onClick={handleCreateRoomWithCode}
                disabled={isCreatingRoom}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm flex items-center justify-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Create room with this code
              </button>
            </div>
          )}
          {isCreatingRoom && (
            <div className="mt-2 text-blue-400 text-sm">
              Creating new room...
            </div>
          )}
        </div>

        {/* Name */}
        <div className="mb-6">
          <label htmlFor="display_name" className="block text-white text-sm font-medium mb-2">
            Your Name
          </label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              id="display_name"
              type="text"
              value={display_name}
              onChange={(e) => setDisplay_name(e.target.value)}
              placeholder="Enter your name"
              className={`w-full pl-12 pr-4 py-3 bg-navy-800 text-white rounded-lg border focus:outline-none focus:ring-2 transition-colors ${
                display_name && !isDisplayNameValid 
                  ? 'border-red-500 focus:ring-red-400' 
                  : 'border-white/10 focus:ring-blue-400'
              }`}
              maxLength={50}
              required
            />
          </div>
        </div>

        {/* Accessibility */}
        <div className="mb-6">
          <label className="flex items-center gap-3 cursor-pointer p-4 bg-navy-800 rounded-lg hover:bg-navy-700 transition-colors">
            <input
              type="checkbox"
              checked={accessibility_mode}
              onChange={(e) => setAccessibility_mode(e.target.checked)}
              className="w-5 h-5 focus:ring-2 focus:ring-purple-400"
            />
            <div className="flex-1">
              <span className="text-white text-sm font-medium block">Sign Language Mode</span>
              <span className="text-gray-400 text-xs">Enable real-time ASL translation</span>
            </div>
            <Accessibility className={`w-6 h-6 ${accessibility_mode ? 'text-purple-400' : 'text-gray-400'}`} />
          </label>
        </div>

        {/* Camera Preview */}
        <div className="mb-6">
          <div className="text-white text-sm font-medium mb-2">Camera Preview</div>
          
          <div className="aspect-video bg-black rounded-lg overflow-hidden relative mb-3">
            {camera_preview_granted && cameraStream ? (
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
                  <Camera className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                  <div className="text-gray-400 text-sm">
                    {isLoadingCamera ? 'Starting camera...' : 'Camera preview off'}
                  </div>
                </div>
              </div>
            )}
          </div>
          
          <button
            onClick={handleCameraToggle}
            disabled={isLoadingCamera}
            className="w-full px-4 py-2 bg-navy-800 text-white rounded-lg hover:bg-navy-700 focus:ring-2 focus:ring-blue-400 disabled:opacity-50 transition-colors text-sm flex items-center justify-center gap-2"
          >
            {camera_preview_granted ? <CameraOff className="w-4 h-4" /> : <Camera className="w-4 h-4" />}
            {isLoadingCamera ? 'Starting camera...' : 
             camera_preview_granted ? 'Turn off camera preview' : 'Turn on camera preview'}
          </button>
          
          {cameraError && (
            <div className="mt-3 p-3 bg-yellow-900/30 border border-yellow-700/50 rounded-lg">
              <div className="text-yellow-200 text-sm flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                {cameraError}
              </div>
              <div className="text-yellow-300 text-xs mt-2">
                Tip: Check browser permissions or close other apps using the camera
              </div>
            </div>
          )}
        </div>

        {/* Join Button */}
        <button
          onClick={handleJoin}
          disabled={!canJoin}
          className={`w-full px-6 py-4 text-lg font-semibold rounded-lg transition-all flex items-center justify-center gap-2 ${
            canJoin
              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 focus:ring-4 focus:ring-blue-400 shadow-neon-blue'
              : 'bg-gray-600 text-gray-400 cursor-not-allowed'
          }`}
        >
          <Video className="w-5 h-5" />
          {isJoining ? 'Joining Meeting...' : 'JOIN MEETING'}
        </button>
        
        {!canJoin && (
          <div className="mt-4 text-center text-gray-400 text-xs">
            Please fill in all required fields to join
          </div>
        )}
      </div>
    </div>
  );
}
