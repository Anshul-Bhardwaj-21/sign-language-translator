import { useEffect, useState } from 'react'

export function useNetworkStatus() {
  const readEffectiveType = () => {
    if (typeof navigator === 'undefined') {
      return 'unknown'
    }

    const connection = (navigator as Navigator & { connection?: { effectiveType?: string } }).connection
    return connection?.effectiveType ?? 'online'
  }

  const [online, setOnline] = useState(() => (typeof navigator === 'undefined' ? true : navigator.onLine))
  const [effectiveType, setEffectiveType] = useState(readEffectiveType)

  useEffect(() => {
    const handleOnline = () => {
      setOnline(true)
      setEffectiveType(readEffectiveType())
    }
    const handleOffline = () => {
      setOnline(false)
      setEffectiveType('offline')
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return { online, effectiveType }
}
