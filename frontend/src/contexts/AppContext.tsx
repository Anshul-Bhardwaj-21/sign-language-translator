import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

import type { AppUser, RecentRoom, UserPreferences } from '../types/app'

interface LoginPayload {
  displayName: string
  email?: string
  guest?: boolean
}

interface AppContextValue {
  user: AppUser | null
  preferences: UserPreferences
  recentRooms: RecentRoom[]
  login: (payload: LoginPayload) => void
  logout: () => void
  updatePreferences: (updates: Partial<UserPreferences>) => void
  rememberRoom: (room: RecentRoom) => void
}

const USER_KEY = 'signbridge.user'
const PREFERENCES_KEY = 'signbridge.preferences'
const ROOMS_KEY = 'signbridge.recentRooms'

const defaultPreferences: UserPreferences = {
  cameraEnabled: true,
  micEnabled: true,
  translationEnabled: true,
  accessibilityMode: false,
  showVisionOverlay: true,
  autoSpeakCaptions: false,
  captureIntervalMs: 1200,
  preferredLayout: 'focus',
}

const AppContext = createContext<AppContextValue | undefined>(undefined)

function loadJson<T>(key: string, fallback: T): T {
  const raw = localStorage.getItem(key)
  if (!raw) {
    return fallback
  }

  try {
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AppUser | null>(() => loadJson<AppUser | null>(USER_KEY, null))
  const [preferences, setPreferences] = useState<UserPreferences>(() =>
    loadJson<UserPreferences>(PREFERENCES_KEY, defaultPreferences),
  )
  const [recentRooms, setRecentRooms] = useState<RecentRoom[]>(() => loadJson<RecentRoom[]>(ROOMS_KEY, []))

  useEffect(() => {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  }, [user])

  useEffect(() => {
    localStorage.setItem(PREFERENCES_KEY, JSON.stringify(preferences))
  }, [preferences])

  useEffect(() => {
    localStorage.setItem(ROOMS_KEY, JSON.stringify(recentRooms))
  }, [recentRooms])

  const login = ({ displayName, email, guest = false }: LoginPayload) => {
    setUser({
      id: crypto.randomUUID(),
      displayName,
      email,
      isGuest: guest,
    })
  }

  const logout = () => {
    setUser(null)
  }

  const updatePreferences = (updates: Partial<UserPreferences>) => {
    setPreferences((current) => ({ ...current, ...updates }))
  }

  const rememberRoom = (room: RecentRoom) => {
    setRecentRooms((current) => [room, ...current.filter((entry) => entry.roomId !== room.roomId)].slice(0, 6))
  }

  return (
    <AppContext.Provider value={{ user, preferences, recentRooms, login, logout, updatePreferences, rememberRoom }}>
      {children}
    </AppContext.Provider>
  )
}

export function useAppContext() {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider')
  }
  return context
}
