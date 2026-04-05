const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

// Logging utility
const log = {
  info: (message: string, ...args: any[]) => {
    console.log(`[API] ${message}`, ...args);
  },
  error: (message: string, ...args: any[]) => {
    console.error(`[API ERROR] ${message}`, ...args);
  },
  warn: (message: string, ...args: any[]) => {
    console.warn(`[API WARNING] ${message}`, ...args);
  },
  debug: (message: string, ...args: any[]) => {
    if (import.meta.env.DEV) {
      console.debug(`[API DEBUG] ${message}`, ...args);
    }
  },
};

export interface RoomCreateResponse {
  room_code: string;
  room_id: string;
  created_at: number;
  websocket_url: string;
}

export interface RoomValidateResponse {
  valid: boolean;
  room_id?: string;
  participants_count?: number;
  is_full?: boolean;
  accessibility_mode?: boolean;
  error?: string;
}

export interface MLResult {
  success: boolean;
  hand_detected: boolean;
  landmarks?: number[][];
  gesture: string;
  confidence: number;
  caption: string;
  movement_state: string;
  processing_time_ms: number;
  error?: string;
  fallback_mode?: string;
}

export const api = {
  async createRoom(hostUserId: string, accessibilityMode: boolean = false): Promise<RoomCreateResponse> {
    log.info('Creating room', { hostUserId, accessibilityMode });
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/rooms/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          host_user_id: hostUserId,
          accessibility_mode: accessibilityMode,
          max_participants: 10
        })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        log.error('Failed to create room', { status: response.status, error: errorText });
        throw new Error(`Failed to create room: ${response.statusText}`);
      }
      
      const data = await response.json();
      log.info('Room created successfully', data);
      return data;
    } catch (error) {
      log.error('Create room error', error);
      throw error;
    }
  },

  async validateRoom(roomCode: string): Promise<RoomValidateResponse> {
    log.info('Validating room', { roomCode });
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/rooms/${roomCode}/validate`);
      
      if (!response.ok) {
        const errorText = await response.text();
        log.error('Failed to validate room', { status: response.status, error: errorText });
        throw new Error(`Failed to validate room: ${response.statusText}`);
      }
      
      const data = await response.json();
      log.info('Room validation result', data);
      return data;
    } catch (error) {
      log.error('Validate room error', error);
      throw error;
    }
  },

  async joinRoom(roomCode: string, userId: string, userName: string) {
    log.info('Joining room', { roomCode, userId, userName });
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/rooms/${roomCode}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, user_name: userName })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        log.error('Failed to join room', { status: response.status, error: errorText });
        throw new Error(`Failed to join room: ${response.statusText}`);
      }
      
      const data = await response.json();
      log.info('Joined room successfully', data);
      return data;
    } catch (error) {
      log.error('Join room error', error);
      throw error;
    }
  },

  async processFrame(frame: string, userId: string, sessionId: string): Promise<MLResult> {
    log.debug('Processing frame', { userId, sessionId, frameLength: frame.length });
    
    // Manual timeout implementation for browser compatibility
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      log.warn('Frame processing timeout');
      controller.abort();
    }, 5000);

    try {
      const response = await fetch(`${API_BASE_URL}/api/ml/process-frame`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          frame,
          user_id: userId,
          session_id: sessionId,
          timestamp: Date.now() / 1000
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        log.error('Frame processing failed', { status: response.status });
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      log.debug('Frame processed successfully', { 
        gesture: data.gesture, 
        confidence: data.confidence,
        handDetected: data.hand_detected 
      });
      return data;
    } catch (error) {
      clearTimeout(timeoutId);
      
      log.error('ML processing failed', error);
      return {
        success: false,
        hand_detected: false,
        gesture: 'none',
        confidence: 0,
        caption: '',
        movement_state: 'error',
        processing_time_ms: 0,
        error: error instanceof Error ? error.message : 'Unknown error',
        fallback_mode: 'text_only'
      };
    }
  }
};
