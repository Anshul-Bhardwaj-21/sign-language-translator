import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Video, VideoOff, Mic, MicOff, Phone, Monitor, MonitorOff,
  Accessibility, Hand, Eye, Sun, AlertTriangle, Keyboard
} from 'lucide-react';

interface LocationState {
  displayName?: string;
  cameraEnabled?: boolean;
  micEnabled?: boolean;
  accessibilityMode?: boolean;
}

interface DetectionQuality {
  lighting: 'good' | 'poor' | 'dark';
  distance: 'good' | 'too-close' | 'too-far';
  handVisible: boolean;
  faceVisible: boolean;
  confidence: number;
}

export default function VideoCallPageNew() {
  const [cameraError, setCameraError] = useState<string>('');
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state as LocationState) || {};
  
  const [displayName] = useState(state.displayName || 'Anonymous User');
  const [cameraEnabled, setCameraEnabled] = useState(state.cameraEnabled || false);
  const [micEnabled, setMicEnabled] = useState(state.micEnabled !== false);
  const [screenSharing, setScreenSharing] = useState(false);
  const [accessibilityMode, setAccessibilityMode] = useState(state.accessibilityMode || false);
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [isLoadingCamera, setIsLoadingCamera] = useState(false);
export default function VideoCallPageNew() {seState<string>('');
  const [handDetected, setHandDetected] = useState(false);
  const [faceDetected, setFaceDetected] = useState(false);
  const [detectionQuality, setDetectionQuality] = useState<DetectionQuality>({
    lighting: 'good',
    distance: 'good',
    handVisible: false,
    faceVisible: false,
    confidence: 0
  });
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [showDetectionOverlay, setShowDetectionOverlay] = useState(true);
  
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const initializingRef = useRef(false);

  const initializeCamera = useCallback(async () => {
    if (!cameraEnabled || initializingRef.current) return;
    initializingRef.current = true;
    setIsLoadingCamera(true);
    setCameraError('');

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
        audio: false
      });
      setLocalStream(stream);
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
        await localVideoRef.current.play();
      }
      setIsLoadingCamera(false);
      initializingRef.current = false;
    } catch (err) {
      setCameraError('Could not access camera');
      setIsLoadingCamera(false);
      setCameraEnabled(false);
      initializingRef.current = false;
    }
  }, [cameraEnabled]);

  const cleanupCamera = useCallback(() => {
    if (localStream) {
      localStream.getTracks().forEach(track => track.stop());
      setLocalStream(null);
    }
    if (localVideoRef.current) {
      localVideoRef.current.srcObject = null;
    }
  }, [localStream]);

  const handleToggleCamera = useCallback(() => {
    if (cameraEnabled) {
      cleanupCamera();
      setCameraEnabled(false);
    } else {
      setCameraEnabled(true);
    }
  }, [cameraEnabled, cleanupCamera]);

  const handleToggleMic = useCallback(() => {
    if (localStream) {
      localStream.getAudioTracks().forEach(track => {
        track.enabled = !micEnabled;
      });
    }
    setMicEnabled(!micEnabled);
  }, [localStream, micEnabled]);

  const handleToggleAccessibility = useCallback(() => {
    setAccessibilityMode(!accessibilityMode);
  }, [accessibilityMode]);

  const handleToggleScreenShare = useCallback(async () => {
    if (screenSharing) {
      setScreenSharing(false);
    } else {
      try {
        await navigator.mediaDevices.getDisplayMedia({ video: true });
        setScreenSharing(true);
      } catch (err) {
        console.error('Screen share failed');
      }
    }
  }, [screenSharing]);

  const handleLeave = useCallback(() => {
    if (window.confirm('Leave call?')) {
      cleanupCamera();
      navigate('/dashboard');
    }
  }, [cleanupCamera, navigate]);

  useEffect(() => {
    if (!accessibilityMode || !cameraEnabled) return;
    const interval = setInterval(() => {
      setHandDetected(Math.random() > 0.3);
      setFaceDetected(Math.random() > 0.2);
      setDetectionQuality({
        lighting: ['good', 'poor', 'dark'][Math.floor(Math.random() * 3)] as any,
        distance: ['good', 'too-close', 'too-far'][Math.floor(Math.random() * 3)] as any,
        handVisible: Math.random() > 0.3,
        faceVisible: Math.random() > 0.2,
        confidence: 0.7 + Math.random() * 0.3
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [accessibilityMode, cameraEnabled]);

  useEffect(() => {
    if (!accessibilityMode || !showDetectionOverlay || !canvasRef.current || !localVideoRef.current) return;
    const canvas = canvasRef.current;
    const video = localVideoRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const drawOverlay = () => {
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (faceDetected) {
        const faceX = canvas.width * 0.3;
        const faceY = canvas.height * 0.2;
        const faceW = canvas.width * 0.4;
        const faceH = canvas.height * 0.5;
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 3;
        ctx.strokeRect(faceX, faceY, faceW, faceH);
        ctx.fillStyle = '#3b82f6';
        ctx.fillRect(faceX, faceY - 25, 80, 25);
        ctx.fillStyle = '#ffffff';
        ctx.font = '14px sans-serif';
        ctx.fillText('Face', faceX + 5, faceY - 7);
      }

      if (handDetected) {
        const handX = canvas.width * 0.5;
        const handY = canvas.height * 0.6;
        const landmarks = [
          [handX, handY],
          [handX - 20, handY - 40],
          [handX, handY - 60],
          [handX + 20, handY - 55],
          [handX + 35, handY - 45],
          [handX + 45, handY - 30],
        ];
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(landmarks[0][0], landmarks[0][1]);
        landmarks.forEach(([x, y]) => ctx.lineTo(x, y));
        ctx.stroke();
        landmarks.forEach(([x, y]) => {
          ctx.fillStyle = '#10b981';
          ctx.beginPath();
          ctx.arc(x, y, 5, 0, 2 * Math.PI);
          ctx.fill();
        });
        ctx.fillStyle = '#10b981';
        ctx.fillRect(handX - 40, handY + 20, 80, 25);
        ctx.fillStyle = '#ffffff';
        ctx.font = '14px sans-serif';
        ctx.fillText('Hand', handX - 30, handY + 38);
      }
    };

    const animationId = requestAnimationFrame(function animate() {
      drawOverlay();
      requestAnimationFrame(animate);
    });
    return () => cancelAnimationFrame(animationId);
  }, [accessibilityMode, showDetectionOverlay, handDetected, faceDetected]);

  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return;
      switch (e.key.toLowerCase()) {
        case 'm': handleToggleMic(); break;
        case 'v': handleToggleCamera(); break;
        case 'a': handleToggleAccessibility(); break;
        case 's': handleToggleScreenShare(); break;
        case 'h': setShowShortcuts(prev => !prev); break;
        case 'd': setShowDetectionOverlay(prev => !prev); break;
      }
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [handleToggleMic, handleToggleCamera, handleToggleAccessibility, handleToggleScreenShare]);

  useEffect(() => {
    if (cameraEnabled) initializeCamera();
    return () => { if (cameraEnabled) cleanupCamera(); };
  }, [cameraEnabled, initializeCamera, cleanupCamera]);

  useEffect(() => {
    return () => cleanupCamera();
  }, [cleanupCamera]);

  return (
    <div className="flex flex-col h-screen bg-navy-950">
      <div className="bg-navy-900/50 backdrop-blur-xl border-b border-white/10 px-6 py-3 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Video className="w-5 h-5 text-blue-400" />
            <span className="text-white font-semibold">Room: {roomCode}</span>
          </div>
          <div className="h-4 w-px bg-white/20" />
          <span className="text-gray-400 text-sm">{displayName}</span>
        </div>
        <div className="flex items-center gap-4">
          {accessibilityMode && (
            <div className="flex items-center gap-3 text-sm">
              <div className="flex items-center gap-2">
                <Hand className={`w-4 h-4 ${handDetected ? 'text-green-400' : 'text-gray-500'}`} />
                <span className={handDetected ? 'text-green-400' : 'text-gray-500'}>
                  {handDetected ? 'Hand Detected' : 'No Hand'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Eye className={`w-4 h-4 ${faceDetected ? 'text-blue-400' : 'text-gray-500'}`} />
                <span className={faceDetected ? 'text-blue-400' : 'text-gray-500'}>
                  {faceDetected ? 'Face Detected' : 'No Face'}
                </span>
              </div>
            </div>
          )}
          {accessibilityMode && (
            <div className="bg-purple-600/20 border border-purple-500/50 px-4 py-1 rounded-full text-purple-300 text-sm font-semibold flex items-center gap-2">
              <Accessibility className="w-4 h-4" />
              Accessibility Mode
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 relative p-4">
        <div className="w-full h-full bg-black rounded-lg overflow-hidden relative">
          {isLoadingCamera && (
            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-75 z-10">
              <div className="text-center">
                <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
                <div className="text-white text-lg">Starting camera...</div>
              </div>
            </div>
          )}

          {cameraError && (
            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-75 z-10">
              <div className="text-center max-w-md p-6">
                <AlertTriangle className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
                <div className="text-white text-lg mb-4">{cameraError}</div>
                <button onClick={() => { setCameraError(''); setCameraEnabled(true); }} className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  Try Again
                </button>
              </div>
            </div>
          )}

          {cameraEnabled && localStream && !cameraError ? (
            <div className="relative w-full h-full">
              <video ref={localVideoRef} autoPlay playsInline muted className="w-full h-full object-contain" style={{ transform: 'scaleX(-1)' }} />
              {accessibilityMode && showDetectionOverlay && (
                <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" style={{ transform: 'scaleX(-1)' }} />
              )}
            </div>
          ) : !cameraError && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <VideoOff className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                <div className="text-gray-400 text-xl mb-4">Camera is off</div>
                <button onClick={handleToggleCamera} className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  Turn On Camera
                </button>
              </div>
            </div>
          )}

          {accessibilityMode && cameraEnabled && (
            <div className="absolute top-4 left-4 space-y-2">
              {detectionQuality.lighting !== 'good' && (
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="bg-yellow-900/80 backdrop-blur-sm border border-yellow-600 px-4 py-2 rounded-lg flex items-center gap-2">
                  <Sun className="w-5 h-5 text-yellow-300" />
                  <span className="text-yellow-100 text-sm">
                    {detectionQuality.lighting === 'dark' ? 'Too dark - Move to better lighting' : 'Poor lighting - Adjust position'}
                  </span>
                </motion.div>
              )}
              {detectionQuality.distance !== 'good' && (
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="bg-orange-900/80 backdrop-blur-sm border border-orange-600 px-4 py-2 rounded-lg flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-orange-300" />
                  <span className="text-orange-100 text-sm">
                    {detectionQuality.distance === 'too-close' ? 'Too close - Move back' : 'Too far - Move closer'}
                  </span>
                </motion.div>
              )}
              {detectionQuality.confidence > 0 && (
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="bg-green-900/80 backdrop-blur-sm border border-green-600 px-4 py-2 rounded-lg">
                  <div className="text-green-100 text-sm mb-1">Detection Quality</div>
                  <div className="w-32 h-2 bg-green-950 rounded-full overflow-hidden">
                    <div className="h-full bg-green-400 transition-all duration-300" style={{ width: `${detectionQuality.confidence * 100}%` }} />
                  </div>
                </motion.div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="bg-navy-900/50 backdrop-blur-xl border-t border-white/10 px-6 py-4">
        <div className="flex justify-center items-center gap-4">
          <button onClick={handleToggleMic} className={`w-14 h-14 rounded-full flex items-center justify-center transition-all focus:ring-4 ${micEnabled ? 'bg-navy-800 hover:bg-navy-700 focus:ring-gray-500' : 'bg-red-600 hover:bg-red-700 focus:ring-red-400'}`} title={micEnabled ? 'Mute (M)' : 'Unmute (M)'}>
            {micEnabled ? <Mic className="w-6 h-6 text-white" /> : <MicOff className="w-6 h-6 text-white" />}
          </button>
          <button onClick={handleToggleCamera} disabled={isLoadingCamera} className={`w-14 h-14 rounded-full flex items-center justify-center transition-all focus:ring-4 ${cameraEnabled ? 'bg-navy-800 hover:bg-navy-700 focus:ring-gray-500' : 'bg-red-600 hover:bg-red-700 focus:ring-red-400'}`} title={cameraEnabled ? 'Turn off camera (V)' : 'Turn on camera (V)'}>
            {cameraEnabled ? <Video className="w-6 h-6 text-white" /> : <VideoOff className="w-6 h-6 text-white" />}
          </button>
          <button onClick={handleToggleScreenShare} className={`w-14 h-14 rounded-full flex items-center justify-center transition-all focus:ring-4 ${screenSharing ? 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-400' : 'bg-navy-800 hover:bg-navy-700 focus:ring-gray-500'}`} title={screenSharing ? 'Stop sharing (S)' : 'Share screen (S)'}>
            {screenSharing ? <MonitorOff className="w-6 h-6 text-white" /> : <Monitor className="w-6 h-6 text-white" />}
          </button>
          <button onClick={handleToggleAccessibility} className={`w-14 h-14 rounded-full flex items-center justify-center transition-all focus:ring-4 ${accessibilityMode ? 'bg-purple-600 hover:bg-purple-700 focus:ring-purple-400' : 'bg-navy-800 hover:bg-navy-700 focus:ring-gray-500'}`} title={accessibilityMode ? 'Disable accessibility (A)' : 'Enable accessibility (A)'}>
            <Accessibility className="w-6 h-6 text-white" />
          </button>
          <button onClick={() => setShowShortcuts(!showShortcuts)} className="w-14 h-14 rounded-full bg-navy-800 hover:bg-navy-700 flex items-center justify-center focus:ring-4 focus:ring-gray-500 transition-all" title="Show shortcuts (H)">
            <Keyboard className="w-6 h-6 text-white" />
          </button>
          <button onClick={handleLeave} className="w-14 h-14 rounded-full bg-red-600 hover:bg-red-700 flex items-center justify-center focus:ring-4 focus:ring-red-400 transition-all" title="Leave call">
            <Phone className="w-6 h-6 text-white transform rotate-135" />
          </button>
        </div>
        <div className="text-center mt-3 text-gray-500 text-xs">Press H to show keyboard shortcuts</div>
      </div>

      <AnimatePresence>
        {showShortcuts && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowShortcuts(false)}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} className="bg-navy-900/90 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl max-w-md w-full p-8" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center gap-3 mb-6">
                <Keyboard className="w-8 h-8 text-blue-400" />
                <h3 className="text-2xl font-bold text-white">Keyboard Shortcuts</h3>
              </div>
              <div className="space-y-3">
                {[
                  { key: 'M', action: 'Toggle Microphone' },
                  { key: 'V', action: 'Toggle Camera' },
                  { key: 'A', action: 'Toggle Accessibility Mode' },
                  { key: 'S', action: 'Toggle Screen Share' },
                  { key: 'D', action: 'Toggle Detection Overlay' },
                  { key: 'H', action: 'Show/Hide Shortcuts' },
                ].map(({ key, action }) => (
                  <div key={key} className="flex items-center justify-between p-3 bg-navy-800/50 rounded-lg">
                    <span className="text-gray-300">{action}</span>
                    <kbd className="px-3 py-1 bg-navy-700 border border-white/20 rounded text-white font-mono text-sm">{key}</kbd>
                  </div>
                ))}
              </div>
              <button onClick={() => setShowShortcuts(false)} className="w-full mt-6 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                Got it
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}



export default VideoCallPageNew;
