import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import type { DeviceOption, PermissionState } from '../types/app'
import { useAudioLevel } from './useAudioLevel'

interface UseMediaSetupArgs {
  cameraEnabled: boolean
  micEnabled: boolean
  preferredCameraId?: string
  preferredMicId?: string
  preferredSpeakerId?: string
}

function deviceLabel(device: MediaDeviceInfo, fallback: string, index: number) {
  return device.label || `${fallback} ${index + 1}`
}

export function useMediaSetup({
  cameraEnabled,
  micEnabled,
  preferredCameraId,
  preferredMicId,
  preferredSpeakerId,
}: UseMediaSetupArgs) {
  const [previewStream, setPreviewStream] = useState<MediaStream | null>(null)
  const [cameraPermission, setCameraPermission] = useState<PermissionState>('prompt')
  const [micPermission, setMicPermission] = useState<PermissionState>('prompt')
  const [cameraError, setCameraError] = useState<string | null>(null)
  const [micError, setMicError] = useState<string | null>(null)
  const [isPreparing, setIsPreparing] = useState(false)
  const [videoInputs, setVideoInputs] = useState<DeviceOption[]>([])
  const [audioInputs, setAudioInputs] = useState<DeviceOption[]>([])
  const [audioOutputs, setAudioOutputs] = useState<DeviceOption[]>([])
  const [selectedCameraId, setSelectedCameraId] = useState(preferredCameraId)
  const [selectedMicId, setSelectedMicId] = useState(preferredMicId)
  const [selectedSpeakerId, setSelectedSpeakerId] = useState(preferredSpeakerId)
  const [compatibilityNotes, setCompatibilityNotes] = useState<string[]>([])

  const streamRef = useRef<MediaStream | null>(null)
  const audioLevel = useAudioLevel(previewStream, micEnabled)

  const supportsMedia = typeof navigator !== 'undefined' && Boolean(navigator.mediaDevices?.getUserMedia)
  const supportsSinkSelection =
    typeof document !== 'undefined' && 'setSinkId' in HTMLMediaElement.prototype

  const refreshDevices = useCallback(async () => {
    if (!navigator.mediaDevices?.enumerateDevices) {
      setCompatibilityNotes((current) =>
        current.includes('Device selection is limited in this browser.') ? current : [...current, 'Device selection is limited in this browser.'],
      )
      return
    }

    const devices = await navigator.mediaDevices.enumerateDevices()
    const nextVideoInputs = devices
      .filter((device) => device.kind === 'videoinput')
      .map((device, index) => ({
        deviceId: device.deviceId,
        label: deviceLabel(device, 'Camera', index),
      }))
    const nextAudioInputs = devices
      .filter((device) => device.kind === 'audioinput')
      .map((device, index) => ({
        deviceId: device.deviceId,
        label: deviceLabel(device, 'Microphone', index),
      }))
    const nextAudioOutputs = devices
      .filter((device) => device.kind === 'audiooutput')
      .map((device, index) => ({
        deviceId: device.deviceId,
        label: deviceLabel(device, 'Speaker', index),
      }))

    setVideoInputs(nextVideoInputs)
    setAudioInputs(nextAudioInputs)
    setAudioOutputs(nextAudioOutputs)
    setSelectedCameraId((current) => current ?? nextVideoInputs[0]?.deviceId)
    setSelectedMicId((current) => current ?? nextAudioInputs[0]?.deviceId)
    setSelectedSpeakerId((current) => current ?? nextAudioOutputs[0]?.deviceId)
  }, [])

  const stopPreview = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    setPreviewStream(null)
  }, [])

  const preparePreview = useCallback(async () => {
    if (!supportsMedia) {
      setCameraPermission('unsupported')
      setMicPermission('unsupported')
      setCompatibilityNotes((current) =>
        current.includes('This browser cannot access local media devices.')
          ? current
          : [...current, 'This browser cannot access local media devices.'],
      )
      return
    }

    if (!cameraEnabled && !micEnabled) {
      stopPreview()
      return
    }

    setIsPreparing(true)
    setCameraError(null)
    setMicError(null)

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: cameraEnabled
          ? {
              width: { ideal: 1280 },
              height: { ideal: 720 },
              facingMode: 'user',
              deviceId: selectedCameraId ? { exact: selectedCameraId } : undefined,
            }
          : false,
        audio: micEnabled
          ? {
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true,
              deviceId: selectedMicId ? { exact: selectedMicId } : undefined,
            }
          : false,
      })

      stopPreview()
      streamRef.current = stream
      setPreviewStream(stream)
      if (cameraEnabled) {
        setCameraPermission('granted')
      }
      if (micEnabled) {
        setMicPermission('granted')
      }
      await refreshDevices()
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to prepare devices.'
      if (cameraEnabled) {
        setCameraPermission('denied')
        setCameraError(message)
      }
      if (micEnabled) {
        setMicPermission('denied')
        setMicError(message)
      }
      stopPreview()
    } finally {
      setIsPreparing(false)
    }
  }, [
    cameraEnabled,
    micEnabled,
    refreshDevices,
    selectedCameraId,
    selectedMicId,
    stopPreview,
    supportsMedia,
  ])

  useEffect(() => {
    void refreshDevices()
  }, [refreshDevices])

  useEffect(() => {
    const handler = () => {
      void refreshDevices()
    }
    navigator.mediaDevices?.addEventListener?.('devicechange', handler)
    return () => {
      navigator.mediaDevices?.removeEventListener?.('devicechange', handler)
    }
  }, [refreshDevices])

  useEffect(() => {
    void preparePreview()
    return () => {
      stopPreview()
    }
  }, [preparePreview, stopPreview])

  const browserNotes = useMemo(() => {
    const notes = [...compatibilityNotes]
    if (!supportsSinkSelection) {
      notes.push('Speaker selection depends on browser support and may be unavailable.')
    }
    return Array.from(new Set(notes))
  }, [compatibilityNotes, supportsSinkSelection])

  return {
    previewStream,
    audioLevel,
    cameraPermission,
    micPermission,
    cameraError,
    micError,
    isPreparing,
    videoInputs,
    audioInputs,
    audioOutputs,
    selectedCameraId,
    selectedMicId,
    selectedSpeakerId,
    setSelectedCameraId,
    setSelectedMicId,
    setSelectedSpeakerId,
    refreshDevices,
    restartPreview: preparePreview,
    stopPreview,
    supportsMedia,
    supportsSinkSelection,
    compatibilityNotes: browserNotes,
  }
}
