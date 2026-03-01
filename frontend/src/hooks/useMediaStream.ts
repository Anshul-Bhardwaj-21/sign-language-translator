import { useState, useCallback, useRef, useEffect } from 'react';

interface UseMediaStreamOptions {
  video?: boolean;
  audio?: boolean;
}

export const useMediaStream = (options: UseMediaStreamOptions = { video: true, audio: true }) => {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [isEnabled, setIsEnabled] = useState(false);
  const streamRef = useRef<MediaStream | null>(null);

  const startStream = useCallback(async () => {
    if (streamRef.current) {
      return streamRef.current;
    }

    setIsLoading(true);
    setError('');

    const constraints = [
      {
        video: options.video ? {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 30 },
          facingMode: 'user'
        } : false,
        audio: options.audio ? {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } : false
      },
      {
        video: options.video ? {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        } : false,
        audio: options.audio
      },
      {
        video: options.video,
        audio: options.audio
      }
    ];

    for (const constraint of constraints) {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia(constraint);
        streamRef.current = mediaStream;
        setStream(mediaStream);
        setIsEnabled(true);
        setIsLoading(false);
        return mediaStream;
      } catch (err) {
        console.log('Media stream attempt failed:', err);
        continue;
      }
    }

    setError('Could not access camera/microphone. Please check permissions.');
    setIsLoading(false);
    return null;
  }, [options.video, options.audio]);

  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        track.stop();
        track.enabled = false;
      });
      streamRef.current = null;
      setStream(null);
      setIsEnabled(false);
    }
  }, []);

  const toggleVideo = useCallback(() => {
    if (streamRef.current) {
      const videoTracks = streamRef.current.getVideoTracks();
      videoTracks.forEach(track => {
        track.enabled = !track.enabled;
      });
    }
  }, []);

  const toggleAudio = useCallback(() => {
    if (streamRef.current) {
      const audioTracks = streamRef.current.getAudioTracks();
      audioTracks.forEach(track => {
        track.enabled = !track.enabled;
      });
    }
  }, []);

  useEffect(() => {
    return () => {
      stopStream();
    };
  }, [stopStream]);

  return {
    stream,
    isLoading,
    error,
    isEnabled,
    startStream,
    stopStream,
    toggleVideo,
    toggleAudio,
  };
};
