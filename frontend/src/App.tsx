import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppProvider } from './contexts/AppContext'
import { WebSocketProvider } from './contexts/WebSocketContext'
import { MeetingProvider } from './contexts/MeetingContext'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import ErrorBoundary from './components/ErrorBoundary'
import BackendHealthCheck from './components/BackendHealthCheck'
import LandingPageNew from './pages/LandingPageNew'
import DashboardNew from './pages/DashboardNew'
import LoginPage from './pages/LoginPage'
import AdminDashboard from './pages/AdminDashboard'
import PreJoinLobby from './pages/PreJoinLobby'
import VideoCallPage from './pages/VideoCallPage'
import MeetingRoom from './pages/MeetingRoom'

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
    <ErrorBoundary>
      <AppProvider>
        <WebSocketProvider>
          <MeetingProvider>
            <ThemeProvider>
              <AuthProvider>
                <BackendHealthCheck />
                <BrowserRouter>
                  <Routes>
                    <Route path="/" element={<LandingPageNew />} />
                    <Route path="/login" element={<LoginPage />} />
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
                      path="/lobby/:roomCode"
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
                    <Route
                      path="/meeting/:roomCode"
                      element={
                        <ProtectedRoute>
                          <MeetingRoom />
                        </ProtectedRoute>
                      }
                    />
                  </Routes>
                </BrowserRouter>
              </AuthProvider>
            </ThemeProvider>
          </MeetingProvider>
        </WebSocketProvider>
      </AppProvider>
    </ErrorBoundary>
  )
}

export default App
