/**
 * ASL Frame Capture Service
 * 
 * Manages camera access, frame capture, and WebSocket communication for ASL recognition.
 * 
 * Features:
 * - Camera management (getUserMedia)
 * - Frame capture at 24 FPS
 * - Throttle to 10 FPS for sending
 * - JPEG encoding and Base64 conversion
 * - WebSocket client with reconnection
 */

export interface VideoFrameMessage {
  type: 'video_frame';
  frame_id: number;
  timestamp: number;
  image: string; // base64-encoded JPEG
  session_id: string;
  user_id: string;
}

export interface CaptionMessage {
  type: 'caption';
  level: 'live' | 'word' | 'sentence';
  text: string;
  confidence: number;
  timestamp: number;
}

export interface AudioMessage {
  type: 'audio';
  format: 'mp3';
  data: string; // base64-encoded audio
  timestamp: number;
}

export interface ErrorMessage {
  type: 'error';
  code: 'INVALID_SESSION' | 'CAMERA_FAILURE' | 'LOW_CONFIDENCE' | 'MODEL_NOT_FOUND' | 'PROCESSING_FAILED' | 'INVALID_FRAME';
  message: string;
  severity: 'fatal' | 'recoverable' | 'warning';
  timestamp: number;
}

type ServerMessage = CaptionMessage | AudioMessage | ErrorMessage;

export interface ASLCaptureConfig {
  sessionId: string;
  userId: string;
  backendUrl?: string;
  captureFrameRate?: number; // FPS for capture (default: 24)
  sendFrameRate?: number; // FPS for sending (default: 10)
  jpegQuality?: number; // JPEG quality 0-1 (default: 0.8)
  reconnectAttempts?: number; // Max reconnection attempts (default: 3)
  reconnectDelay?: number; // Delay between reconnects in ms (default: 2000)
}

export class ASLCaptureService {
  private config: Required<ASLCaptureConfig>;
  private mediaStream: MediaStream | null = null;
  private videoElement: HTMLVideoElement | null = null;
  private canvas: HTMLCanvasElement | null = null;
  private ctx: CanvasRenderingContext2D | null = null;
  private ws: WebSocket | null = null;
  
  private captureIntervalId: number | null = null;
  private sendIntervalId: number | null = null;
  private frameId = 0;
  private lastCapturedFrame: string | null = null;
  
  private isCapturing = false;
  private reconnectCount = 0;
  
  // Callbacks
  private onCaptionCallback?: (caption: CaptionMessage) => void;
  private onAudioCallback?: (audio: AudioMessage) => void;
  private onErrorCallback?: (error: ErrorMessage) => void;
  private onConnectionChangeCallback?: (connected: boolean) => void;
  
  constructor(config: ASLCaptureConfig) {
    this.config = {
      backendUrl: config.backendUrl || 'ws://localhost:8000',
      captureFrameRate: config.captureFrameRate || 24,
      sendFrameRate: config.sendFrameRate || 10,
      jpegQuality: config.jpegQuality || 0.8,
      reconnectAttempts: config.reconnectAttempts || 3,
      reconnectDelay: config.reconnectDelay || 2000,
      ...config
    };
    
    // Create canvas for frame capture
    this.canvas = document.createElement('canvas');
    this.ctx = this.canvas.getContext('2d');
  }
  
  /**
   * Start camera and begin capturing frames
   */
  async start(): Promise<void> {
    try {
      // Request camera access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          frameRate: { ideal: this.config.captureFrameRate }
        },
        audio: false
      });
      
      // Create video element
      this.videoElement = document.createElement('video');
      this.videoElement.srcObject = this.mediaStream;
      this.videoElement.autoplay = true;
      this.videoElement.playsInline = true;
      
      // Wait for video to be ready
      await new Promise<void>((resolve) => {
        this.videoElement!.onloadedmetadata = () => {
          this.videoElement!.play();
          resolve();
        };
      });
      
      // Set canvas size to match video
      this.canvas!.width = this.videoElement.videoWidth;
      this.canvas!.height = this.videoElement.videoHeight;
      
      // Connect WebSocket
      await this.connectWebSocket();
      
      // Start capture loop
      this.startCapture();
      
      console.log('ASL capture started');
    } catch (error) {
      console.error('Failed to start ASL capture:', error);
      this.handleError({
        type: 'error',
        code: 'CAMERA_FAILURE',
        message: error instanceof Error ? error.message : 'Failed to access camera',
        severity: 'fatal',
        timestamp: Date.now()
      });
      throw error;
    }
  }
  
  /**
   * Stop capturing and cleanup resources
   */
  stop(): void {
    this.isCapturing = false;
    
    // Stop capture intervals
    if (this.captureIntervalId !== null) {
      clearInterval(this.captureIntervalId);
      this.captureIntervalId = null;
    }
    
    if (this.sendIntervalId !== null) {
      clearInterval(this.sendIntervalId);
      this.sendIntervalId = null;
    }
    
    // Close WebSocket
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    // Stop media stream
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }
    
    // Cleanup video element
    if (this.videoElement) {
      this.videoElement.srcObject = null;
      this.videoElement = null;
    }
    
    console.log('ASL capture stopped');
  }
  
  /**
   * Connect to WebSocket server
   */
  private async connectWebSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = `${this.config.backendUrl}/ws/cv/${this.config.sessionId}/${this.config.userId}`;
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectCount = 0;
        this.onConnectionChangeCallback?.(true);
        resolve();
      };
      
      this.ws.onmessage = (event) => {
        this.handleServerMessage(JSON.parse(event.data));
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };
      
      this.ws.onclose = () => {
        console.log('WebSocket closed');
        this.onConnectionChangeCallback?.(false);
        this.attemptReconnect();
      };
    });
  }
  
  /**
   * Attempt to reconnect WebSocket
   */
  private async attemptReconnect(): Promise<void> {
    if (this.reconnectCount >= this.config.reconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.handleError({
        type: 'error',
        code: 'INVALID_SESSION',
        message: 'Failed to reconnect to server',
        severity: 'fatal',
        timestamp: Date.now()
      });
      return;
    }
    
    this.reconnectCount++;
    console.log(`Reconnecting... (${this.reconnectCount}/${this.config.reconnectAttempts})`);
    
    await new Promise(resolve => setTimeout(resolve, this.config.reconnectDelay));
    
    try {
      await this.connectWebSocket();
    } catch (error) {
      console.error('Reconnection failed:', error);
    }
  }
  
  /**
   * Start frame capture loop
   */
  private startCapture(): void {
    this.isCapturing = true;
    
    // Capture frames at captureFrameRate
    const captureInterval = 1000 / this.config.captureFrameRate;
    this.captureIntervalId = window.setInterval(() => {
      this.captureFrame();
    }, captureInterval);
    
    // Send frames at sendFrameRate
    const sendInterval = 1000 / this.config.sendFrameRate;
    this.sendIntervalId = window.setInterval(() => {
      this.sendFrame();
    }, sendInterval);
  }
  
  /**
   * Capture single frame from video
   */
  private captureFrame(): void {
    if (!this.isCapturing || !this.videoElement || !this.ctx || !this.canvas) {
      return;
    }
    
    try {
      // Draw video frame to canvas
      this.ctx.drawImage(this.videoElement, 0, 0, this.canvas.width, this.canvas.height);
      
      // Convert to JPEG base64
      this.lastCapturedFrame = this.canvas.toDataURL('image/jpeg', this.config.jpegQuality);
    } catch (error) {
      console.error('Frame capture failed:', error);
    }
  }
  
  /**
   * Send captured frame via WebSocket
   */
  private sendFrame(): void {
    if (!this.lastCapturedFrame || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }
    
    try {
      // Extract base64 data (remove data:image/jpeg;base64, prefix)
      const base64Data = this.lastCapturedFrame.split(',')[1];
      
      const message: VideoFrameMessage = {
        type: 'video_frame',
        frame_id: this.frameId++,
        timestamp: Date.now(),
        image: base64Data,
        session_id: this.config.sessionId,
        user_id: this.config.userId
      };
      
      this.ws.send(JSON.stringify(message));
    } catch (error) {
      console.error('Frame send failed:', error);
    }
  }
  
  /**
   * Handle incoming server message
   */
  private handleServerMessage(message: ServerMessage): void {
    switch (message.type) {
      case 'caption':
        this.onCaptionCallback?.(message);
        break;
      
      case 'audio':
        this.onAudioCallback?.(message);
        break;
      
      case 'error':
        this.handleError(message);
        break;
    }
  }
  
  /**
   * Handle error message
   */
  private handleError(error: ErrorMessage): void {
    console.error('ASL error:', error);
    this.onErrorCallback?.(error);
    
    if (error.severity === 'fatal') {
      this.stop();
    }
  }
  
  /**
   * Register callback for caption messages
   */
  onCaption(callback: (caption: CaptionMessage) => void): void {
    this.onCaptionCallback = callback;
  }
  
  /**
   * Register callback for audio messages
   */
  onAudio(callback: (audio: AudioMessage) => void): void {
    this.onAudioCallback = callback;
  }
  
  /**
   * Register callback for error messages
   */
  onError(callback: (error: ErrorMessage) => void): void {
    this.onErrorCallback = callback;
  }
  
  /**
   * Register callback for connection state changes
   */
  onConnectionChange(callback: (connected: boolean) => void): void {
    this.onConnectionChangeCallback = callback;
  }
  
  /**
   * Check if currently capturing
   */
  isActive(): boolean {
    return this.isCapturing;
  }
}
