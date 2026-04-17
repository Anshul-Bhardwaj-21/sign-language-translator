import type { HealthSnapshot, PredictionSnapshot, RoomSnapshot } from '../types/app'

const API_BASE_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') || 'http://localhost:8001'

type ApiEnvelope<T> = {
  success: boolean
  message: string
  data: T
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Request failed with status ${response.status}`)
  }

  const payload = (await response.json()) as ApiEnvelope<T>
  return payload.data
}

export const api = {
  async getHealth() {
    return request<HealthSnapshot>('/health')
  },

  async getIceServers(): Promise<RTCIceServer[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/ice-servers`)
      if (!res.ok) throw new Error('ice-servers fetch failed')
      const data = await res.json() as { iceServers: RTCIceServer[] }
      return data.iceServers
    } catch {
      // Fallback to Google STUN if backend unreachable
      return [{ urls: 'stun:stun.l.google.com:19302' }]
    }
  },

  async createRoom(input: {
    displayName: string
    participantId: string
    roomName?: string
    accessibilityMode?: boolean
    maxParticipants?: number
  }) {
    return request<RoomSnapshot>('/rooms', {
      method: 'POST',
      body: JSON.stringify({
        display_name: input.displayName,
        participant_id: input.participantId,
        room_name: input.roomName ?? 'Live translation room',
        accessibility_mode: input.accessibilityMode ?? true,
        max_participants: input.maxParticipants ?? 2,
      }),
    })
  },

  async joinRoom(roomId: string, input: { displayName: string; participantId: string }) {
    return request<RoomSnapshot>(`/rooms/${roomId}/join`, {
      method: 'POST',
      body: JSON.stringify({
        display_name: input.displayName,
        participant_id: input.participantId,
      }),
    })
  },

  async getRoom(roomId: string) {
    return request<RoomSnapshot>(`/rooms/${roomId}`)
  },

  async predict(input: {
    imageBase64: string
    roomId: string
    participantId: string
  }) {
    return request<PredictionSnapshot>('/predict', {
      method: 'POST',
      body: JSON.stringify({
        image_base64: input.imageBase64,
        room_id: input.roomId,
        participant_id: input.participantId,
        timestamp_ms: Date.now(),
      }),
    })
  },
}

export function getRealtimeUrl(roomId: string, participantId: string, displayName: string) {
  const configured = import.meta.env.VITE_WS_URL
  const baseUrl = configured ?? API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://')
  const params = new URLSearchParams({
    participant_id: participantId,
    display_name: displayName,
  })
  return `${baseUrl}/ws/rooms/${roomId}?${params.toString()}`
}
