import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { api, getRealtimeUrl } from '../services/api'
import type {
  AppUser,
  CaptionMessage,
  ChatMessage,
  ConnectionStatus,
  PredictionSnapshot,
  RecentRoom,
  RoomSnapshot,
  UserPreferences,
} from '../types/app'

interface UseRoomSessionArgs {
  roomId: string
  user: AppUser
  preferences: UserPreferences
  rememberRoom: (room: RecentRoom) => void
}

export function useRoomSession({ roomId, user, preferences, rememberRoom }: UseRoomSessionArgs) {
  const [room, setRoom] = useState<RoomSnapshot | null>(null)
  const [localStream, setLocalStream] = useState<MediaStream | null>(null)
  const [remoteStreams, setRemoteStreams] = useState<Record<string, MediaStream>>({})
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [captionMessages, setCaptionMessages] = useState<CaptionMessage[]>([])
  const [latestPrediction, setLatestPrediction] = useState<PredictionSnapshot | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting')
  const [peerStates, setPeerStates] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const localVideoRef = useRef<HTMLVideoElement>(null)
  const localStreamRef = useRef<MediaStream | null>(null)
  const activeSessionRef = useRef(true)
  const websocketRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<number | null>(null)
  const heartbeatRef = useRef<number | null>(null)
  const predictionLockRef = useRef(false)
  const lastPublishedCaptionRef = useRef<string | null>(null)
  const selectedDevicesRef = useRef<{ cameraId?: string; micId?: string }>({})
  const peerConnectionsRef = useRef<Map<string, RTCPeerConnection>>(new Map())
  const iceServersRef = useRef<RTCIceServer[]>([{ urls: 'stun:stun.l.google.com:19302' }])
  // Stable refs to latest callbacks — avoids re-running bootstrap on every preference change
  const connectRealtimeRef = useRef<() => void>(() => undefined)
  const ensureMediaRef = useRef<() => Promise<void>>(() => Promise.resolve())
  const rememberRoomRef = useRef(rememberRoom)

  const otherParticipants = useMemo(
    () => room?.participants.filter((participant) => participant.participant_id !== user.id) ?? [],
    [room, user.id],
  )

  const sendRealtime = useCallback((type: string, payload: Record<string, unknown>) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({ type, payload }))
    }
  }, [])

  const updateParticipantState = useCallback((participantId: string, updates: Partial<RoomSnapshot['participants'][number]>) => {
    setRoom((current) => {
      if (!current) {
        return current
      }
      return {
        ...current,
        participants: current.participants.map((participant) =>
          participant.participant_id === participantId ? { ...participant, ...updates } : participant,
        ),
      }
    })
  }, [])

  const closePeerConnection = useCallback((participantId: string) => {
    const connection = peerConnectionsRef.current.get(participantId)
    if (connection) {
      connection.onicecandidate = null
      connection.ontrack = null
      connection.onconnectionstatechange = null
      connection.close()
      peerConnectionsRef.current.delete(participantId)
    }

    setRemoteStreams((current) => {
      const next = { ...current }
      delete next[participantId]
      return next
    })
    setPeerStates((current) => {
      const next = { ...current }
      delete next[participantId]
      return next
    })
  }, [])

  const createPeerConnection = useCallback(
    (participantId: string) => {
      const existing = peerConnectionsRef.current.get(participantId)
      if (existing) {
        return existing
      }

      const peerConnection = new RTCPeerConnection({
        iceServers: iceServersRef.current,
      })

      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach((track) => {
          peerConnection.addTrack(track, localStreamRef.current!)
        })
      }

      peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
          sendRealtime('signal.ice-candidate', {
            to_participant_id: participantId,
            candidate: event.candidate.toJSON(),
          })
        }
      }

      peerConnection.ontrack = (event) => {
        const [stream] = event.streams
        if (stream) {
          setRemoteStreams((current) => ({ ...current, [participantId]: stream }))
        }
      }

      peerConnection.onconnectionstatechange = () => {
        setPeerStates((current) => ({
          ...current,
          [participantId]: peerConnection.connectionState,
        }))

        if (peerConnection.connectionState === 'failed' || peerConnection.connectionState === 'closed') {
          closePeerConnection(participantId)
        }
      }

      peerConnectionsRef.current.set(participantId, peerConnection)
      return peerConnection
    },
    [closePeerConnection, sendRealtime],
  )

  const createOffer = useCallback(
    async (participantId: string) => {
      const peerConnection = createPeerConnection(participantId)
      const offer = await peerConnection.createOffer()
      await peerConnection.setLocalDescription(offer)
      sendRealtime('signal.offer', {
        to_participant_id: participantId,
        description: offer,
      })
    },
    [createPeerConnection, sendRealtime],
  )

  const syncLocalTracks = useCallback(async () => {
    if (!localStreamRef.current) {
      return
    }

    for (const [participantId, peerConnection] of peerConnectionsRef.current.entries()) {
      const senders = peerConnection.getSenders()
      localStreamRef.current.getTracks().forEach((track) => {
        const sender = senders.find((entry) => entry.track?.kind === track.kind)
        if (sender) {
          void sender.replaceTrack(track)
        } else {
          peerConnection.addTrack(track, localStreamRef.current!)
        }
      })

      if (peerConnection.signalingState === 'stable') {
        await createOffer(participantId)
      }
    }
  }, [createOffer])

  const stopLocalStream = useCallback(() => {
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((track) => track.stop())
      localStreamRef.current = null
      setLocalStream(null)
    }
  }, [])

  const ensureMedia = useCallback(async () => {
    const needsVideo = preferences.cameraEnabled
    const needsAudio = preferences.micEnabled

    if (!needsVideo && !needsAudio) {
      stopLocalStream()
      return
    }

    const cameraChanged = selectedDevicesRef.current.cameraId !== preferences.preferredCameraId
    const micChanged = selectedDevicesRef.current.micId !== preferences.preferredMicId
    const mustReacquire = cameraChanged || micChanged || !localStreamRef.current

    if (mustReacquire) {
      stopLocalStream()

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: needsAudio
          ? {
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true,
              deviceId: preferences.preferredMicId ? { exact: preferences.preferredMicId } : undefined,
            }
          : false,
        video: needsVideo
          ? {
              width: { ideal: 1280 },
              height: { ideal: 720 },
              frameRate: { ideal: 24, max: 30 },
              facingMode: 'user',
              deviceId: preferences.preferredCameraId ? { exact: preferences.preferredCameraId } : undefined,
            }
          : false,
      })
      stream.getTracks().forEach((track) => {
        track.onended = () => {
          setError(track.kind === 'video' ? 'Camera disconnected during the meeting.' : 'Microphone disconnected during the meeting.')
        }
      })
      selectedDevicesRef.current = {
        cameraId: preferences.preferredCameraId,
        micId: preferences.preferredMicId,
      }
      localStreamRef.current = stream
      setLocalStream(stream)
      return
    }

    const activeStream = localStreamRef.current
    if (!activeStream) {
      return
    }

    activeStream.getAudioTracks().forEach((track) => {
      track.enabled = preferences.micEnabled
    })
    activeStream.getVideoTracks().forEach((track) => {
      track.enabled = preferences.cameraEnabled
    })
  }, [
    preferences.cameraEnabled,
    preferences.micEnabled,
    preferences.preferredCameraId,
    preferences.preferredMicId,
    stopLocalStream,
  ])

  // Keep ref in sync so bootstrap can call latest version without re-running
  ensureMediaRef.current = ensureMedia

  const connectRealtime = useCallback(() => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    setConnectionStatus((current) => (current === 'connected' ? current : 'connecting'))
    const socket = new WebSocket(getRealtimeUrl(roomId, user.id, user.displayName))
    websocketRef.current = socket

    socket.onopen = () => {
      setConnectionStatus('connected')
      if (heartbeatRef.current) {
        window.clearInterval(heartbeatRef.current)
      }
      heartbeatRef.current = window.setInterval(() => {
        sendRealtime('ping', {})
      }, 15000)
    }

    socket.onclose = () => {
      if (!activeSessionRef.current) {
        return
      }
      setConnectionStatus('reconnecting')
      if (heartbeatRef.current) {
        window.clearInterval(heartbeatRef.current)
      }
      reconnectTimerRef.current = window.setTimeout(() => {
        connectRealtime()
      }, 2000)
    }

    socket.onerror = () => {
      setConnectionStatus('error')
    }

    socket.onmessage = async (event) => {
      const envelope = JSON.parse(event.data) as { type: string; payload: Record<string, unknown> }

      if (envelope.type === 'room.snapshot') {
        const snapshot = envelope.payload as unknown as RoomSnapshot
        setRoom(snapshot)
        setChatMessages(snapshot.recent_chat ?? [])
        setCaptionMessages(snapshot.recent_captions ?? [])
        rememberRoom({
          roomId: snapshot.room_id,
          roomName: snapshot.room_name,
          lastJoinedAt: new Date().toISOString(),
        })
        return
      }

      if (envelope.type === 'room.participant-joined') {
        const joined = envelope.payload as { participant_id: string; display_name: string }
        setRoom((current) => {
          if (!current) {
            return current
          }
          const exists = current.participants.some((participant) => participant.participant_id === joined.participant_id)
          if (exists) {
            return current
          }
          return {
            ...current,
            participants: [
              ...current.participants,
              {
                participant_id: joined.participant_id,
                display_name: joined.display_name,
                role: 'guest',
                joined_at: new Date().toISOString(),
                connected: true,
                mic_enabled: true,
                camera_enabled: true,
              },
            ],
          }
        })
        if (joined.participant_id !== user.id) {
          await createOffer(joined.participant_id)
        }
        return
      }

      if (envelope.type === 'room.participant-left') {
        const left = envelope.payload as { participant_id: string }
        closePeerConnection(left.participant_id)
        updateParticipantState(left.participant_id, { connected: false })
        return
      }

      if (envelope.type === 'signal.offer') {
        const payload = envelope.payload as {
          from_participant_id: string
          description: RTCSessionDescriptionInit
        }
        const peerConnection = createPeerConnection(payload.from_participant_id)
        await peerConnection.setRemoteDescription(payload.description)
        const answer = await peerConnection.createAnswer()
        await peerConnection.setLocalDescription(answer)
        sendRealtime('signal.answer', {
          to_participant_id: payload.from_participant_id,
          description: answer,
        })
        return
      }

      if (envelope.type === 'signal.answer') {
        const payload = envelope.payload as {
          from_participant_id: string
          description: RTCSessionDescriptionInit
        }
        const peerConnection = peerConnectionsRef.current.get(payload.from_participant_id)
        if (peerConnection) {
          await peerConnection.setRemoteDescription(payload.description)
        }
        return
      }

      if (envelope.type === 'signal.ice-candidate') {
        const payload = envelope.payload as {
          from_participant_id: string
          candidate: RTCIceCandidateInit
        }
        const peerConnection = createPeerConnection(payload.from_participant_id)
        await peerConnection.addIceCandidate(payload.candidate)
        return
      }

      if (envelope.type === 'chat.message') {
        setChatMessages((current) => [...current, envelope.payload as unknown as ChatMessage].slice(-40))
        return
      }

      if (envelope.type === 'caption.publish') {
        setCaptionMessages((current) => [...current, envelope.payload as unknown as CaptionMessage].slice(-40))
        return
      }

      if (envelope.type === 'caption.clear') {
        setCaptionMessages([])
        setLatestPrediction((current) =>
          current
            ? {
                ...current,
                confirmed_caption: null,
                caption_history: [],
              }
            : current,
        )
        lastPublishedCaptionRef.current = null
        return
      }

      if (envelope.type === 'status.update') {
        const payload = envelope.payload as { participant_id: string; mic_enabled?: boolean; camera_enabled?: boolean; screen_sharing?: boolean }
        updateParticipantState(payload.participant_id, {
          mic_enabled: payload.mic_enabled ?? true,
          camera_enabled: payload.camera_enabled ?? true,
          ...(payload.screen_sharing !== undefined && { screen_sharing: payload.screen_sharing } as Record<string, unknown>),
        })
        return
      }

      if (envelope.type === 'pong') {
        setConnectionStatus('connected')
        return
      }

      if (envelope.type === 'system.error') {
        setError(String(envelope.payload.message ?? 'Realtime event failed.'))
      }
    }
  }, [closePeerConnection, createOffer, createPeerConnection, rememberRoom, roomId, sendRealtime, updateParticipantState, user.displayName, user.id])

  // Keep ref in sync — bootstrap calls this without it being a dependency
  connectRealtimeRef.current = connectRealtime
  rememberRoomRef.current = rememberRoom

  const sendChat = useCallback(
    (message: string) => {
      const trimmed = message.trim()
      if (!trimmed) {
        return
      }
      sendRealtime('chat.message', { message: trimmed })
    },
    [sendRealtime],
  )

  const clearCaptions = useCallback(() => {
    setCaptionMessages([])
    setLatestPrediction((current) =>
      current
        ? {
            ...current,
            confirmed_caption: null,
            caption_history: [],
          }
        : current,
    )
    lastPublishedCaptionRef.current = null
    sendRealtime('caption.clear', {})
  }, [sendRealtime])

  const dismissError = useCallback(() => {
    setError(null)
  }, [])

  const toggleStatus = useCallback(
    (payload: { mic_enabled?: boolean; camera_enabled?: boolean }) => {
      sendRealtime('status.update', payload)
    },
    [sendRealtime],
  )

  useEffect(() => {
    let active = true
    activeSessionRef.current = true

    async function bootstrap() {
      setLoading(true)
      setError(null)
      try {
        // Fetch ICE servers from backend (includes TURN if configured)
        iceServersRef.current = await api.getIceServers()

        const joinedRoom = await api.joinRoom(roomId, {
          displayName: user.displayName,
          participantId: user.id,
        })
        if (!active) {
          return
        }
        setRoom(joinedRoom)
        setChatMessages(joinedRoom.recent_chat ?? [])
        setCaptionMessages(joinedRoom.recent_captions ?? [])
        rememberRoomRef.current({
          roomId: joinedRoom.room_id,
          roomName: joinedRoom.room_name,
          lastJoinedAt: new Date().toISOString(),
        })
        await ensureMediaRef.current()
        connectRealtimeRef.current()
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : 'Unable to enter room.')
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    void bootstrap()

    return () => {
      active = false
      activeSessionRef.current = false
      websocketRef.current?.close()
      setConnectionStatus('disconnected')
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current)
      }
      if (heartbeatRef.current) {
        window.clearInterval(heartbeatRef.current)
      }
      peerConnectionsRef.current.forEach((_, participantId) => {
        closePeerConnection(participantId)
      })
      stopLocalStream()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roomId, user.id, user.displayName, closePeerConnection, stopLocalStream])

  useEffect(() => {
    void ensureMedia().catch((caughtError) => {
      setError(caughtError instanceof Error ? caughtError.message : 'Unable to initialize devices.')
    })
  }, [ensureMedia])

  useEffect(() => {
    localStreamRef.current = localStream
  }, [localStream])

  useEffect(() => {
    void syncLocalTracks()
  }, [localStream, syncLocalTracks])

  useEffect(() => {
    toggleStatus({
      mic_enabled: preferences.micEnabled,
      camera_enabled: preferences.cameraEnabled,
    })
  }, [preferences.cameraEnabled, preferences.micEnabled, toggleStatus])

  useEffect(() => {
    const shouldRunVisionPipeline = preferences.translationEnabled || preferences.accessibilityMode
    if (!shouldRunVisionPipeline || !localVideoRef.current || !room || !preferences.cameraEnabled) {
      return
    }

    const canvas = document.createElement('canvas')
    const context = canvas.getContext('2d')
    if (!context) {
      return
    }

    const interval = window.setInterval(async () => {
      const video = localVideoRef.current
      if (!video || predictionLockRef.current || video.readyState < 2) {
        return
      }

      canvas.width = video.videoWidth || 640
      canvas.height = video.videoHeight || 360
      context.drawImage(video, 0, 0, canvas.width, canvas.height)
      predictionLockRef.current = true

      try {
        const imageBase64 = canvas.toDataURL('image/jpeg', 0.7)
        const prediction = await api.predict({
          imageBase64,
          roomId: room.room_id,
          participantId: user.id,
        })
        setLatestPrediction(prediction)

        if (
          preferences.translationEnabled &&
          prediction.confirmed_caption &&
          prediction.confirmed_caption !== lastPublishedCaptionRef.current
        ) {
          lastPublishedCaptionRef.current = prediction.confirmed_caption
          sendRealtime('caption.publish', {
            caption: prediction.confirmed_caption,
            confidence: prediction.confidence,
          })
        }
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : 'Prediction failed.')
      } finally {
        predictionLockRef.current = false
      }
    }, preferences.captureIntervalMs)

    return () => {
      window.clearInterval(interval)
    }
  }, [
    preferences.accessibilityMode,
    preferences.cameraEnabled,
    preferences.captureIntervalMs,
    preferences.translationEnabled,
    room,
    sendRealtime,
    user.id,
  ])

  return {
    room,
    localStream,
    localVideoRef,
    remoteStreams,
    chatMessages,
    captionMessages,
    latestPrediction,
    connectionStatus,
    peerStates,
    otherParticipants,
    loading,
    error,
    sendChat,
    clearCaptions,
    dismissError,
    sendRealtime,
  }
}
