import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Video, VideoOff, Mic, MicOff, Phone, Settings, MessageSquare, Users } from 'lucide-react';
import { useApp } from '../contexts/AppContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import { GlassCard } from '../components/ui/GlassCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useToast } from '../hooks/useToast';

interface Caption {
  id: string;
  text: string;
  confidence: number;
  timestamp: number;
  userId: string;
}

interface WordFrequency {
  word: string;
  count: number;
}

export default function VideoCallPageNew() {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  const { user, aiStatus, incrementWordsRecognized, setIsInCall, connectionStrength } = useApp();
  const { isConnected, subscribe } = useWebSocket();
  const { error: showToast } = useToast();

  // Media states
  const [cameraEnabled, setCameraEnabled] = useState(true);
  const [micEnabled, setMicEnabled] = useState(true);
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);

  // UI states
  const [showChat, setShowChat] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Caption states
  const [captions, setCaptions] = useState<Caption[]>([]);
  const [handDetected, setHandDetected] = useState(false);
  const [gestureStable, setGestureStable] = useState(false);
  const [recognitionConfidence, setRecognitionConfidence] = useState(0);

  // Analytics
  const [wordFrequency, setWordFrequency] = useState<WordFrequency[]>([]);
  const [totalWordsDetected, setTotalWordsDetected] = useState(0);

  // Refs
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const captionScrollRef = useRef<HTMLDivElement>(null);

  // Initialize camera
  useEffect(() => {
    const initCamera = async () => {
      if (!cameraEnabled) return;

      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 1280, height: 720, facingMode: 'user' },
          audio: micEnabled
        });

        setLocalStream(stream);
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream;
        }
      } catch (error) {
        showToast('Failed to access camera', 'error');
        console.error('Camera error:', error);
      }
    };

    initCamera();

    return () => {
      localStream?.getTracks().forEach(track => track.stop());
    };
  }, [cameraEnabled, micEnabled, showToast]);

  // WebSocket subscriptions
  useEffect(() => {
    if (!roomCode || !user) return;

    const unsubCaption = subscribe('caption', (data: Caption) => {
      setCaptions(prev => [...prev, data]);
      incrementWordsRecognized();
      setTotalWordsDetected(prev => prev + 1);

      // Update word frequency
      const words = data.text.toLowerCase().split(' ');
      setWordFrequency(prev => {
        const newFreq = [...prev];
        words.forEach(word => {
          const existing = newFreq.find(w => w.word === word);
          if (existing) {
            existing.count++;
          } else {
            newFreq.push({ word, count: 1 });
          }
        });
        return newFreq.sort((a, b) => b.count - a.count).slice(0, 10);
      });

      // Auto-scroll captions
      setTimeout(() => {
        if (captionScrollRef.current) {
          captionScrollRef.current.scrollTop = captionScrollRef.current.scrollHeight;
        }
      }, 100);
    });

    const unsubHandDetection = subscribe('hand_detection', (data: { detected: boolean; stable: boolean; confidence: number }) => {
      setHandDetected(data.detected);
      setGestureStable(data.stable);
      setRecognitionConfidence(data.confidence);
    });

    return () => {
      unsubCaption();
      unsubHandDetection();
    };
  }, [roomCode, user, subscribe, incrementWordsRecognized]);

  // Set in call status
  useEffect(() => {
    setIsInCall(true);
    return () => setIsInCall(false);
  }, [setIsInCall]);

  const handleToggleCamera = () => {
    if (localStream) {
      localStream.getVideoTracks().forEach(track => {
        track.enabled = !cameraEnabled;
      });
    }
    setCameraEnabled(!cameraEnabled);
  };

  const handleToggleMic = () => {
    if (localStream) {
      localStream.getAudioTracks().forEach(track => {
        track.enabled = !micEnabled;
      });
    }
    setMicEnabled(!micEnabled);
  };

  const handleLeaveCall = () => {
    if (window.confirm('Leave call?')) {
      localStream?.getTracks().forEach(track => track.stop());
      navigate('/dashboard');
    }
  };

  return (
    <div className="h-screen bg-navy-950 flex flex-col overflow-hidden">
      {/* Top Bar */}
      <motion.div
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className="bg-navy-900/80 backdrop-blur-xl border-b border-navy-800 px-6 py-4 flex items-center justify-between"
      >
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-white">Room: {roomCode}</h1>
          <StatusBadge
            status={isConnected ? 'success' : 'error'}
            label={isConnected ? 'Connected' : 'Disconnected'}
          />
          <StatusBadge
            status={aiStatus === 'connected' ? 'success' : aiStatus === 'mock' ? 'warning' : 'error'}
            label={aiStatus === 'connected' ? 'AI Active' : aiStatus === 'mock' ? 'Mock Mode' : 'AI Offline'}
          />
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span>Connection: {connectionStrength}%</span>
          </div>
          <div className="text-sm text-gray-400">
            Words: {totalWordsDetected}
          </div>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 flex gap-4 p-4 overflow-hidden">
        {/* Left: Local Video */}
        <motion.div
          initial={{ x: -100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          className="flex-1 relative"
        >
          <GlassCard className="h-full relative overflow-hidden group">
            {/* Video */}
            <video
              ref={localVideoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover rounded-lg mirror"
            />

            {/* Hand Detection Overlay */}
            <AnimatePresence>
              {handDetected && (
                <motion.div
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                  className="absolute top-4 left-4"
                >
                  <div className={`px-4 py-2 rounded-full backdrop-blur-xl ${
                    gestureStable ? 'bg-green-500/20 border-2 border-green-500' : 'bg-yellow-500/20 border-2 border-yellow-500'
                  }`}>
                    <div className="flex items-center gap-2">
                      <motion.div
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ repeat: Infinity, duration: 1 }}
                        className="text-2xl"
                      >
                        ✋
                      </motion.div>
                      <span className="text-white font-semibold">
                        {gestureStable ? 'Stable' : 'Detecting...'}
                      </span>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Recognition Indicator */}
            {handDetected && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute top-4 right-4"
              >
                <div className="w-16 h-16 rounded-full bg-purple-500/20 backdrop-blur-xl border-2 border-purple-500 flex items-center justify-center">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 2, ease: 'linear' }}
                    className="text-purple-400"
                  >
                    🔄
                  </motion.div>
                </div>
              </motion.div>
            )}

            {/* User Label */}
            <div className="absolute bottom-4 left-4">
              <div className="px-4 py-2 bg-black/60 backdrop-blur-xl rounded-full">
                <span className="text-white font-semibold">{user?.name || 'You'}</span>
              </div>
            </div>

            {/* Camera Off Overlay */}
            {!cameraEnabled && (
              <div className="absolute inset-0 bg-navy-900 flex items-center justify-center">
                <div className="text-center">
                  <VideoOff className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                  <p className="text-gray-400">Camera is off</p>
                </div>
              </div>
            )}
          </GlassCard>
        </motion.div>

        {/* Right: Remote Video + Captions */}
        <motion.div
          initial={{ x: 100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          className="flex-1 flex flex-col gap-4"
        >
          {/* Remote Video */}
          <GlassCard className="flex-1 relative overflow-hidden">
            <video
              ref={remoteVideoRef}
              autoPlay
              playsInline
              className="w-full h-full object-cover rounded-lg"
            />

            {/* Placeholder */}
            <div className="absolute inset-0 bg-navy-900 flex items-center justify-center">
              <div className="text-center">
                <Users className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                <p className="text-gray-400">Waiting for participant...</p>
              </div>
            </div>
          </GlassCard>

          {/* Live Captions Panel */}
          <GlassCard className="h-64 flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white">Live Captions</h3>
              <StatusBadge
                status={handDetected ? 'success' : 'default'}
                label={handDetected ? 'Detecting' : 'Idle'}
              />
            </div>

            {/* Confidence Meter */}
            {handDetected && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-4"
              >
                <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
                  <span>Confidence</span>
                  <span>{Math.round(recognitionConfidence * 100)}%</span>
                </div>
                <div className="h-2 bg-navy-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${recognitionConfidence * 100}%` }}
                    transition={{ duration: 0.3 }}
                    className={`h-full rounded-full ${
                      recognitionConfidence > 0.7 ? 'bg-green-500' :
                      recognitionConfidence > 0.5 ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                  />
                </div>
              </motion.div>
            )}

            {/* Caption Timeline */}
            <div
              ref={captionScrollRef}
              className="flex-1 overflow-y-auto space-y-2 pr-2 custom-scrollbar"
            >
              <AnimatePresence>
                {captions.map((caption) => (
                  <motion.div
                    key={caption.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    className="p-3 bg-navy-800/50 rounded-lg border border-navy-700"
                  >
                    <div className="flex items-start justify-between mb-1">
                      <span className="text-xs text-gray-500">
                        {new Date(caption.timestamp).toLocaleTimeString()}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        caption.confidence > 0.7 ? 'bg-green-500/20 text-green-400' :
                        caption.confidence > 0.5 ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-red-500/20 text-red-400'
                      }`}>
                        {Math.round(caption.confidence * 100)}%
                      </span>
                    </div>
                    <p className="text-white">{caption.text}</p>
                  </motion.div>
                ))}
              </AnimatePresence>

              {captions.length === 0 && (
                <div className="text-center text-gray-500 py-8">
                  <p>No captions yet</p>
                  <p className="text-sm mt-2">Start signing to see live captions</p>
                </div>
              )}
            </div>
          </GlassCard>
        </motion.div>

        {/* Word Frequency Sidebar */}
        {wordFrequency.length > 0 && (
          <motion.div
            initial={{ x: 100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="w-64"
          >
            <GlassCard className="h-full">
              <h3 className="text-lg font-bold text-white mb-4">Word Frequency</h3>
              <div className="space-y-2">
                {wordFrequency.map((item, index) => (
                  <motion.div
                    key={item.word}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-center justify-between p-2 bg-navy-800/50 rounded-lg"
                  >
                    <span className="text-white font-medium">{item.word}</span>
                    <span className="text-blue-400 font-bold">{item.count}</span>
                  </motion.div>
                ))}
              </div>
            </GlassCard>
          </motion.div>
        )}
      </div>

      {/* Bottom Control Bar */}
      <motion.div
        initial={{ y: 100 }}
        animate={{ y: 0 }}
        className="bg-navy-900/80 backdrop-blur-xl border-t border-navy-800 px-6 py-4"
      >
        <div className="flex items-center justify-center gap-4">
          {/* Mic Toggle */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleToggleMic}
            className={`w-14 h-14 rounded-full flex items-center justify-center transition-all ${
              micEnabled
                ? 'bg-navy-800 hover:bg-navy-700 text-white'
                : 'bg-red-500 hover:bg-red-600 text-white shadow-neon-red'
            }`}
          >
            {micEnabled ? <Mic className="w-6 h-6" /> : <MicOff className="w-6 h-6" />}
          </motion.button>

          {/* Camera Toggle */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleToggleCamera}
            className={`w-14 h-14 rounded-full flex items-center justify-center transition-all ${
              cameraEnabled
                ? 'bg-navy-800 hover:bg-navy-700 text-white'
                : 'bg-red-500 hover:bg-red-600 text-white shadow-neon-red'
            }`}
          >
            {cameraEnabled ? <Video className="w-6 h-6" /> : <VideoOff className="w-6 h-6" />}
          </motion.button>

          {/* Leave Call */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleLeaveCall}
            className="w-14 h-14 rounded-full bg-red-500 hover:bg-red-600 text-white flex items-center justify-center shadow-neon-red"
          >
            <Phone className="w-6 h-6 rotate-135" />
          </motion.button>

          {/* Chat Toggle */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowChat(!showChat)}
            className={`w-14 h-14 rounded-full flex items-center justify-center transition-all ${
              showChat
                ? 'bg-blue-500 hover:bg-blue-600 text-white shadow-neon-blue'
                : 'bg-navy-800 hover:bg-navy-700 text-white'
            }`}
          >
            <MessageSquare className="w-6 h-6" />
          </motion.button>

          {/* Settings */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowSettings(!showSettings)}
            className="w-14 h-14 rounded-full bg-navy-800 hover:bg-navy-700 text-white flex items-center justify-center"
          >
            <Settings className="w-6 h-6" />
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
}
