import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext'
import LoginPage from './pages/LoginPage'
import HomePage from './pages/HomePage'
import PreJoinLobby from './pages/PreJoinLobby'
import VideoCallPageComplete from './pages/VideoCallPageComplete'

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const user = localStorage.getItem('user');
  return user ? <>{children}</> : <Navigate to="/" replace />;
}

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/home" element={
            <ProtectedRoute>
              <HomePage />
            </ProtectedRoute>
          } />
          <Route path="/lobby/:roomCode" element={
            <ProtectedRoute>
              <PreJoinLobby />
            </ProtectedRoute>
          } />
          <Route path="/call/:roomCode" element={
            <ProtectedRoute>
              <VideoCallPageComplete />
            </ProtectedRoute>
          } />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
