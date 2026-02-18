/**
 * ASL Audio Player Component
 * 
 * Receives Base64 MP3 audio, decodes, and plays automatically.
 * Manages audio queue and provides visual playback indicator.
 */

import React, { useEffect, useRef, useState } from 'react';
import { AudioMessage } from '../services/ASLCaptureService';

interface ASLAudioPlayerProps {
  className?: string;
}

interface AudioQueueItem {
  id: string;
  audioData: string;
  format: string;
}

export const ASLAudioPlayer: React.FC<ASLAudioPlayerProps> = ({ className = '' }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [queue, setQueue] = useState<AudioQueueItem[]>([]);
  
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const queueRef = useRef<AudioQueueItem[]>([]);
  
  // Initialize audio element
  useEffect(() => {
    audioRef.current = new Audio();
    
    audioRef.current.onplay = () => {
      setIsPlaying(true);
    };
    
    audioRef.current.onended = () => {
      setIsPlaying(false);
      playNext();
    };
    
    audioRef.current.onerror = (error) => {
      console.error('Audio playback error:', error);
      setIsPlaying(false);
      playNext();
    };
    
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);
  
  // Sync queue ref with state
  useEffect(() => {
    queueRef.current = queue;
  }, [queue]);
  
  /**
   * Add audio to queue and play if not currently playing
   */
  const addToQueue = (audioMessage: AudioMessage) => {
    const item: AudioQueueItem = {
      id: `${audioMessage.timestamp}`,
      audioData: audioMessage.data,
      format: audioMessage.format
    };
    
    setQueue(prev => [...prev, item]);
    
    // If not currently playing, start playback
    if (!isPlaying && audioRef.current) {
      playAudio(item);
    }
  };
  
  /**
   * Play audio item
   */
  const playAudio = (item: AudioQueueItem) => {
    if (!audioRef.current) return;
    
    try {
      // Convert base64 to blob URL
      const audioBlob = base64ToBlob(item.audioData, `audio/${item.format}`);
      const audioUrl = URL.createObjectURL(audioBlob);
      
      audioRef.current.src = audioUrl;
      audioRef.current.play();
      
      // Cleanup URL after playback
      audioRef.current.onended = () => {
        URL.revokeObjectURL(audioUrl);
        setIsPlaying(false);
        playNext();
      };
    } catch (error) {
      console.error('Failed to play audio:', error);
      setIsPlaying(false);
      playNext();
    }
  };
  
  /**
   * Play next item in queue
   */
  const playNext = () => {
    setQueue(prev => {
      const newQueue = prev.slice(1);
      
      if (newQueue.length > 0 && audioRef.current) {
        // Small delay before playing next
        setTimeout(() => {
          playAudio(newQueue[0]);
        }, 100);
      }
      
      return newQueue;
    });
  };
  
  /**
   * Convert base64 to Blob
   */
  const base64ToBlob = (base64: string, mimeType: string): Blob => {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  };
  
  // Expose addToQueue method via ref
  useEffect(() => {
    (window as any).__aslAudioPlayer = { addToQueue };
  }, [isPlaying]);
  
  return (
    <div className={`asl-audio-player ${className}`} style={{
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      zIndex: 1000
    }}>
      {isPlaying && (
        <div className="playback-indicator" style={{
          background: 'linear-gradient(135deg, #4ade80 0%, #16a34a 100%)',
          borderRadius: '12px',
          padding: '16px 24px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          boxShadow: '0 8px 24px rgba(74, 222, 128, 0.3)',
          animation: 'slideIn 0.3s ease-out'
        }}>
          <div className="speaker-icon" style={{ color: 'white', display: 'flex', alignItems: 'center' }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
              <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
            </svg>
          </div>
          <div className="playback-text" style={{ color: 'white', fontWeight: 600, fontSize: '14px' }}>
            Playing audio...
          </div>
          <div className="audio-wave" style={{ display: 'flex', alignItems: 'center', gap: '4px', height: '20px' }}>
            <span style={{ width: '3px', background: 'white', borderRadius: '2px', animation: 'wave 1s ease-in-out infinite' }}></span>
            <span style={{ width: '3px', background: 'white', borderRadius: '2px', animation: 'wave 1s ease-in-out infinite', animationDelay: '0.2s' }}></span>
            <span style={{ width: '3px', background: 'white', borderRadius: '2px', animation: 'wave 1s ease-in-out infinite', animationDelay: '0.4s' }}></span>
          </div>
        </div>
      )}
      
      {queue.length > 0 && !isPlaying && (
        <div className="queue-indicator" style={{
          background: 'rgba(0, 0, 0, 0.8)',
          borderRadius: '12px',
          padding: '12px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
        }}>
          <div className="queue-count" style={{
            background: '#4ade80',
            color: 'white',
            fontWeight: 700,
            fontSize: '14px',
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {queue.length}
          </div>
          <div className="queue-text" style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '14px' }}>
            in queue
          </div>
        </div>
      )}
      
      <style>{`
        @keyframes slideIn {
          from {
            transform: translateY(100px);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
        
        @keyframes wave {
          0%, 100% {
            height: 8px;
          }
          50% {
            height: 20px;
          }
        }
      `}</style>
    </div>
  );
};

export const getAudioPlayerInstance = () => {
  return (window as any).__aslAudioPlayer as { addToQueue: (msg: AudioMessage) => void } | undefined;
};

export default ASLAudioPlayer;
