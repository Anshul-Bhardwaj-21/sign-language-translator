import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppProvider } from './contexts/AppContext'
import { WebSocketProvider } from './contexts/WebSocketContext'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import LandingPageNew from './pages/LandingPageNew'
import DashboardNew from './pages/DashboardNew'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import HomePage from './pages/HomePage'
import AdminDashboard from './pages/AdminDashboard'
import PreJoinLobby from './pages/PreJoinLobby'
import VideoCallPage from './pages/VideoCallPage'

// Protected Route Component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// Admin Route Component
const AdminRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, user } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (!user?.isAdmin) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
};

function App() {
  return (
    <AppProvider>
      <WebSocketProvider>
        <ThemeProvider>
          <AuthProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/" element={<LandingPageNew />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/home" element={<HomePage />} />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <DashboardNew />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin"
                  element={
                    <AdminRoute>
                      <AdminDashboard />
                    </AdminRoute>
                  }
                />
                <Route
                  path="/lobby"
                  element={
                    <ProtectedRoute>
                      <PreJoinLobby />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/call/:roomCode"
                  element={
                    <ProtectedRoute>
                      <VideoCallPage />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </BrowserRouter>
          </AuthProvider>
        </ThemeProvider>
      </WebSocketProvider>
    </AppProvider>
  )
}

export default App
