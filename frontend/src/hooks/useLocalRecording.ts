import { useCallback, useEffect, useRef, useState } from 'react'

const RECORDING_MIME_TYPES = ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm']

function getSupportedMimeType() {
  if (typeof MediaRecorder === 'undefined' || typeof MediaRecorder.isTypeSupported !== 'function') {
    return undefined
  }

  return RECORDING_MIME_TYPES.find((mimeType) => MediaRecorder.isTypeSupported(mimeType))
}

function downloadRecording(blob: Blob, filePrefix: string) {
  const recordingUrl = URL.createObjectURL(blob)
  const downloadLink = document.createElement('a')
  downloadLink.href = recordingUrl
  downloadLink.download = `${filePrefix}-${new Date().toISOString().replace(/[:.]/g, '-')}.webm`
  document.body.append(downloadLink)
  downloadLink.click()
  downloadLink.remove()
  window.setTimeout(() => {
    URL.revokeObjectURL(recordingUrl)
  }, 0)
}

export function useLocalRecording(stream: MediaStream | null, filePrefix = 'signbridge-session') {
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<number | null>(null)

  const [isRecording, setIsRecording] = useState(false)
  const [durationMs, setDurationMs] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      window.clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const stopRecording = useCallback(() => {
    const recorder = recorderRef.current
    if (!recorder || recorder.state === 'inactive') {
      return false
    }

    recorder.stop()
    return true
  }, [])

  const startRecording = useCallback(() => {
    if (!stream) {
      setError('Turn on your camera or microphone before starting a local recording.')
      return false
    }

    if (typeof MediaRecorder === 'undefined') {
      setError('This browser does not support local recording.')
      return false
    }

    if (recorderRef.current?.state === 'recording') {
      return true
    }

    const mimeType = getSupportedMimeType()
    chunksRef.current = []
    setError(null)
    setDurationMs(0)

    try {
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream)

      recorder.onstart = () => {
        setIsRecording(true)
        const startedAt = Date.now()
        clearTimer()
        timerRef.current = window.setInterval(() => {
          setDurationMs(Date.now() - startedAt)
        }, 1000)
      }

      recorder.onerror = () => {
        setError('The browser stopped the recording unexpectedly.')
      }

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      recorder.onstop = () => {
        setIsRecording(false)
        clearTimer()

        const recordingBlob = new Blob(chunksRef.current, {
          type: recorder.mimeType || mimeType || 'video/webm',
        })

        if (recordingBlob.size > 0) {
          downloadRecording(recordingBlob, filePrefix)
        }

        chunksRef.current = []
      }

      recorder.start(1000)
      recorderRef.current = recorder
      return true
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Unable to start local recording.')
      return false
    }
  }, [clearTimer, filePrefix, stream])

  useEffect(() => {
    if (!stream && recorderRef.current?.state === 'recording') {
      stopRecording()
    }
  }, [stopRecording, stream])

  useEffect(
    () => () => {
      clearTimer()
      if (recorderRef.current && recorderRef.current.state !== 'inactive') {
        recorderRef.current.stop()
      }
    },
    [clearTimer],
  )

  return {
    isRecording,
    durationMs,
    error,
    startRecording,
    stopRecording,
  }
}
