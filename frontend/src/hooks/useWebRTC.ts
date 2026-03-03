import { useEffect, useRef, useState, useCallback } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';

/**
 * WebRTC Hook for Video Calling
 * 
 * Requirements:
 * - 1.1: Support 720p/1080p video resolution at 30 FPS
 * - 1.3: Automatically reduce resolution when bandwidth is insufficient
 * - 21.1: Maintain end-to-end audio latency below 150ms
 * - 21.2: Maintain end-to-end video latency below 200ms
 * - 21.3: Use UDP transport for media streams
 * - 21.5: Use TURN servers only when direct peer connections fail
 * 
 * Features:
 * - Initialize WebRTC PeerConnection with STUN/TURN servers
 * - Implement getUserMedia for camera and microphone access
 * - Implement peer connection establishment with offer/answer
 * - Implement ICE candidate exchange
 * - Handle remote stream display
 * - Implement connection quality monitoring
 */

// STUN/TURN server configuration (Requirement 21.5)
const ICE_SERVERS: RTCIceServer[] = [
  // Public STUN servers
  { urls: 'stun:stun.l.google.com:19302' },
  { urls: 'stun:stun1.l.google.com:19302' },
  { urls: 'stun:stun2.l.google.com:19302' },
  // Add TURN servers here when available
  // {
  //   urls: 'turn:your-turn-server.com:3478',
  //   username: 'username',
  //   credential: 'password'
  // }
];

// WebRTC configuration (Requirements 21.1, 21.2, 21.3)
const RTC_CONFIGURATION: RTCConfiguration = {
  iceServers: ICE_SERVERS,
  iceCandidatePoolSize: 10,
  bundlePolicy: 'max-bundle', // Optimize for low latency
  rtcpMuxPolicy: 'require', // Reduce port usage
  iceTransportPolicy: 'all', // Try direct connection first, fallback to TURN
};

// Media constraints (Requirement 1.1)
const DEFAULT_MEDIA_CONSTRAINTS: MediaStreamConstraints = {
  audio: {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
    sampleRate: 48000,
  },
  video: {
    width: { ideal: 1280, max: 1920 },
    height: { ideal: 720, max: 1080 },
    frameRate: { ideal: 30, max: 30 },
    facingMode: 'user',
  },
};

export interface PeerConnection {
  userId: string;
  connection: RTCPeerConnection;
  stream: MediaStream | null;
}

export interface ConnectionQuality {
  userId: string;
  latency: number;
  packetLoss: number;
  bandwidth: number;
  videoResolution: string;
  timestamp: number;
}

export interface UseWebRTCReturn {
  localStream: MediaStream | null;
  remoteStreams: Map<string, MediaStream>;
  peerConnections: Map<string, RTCPeerConnection>;
  connectionQualities: Map<string, ConnectionQuality>;
  isInitialized: boolean;
  error: string | null;
  screenStream: MediaStream | null;
  isScreenSharing: boolean;
  
  // Methods
  initializeMedia: (constraints?: MediaStreamConstraints) => Promise<void>;
  createPeerConnection: (userId: string) => Promise<RTCPeerConnection>;
  closePeerConnection: (userId: string) => void;
  toggleAudio: (enabled: boolean) => void;
  toggleVideo: (enabled: boolean) => void;
  startScreenShare: () => Promise<void>;
  stopScreenShare: () => void;
  cleanup: () => void;
}

export const useWebRTC = (
  _meetingId: string,
  currentUserId: string
): UseWebRTCReturn => {
  const { sendMessage, subscribe } = useWebSocket();
  
  // State
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [remoteStreams, setRemoteStreams] = useState<Map<string, MediaStream>>(new Map());
  const [connectionQualities, setConnectionQualities] = useState<Map<string, ConnectionQuality>>(new Map());
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [screenStream, setScreenStream] = useState<MediaStream | null>(null);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  
  // Refs
  const peerConnectionsRef = useRef<Map<string, RTCPeerConnection>>(new Map());
  const qualityMonitorIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const screenSendersRef = useRef<Map<string, RTCRtpSender[]>>(new Map());
  
  /**
   * Initialize local media stream (Requirement 1.1)
   * Implements getUserMedia for camera and microphone access
   */
  const initializeMedia = useCallback(async (
    constraints: MediaStreamConstraints = DEFAULT_MEDIA_CONSTRAINTS
  ): Promise<void> => {
    try {
      console.log('Initializing media with constraints:', constraints);
      
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      setLocalStream(stream);
      setIsInitialized(true);
      setError(null);
      
      console.log('Media initialized successfully:', {
        audioTracks: stream.getAudioTracks().length,
        videoTracks: stream.getVideoTracks().length,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to access media devices';
      console.error('Error initializing media:', err);
      setError(errorMessage);
      throw err;
    }
  }, []);
  
  /**
   * Create peer connection for a specific user
   * Implements peer connection establishment with offer/answer
   */
  const createPeerConnection = useCallback(async (userId: string): Promise<RTCPeerConnection> => {
    console.log(`Creating peer connection for user: ${userId}`);
    
    // Check if connection already exists
    if (peerConnectionsRef.current.has(userId)) {
      console.log(`Peer connection already exists for user: ${userId}`);
      return peerConnectionsRef.current.get(userId)!;
    }
    
    // Create new RTCPeerConnection (Requirements 21.1, 21.2, 21.3)
    const peerConnection = new RTCPeerConnection(RTC_CONFIGURATION);
    
    // Add local stream tracks to peer connection
    if (localStream) {
      localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, localStream);
        console.log(`Added ${track.kind} track to peer connection for ${userId}`);
      });
    }
    
    // Handle ICE candidates (Requirement 21.5)
    peerConnection.onicecandidate = (event) => {
      if (event.candidate) {
        console.log(`Sending ICE candidate to ${userId}`);
        sendMessage('ice-candidate', {
          to: userId,
          from: currentUserId,
          candidate: event.candidate.toJSON(),
        });
      }
    };
    
    // Handle ICE connection state changes
    peerConnection.oniceconnectionstatechange = () => {
      console.log(`ICE connection state for ${userId}:`, peerConnection.iceConnectionState);
      
      if (peerConnection.iceConnectionState === 'failed') {
        console.error(`ICE connection failed for ${userId}`);
        // Attempt ICE restart
        peerConnection.restartIce();
      }
      
      if (peerConnection.iceConnectionState === 'disconnected') {
        console.warn(`ICE connection disconnected for ${userId}`);
      }
      
      if (peerConnection.iceConnectionState === 'closed') {
        console.log(`ICE connection closed for ${userId}`);
        closePeerConnection(userId);
      }
    };
    
    // Handle connection state changes
    peerConnection.onconnectionstatechange = () => {
      console.log(`Connection state for ${userId}:`, peerConnection.connectionState);
      
      if (peerConnection.connectionState === 'failed') {
        console.error(`Connection failed for ${userId}`);
        setError(`Connection failed with ${userId}`);
      }
    };
    
    // Handle remote stream (Handle remote stream display)
    peerConnection.ontrack = (event) => {
      console.log(`Received ${event.track.kind} track from ${userId}`);
      
      const [remoteStream] = event.streams;
      if (remoteStream) {
        setRemoteStreams(prev => {
          const updated = new Map(prev);
          updated.set(userId, remoteStream);
          return updated;
        });
        
        console.log(`Remote stream added for ${userId}:`, {
          audioTracks: remoteStream.getAudioTracks().length,
          videoTracks: remoteStream.getVideoTracks().length,
        });
      }
    };
    
    // Store peer connection
    peerConnectionsRef.current.set(userId, peerConnection);
    
    return peerConnection;
  }, [localStream, currentUserId, sendMessage]);
  
  /**
   * Close peer connection for a specific user
   */
  const closePeerConnection = useCallback((userId: string) => {
    console.log(`Closing peer connection for user: ${userId}`);
    
    const peerConnection = peerConnectionsRef.current.get(userId);
    if (peerConnection) {
      peerConnection.close();
      peerConnectionsRef.current.delete(userId);
    }
    
    // Remove remote stream
    setRemoteStreams(prev => {
      const updated = new Map(prev);
      updated.delete(userId);
      return updated;
    });
    
    // Remove connection quality
    setConnectionQualities(prev => {
      const updated = new Map(prev);
      updated.delete(userId);
      return updated;
    });
  }, []);
  
  /**
   * Toggle audio track
   */
  const toggleAudio = useCallback((enabled: boolean) => {
    if (localStream) {
      localStream.getAudioTracks().forEach(track => {
        track.enabled = enabled;
      });
      console.log(`Audio ${enabled ? 'enabled' : 'disabled'}`);
    }
  }, [localStream]);
  
  /**
   * Toggle video track
   */
  const toggleVideo = useCallback((enabled: boolean) => {
    if (localStream) {
      localStream.getVideoTracks().forEach(track => {
        track.enabled = enabled;
      });
      console.log(`Video ${enabled ? 'enabled' : 'disabled'}`);
    }
  }, [localStream]);
  
  /**
   * Start screen sharing (Requirements 2.1, 2.2, 2.3)
   * Implements getDisplayMedia for screen capture
   */
  const startScreenShare = useCallback(async () => {
    try {
      console.log('Starting screen share...');
      
      // Request screen share with getDisplayMedia (Requirement 2.1, 2.2, 2.3)
      const displayStream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          displaySurface: 'monitor', // Can be 'monitor', 'window', or 'browser'
        } as MediaTrackConstraints,
        audio: false, // Screen audio can be added if needed
      });
      
      setScreenStream(displayStream);
      setIsScreenSharing(true);
      
      console.log('Screen share started:', {
        videoTracks: displayStream.getVideoTracks().length,
      });
      
      // Handle screen share stop (when user clicks browser's stop sharing button)
      displayStream.getVideoTracks()[0].onended = () => {
        console.log('Screen share ended by user');
        stopScreenShare();
      };
      
      // Replace video tracks in all peer connections with screen share track
      const screenTrack = displayStream.getVideoTracks()[0];
      
      for (const [userId, peerConnection] of peerConnectionsRef.current.entries()) {
        const senders = peerConnection.getSenders();
        const videoSender = senders.find(sender => sender.track?.kind === 'video');
        
        if (videoSender) {
          // Replace the video track with screen share track
          await videoSender.replaceTrack(screenTrack);
          
          // Store the sender for later restoration
          if (!screenSendersRef.current.has(userId)) {
            screenSendersRef.current.set(userId, []);
          }
          screenSendersRef.current.get(userId)!.push(videoSender);
          
          console.log(`Replaced video track with screen share for user: ${userId}`);
        }
      }
      
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start screen sharing';
      console.error('Error starting screen share:', err);
      setError(errorMessage);
      setIsScreenSharing(false);
      throw err;
    }
  }, []);
  
  /**
   * Stop screen sharing (Requirement 2.5)
   * Restores camera video track
   */
  const stopScreenShare = useCallback(() => {
    console.log('Stopping screen share...');
    
    if (screenStream) {
      // Stop all screen share tracks
      screenStream.getTracks().forEach(track => {
        track.stop();
      });
      setScreenStream(null);
    }
    
    setIsScreenSharing(false);
    
    // Restore original video tracks in all peer connections
    if (localStream) {
      const videoTrack = localStream.getVideoTracks()[0];
      
      for (const [userId] of peerConnectionsRef.current.entries()) {
        const senders = screenSendersRef.current.get(userId);
        
        if (senders && videoTrack) {
          senders.forEach(async (sender) => {
            try {
              await sender.replaceTrack(videoTrack);
              console.log(`Restored video track for user: ${userId}`);
            } catch (err) {
              console.error(`Error restoring video track for ${userId}:`, err);
            }
          });
        }
      }
      
      // Clear screen senders
      screenSendersRef.current.clear();
    }
    
    console.log('Screen share stopped');
  }, [screenStream, localStream]);
  
  /**
   * Monitor connection quality (Implement connection quality monitoring)
   * Requirements 1.3, 21.1, 21.2
   */
  const monitorConnectionQuality = useCallback(async () => {
    for (const [userId, peerConnection] of peerConnectionsRef.current.entries()) {
      try {
        const stats = await peerConnection.getStats();
        
        let latency = 0;
        let packetLoss = 0;
        let bandwidth = 0;
        let videoResolution = 'unknown';
        
        stats.forEach((report) => {
          // Inbound RTP stats
          if (report.type === 'inbound-rtp' && report.kind === 'video') {
            if (report.packetsLost && report.packetsReceived) {
              packetLoss = (report.packetsLost / (report.packetsLost + report.packetsReceived)) * 100;
            }
            
            if (report.frameWidth && report.frameHeight) {
              videoResolution = `${report.frameWidth}x${report.frameHeight}`;
            }
          }
          
          // Candidate pair stats for latency
          if (report.type === 'candidate-pair' && report.state === 'succeeded') {
            if (report.currentRoundTripTime) {
              latency = report.currentRoundTripTime * 1000; // Convert to ms
            }
            
            if (report.availableOutgoingBitrate) {
              bandwidth = report.availableOutgoingBitrate / 1000000; // Convert to Mbps
            }
          }
        });
        
        // Update connection quality state
        setConnectionQualities(prev => {
          const updated = new Map(prev);
          updated.set(userId, {
            userId,
            latency,
            packetLoss,
            bandwidth,
            videoResolution,
            timestamp: Date.now(),
          });
          return updated;
        });
        
        // Adaptive quality adjustment (Requirement 1.3)
        // If latency is high or packet loss is significant, reduce quality
        if (latency > 200 || packetLoss > 5) {
          console.warn(`Poor connection quality for ${userId}:`, {
            latency,
            packetLoss,
            bandwidth,
          });
          
          // TODO: Implement adaptive bitrate adjustment
          // This would involve modifying the sender parameters
        }
        
      } catch (err) {
        console.error(`Error monitoring connection quality for ${userId}:`, err);
      }
    }
  }, []);
  
  /**
   * Cleanup all connections and streams
   */
  const cleanup = useCallback(() => {
    console.log('Cleaning up WebRTC resources');
    
    // Stop quality monitoring
    if (qualityMonitorIntervalRef.current) {
      clearInterval(qualityMonitorIntervalRef.current);
      qualityMonitorIntervalRef.current = null;
    }
    
    // Stop screen sharing if active
    if (isScreenSharing) {
      stopScreenShare();
    }
    
    // Close all peer connections
    peerConnectionsRef.current.forEach((_, userId) => {
      closePeerConnection(userId);
    });
    
    // Stop local stream
    if (localStream) {
      localStream.getTracks().forEach(track => {
        track.stop();
      });
      setLocalStream(null);
    }
    
    setIsInitialized(false);
    setRemoteStreams(new Map());
    setConnectionQualities(new Map());
  }, [localStream, isScreenSharing, stopScreenShare, closePeerConnection]);
  
  /**
   * Handle WebRTC signaling events
   */
  useEffect(() => {
    if (!isInitialized) return;
    
    // Handle incoming offer
    const unsubscribeOffer = subscribe('offer', async (data: any) => {
      console.log('Received offer from:', data.from);
      
      try {
        const peerConnection = await createPeerConnection(data.from);
        
        // Set remote description
        await peerConnection.setRemoteDescription(new RTCSessionDescription(data.sdp));
        
        // Create answer
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        
        // Send answer back
        sendMessage('answer', {
          to: data.from,
          from: currentUserId,
          sdp: answer,
        });
        
        console.log('Sent answer to:', data.from);
      } catch (err) {
        console.error('Error handling offer:', err);
        setError('Failed to handle incoming call');
      }
    });
    
    // Handle incoming answer
    const unsubscribeAnswer = subscribe('answer', async (data: any) => {
      console.log('Received answer from:', data.from);
      
      try {
        const peerConnection = peerConnectionsRef.current.get(data.from);
        if (peerConnection) {
          await peerConnection.setRemoteDescription(new RTCSessionDescription(data.sdp));
          console.log('Set remote description from answer');
        }
      } catch (err) {
        console.error('Error handling answer:', err);
        setError('Failed to complete connection');
      }
    });
    
    // Handle incoming ICE candidate
    const unsubscribeIceCandidate = subscribe('ice-candidate', async (data: any) => {
      console.log('Received ICE candidate from:', data.from);
      
      try {
        const peerConnection = peerConnectionsRef.current.get(data.from);
        if (peerConnection && data.candidate) {
          await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
          console.log('Added ICE candidate');
        }
      } catch (err) {
        console.error('Error adding ICE candidate:', err);
      }
    });
    
    // Handle participant left
    const unsubscribeParticipantLeft = subscribe('participant-left', (data: any) => {
      console.log('Participant left:', data.userId);
      closePeerConnection(data.userId);
    });
    
    // Start quality monitoring (every 5 seconds)
    qualityMonitorIntervalRef.current = setInterval(monitorConnectionQuality, 5000);
    
    return () => {
      unsubscribeOffer();
      unsubscribeAnswer();
      unsubscribeIceCandidate();
      unsubscribeParticipantLeft();
      
      if (qualityMonitorIntervalRef.current) {
        clearInterval(qualityMonitorIntervalRef.current);
      }
    };
  }, [isInitialized, currentUserId, createPeerConnection, closePeerConnection, sendMessage, subscribe, monitorConnectionQuality]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);
  
  return {
    localStream,
    remoteStreams,
    peerConnections: peerConnectionsRef.current,
    connectionQualities,
    isInitialized,
    error,
    screenStream,
    isScreenSharing,
    initializeMedia,
    createPeerConnection,
    closePeerConnection,
    toggleAudio,
    toggleVideo,
    startScreenShare,
    stopScreenShare,
    cleanup,
  };
};


/**
 * Helper hook for initiating calls to participants
 */
export const useWebRTCCaller = (
  webrtc: UseWebRTCReturn,
  currentUserId: string,
  sendMessage: (event: string, data: any) => void
) => {
  /**
   * Initiate call to a specific user
   * Creates offer and sends it via signaling server
   */
  const callUser = useCallback(async (userId: string) => {
    console.log(`Initiating call to user: ${userId}`);
    
    try {
      const peerConnection = await webrtc.createPeerConnection(userId);
      
      // Create offer
      const offer = await peerConnection.createOffer({
        offerToReceiveAudio: true,
        offerToReceiveVideo: true,
      });
      
      await peerConnection.setLocalDescription(offer);
      
      // Send offer via signaling server
      sendMessage('offer', {
        to: userId,
        from: currentUserId,
        sdp: offer,
      });
      
      console.log(`Sent offer to user: ${userId}`);
    } catch (err) {
      console.error(`Error calling user ${userId}:`, err);
      throw err;
    }
  }, [webrtc, currentUserId, sendMessage]);
  
  /**
   * Initiate calls to multiple users
   */
  const callMultipleUsers = useCallback(async (userIds: string[]) => {
    console.log(`Initiating calls to ${userIds.length} users`);
    
    const promises = userIds.map(userId => callUser(userId));
    
    try {
      await Promise.all(promises);
      console.log('Successfully initiated all calls');
    } catch (err) {
      console.error('Error initiating calls:', err);
      throw err;
    }
  }, [callUser]);
  
  return {
    callUser,
    callMultipleUsers,
  };
};
