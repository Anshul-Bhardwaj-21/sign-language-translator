import { BrowserRouter, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { Settings } from 'lucide-react'
import { ProtectedRoute } from './components/ProtectedRoute'
import { useAppContext } from './contexts/AppContext'
import { DashboardPage } from './pages/DashboardPage'
import { LandingPage } from './pages/LandingPage'
import { LobbyPage } from './pages/LobbyPage'
import { LoginPage } from './pages/LoginPage'
import { PremiumRoomExperiencePage } from './pages/PremiumRoomExperiencePage'
import { SettingsPage } from './pages/SettingsPage'

function AppShell() {
  const { user, logout } = useAppContext()
  const location = useLocation()
  const isImmersive = location.pathname.startsWith('/room/') || location.pathname.startsWith('/lobby')
  const isLanding = location.pathname === '/'

  return (
    <div className={`app-shell${isImmersive ? ' app-shell--immersive' : ''}`}>
      {!isImmersive && !isLanding && (
        <header className="sb-topbar">
          <NavLink to="/" className="sb-topbar__brand">
            <span className="sb-topbar__logo">SB</span>
            <span className="sb-topbar__name">SignBridge</span>
          </NavLink>
          <nav className="sb-topbar__nav">
            {user ? (
              <>
                <NavLink to="/dashboard" className="sb-topbar__link">Dashboard</NavLink>
                <NavLink to="/settings" className="sb-topbar__link">
                  <Settings size={15} />
                </NavLink>
                <button className="sb-topbar__signout" onClick={logout}>Sign out</button>
              </>
            ) : (
              <NavLink to="/login" className="sb-topbar__link">Sign in</NavLink>
            )}
          </nav>
        </header>
      )}
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/lobby" element={<LobbyPage />} />
          <Route path="/lobby/:roomId" element={<LobbyPage />} />
          <Route path="/room/:roomId" element={<PremiumRoomExperiencePage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  )
}
