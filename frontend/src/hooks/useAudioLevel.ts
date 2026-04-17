import { useEffect, useState } from 'react'

export function useAudioLevel(stream: MediaStream | null, enabled: boolean) {
  const [level, setLevel] = useState(0)

  useEffect(() => {
    if (!stream || !enabled) {
      setLevel(0)
      return
    }

    const [audioTrack] = stream.getAudioTracks()
    if (!audioTrack) {
      setLevel(0)
      return
    }

    const audioContext = new AudioContext()
    const source = audioContext.createMediaStreamSource(new MediaStream([audioTrack]))
    const analyser = audioContext.createAnalyser()
    analyser.fftSize = 256
    source.connect(analyser)

    const buffer = new Uint8Array(analyser.frequencyBinCount)
    let frameId = 0

    const sample = () => {
      analyser.getByteTimeDomainData(buffer)
      let sum = 0
      for (let index = 0; index < buffer.length; index += 1) {
        const normalized = (buffer[index] - 128) / 128
        sum += normalized * normalized
      }
      const rms = Math.sqrt(sum / buffer.length)
      setLevel(Math.min(1, rms * 3.4))
      frameId = window.requestAnimationFrame(sample)
    }

    frameId = window.requestAnimationFrame(sample)

    return () => {
      window.cancelAnimationFrame(frameId)
      source.disconnect()
      analyser.disconnect()
      if (audioContext.state !== 'closed') {
        void audioContext.close().catch(() => undefined)
      }
    }
  }, [enabled, stream])

  return level
}
