const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
      throw new Error(`Failed to create room: ${response.statusText}`);
    }
    
    return response.json();
  },

  async validateRoom(roomCode: string): Promise<RoomValidateResponse> {
    const response = await fetch(`${API_BASE_URL}/api/rooms/${roomCode}/validate`);
    
    if (!response.ok) {
      throw new Error(`Failed to validate room: ${response.statusText}`);
    }
    
    return response.json();
  },

  async joinRoom(roomCode: string, userId: string, userName: string) {
    const response = await fetch(`${API_BASE_URL}/api/rooms/${roomCode}/join`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, user_name: userName })
    });
    
    if (!response.ok) {
      throw new Error(`Failed to join room: ${response.statusText}`);
    }
    
    return response.json();
  },

  async processFrame(frame: string, userId: string, sessionId: string): Promise<MLResult> {
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
        signal: AbortSignal.timeout(5000)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('ML processing failed:', error);
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
