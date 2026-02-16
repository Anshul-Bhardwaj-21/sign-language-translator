import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import PreJoinLobby from './pages/PreJoinLobby'
import VideoCallPage from './pages/VideoCallPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/lobby/:roomCode" element={<PreJoinLobby />} />
        <Route path="/call/:roomCode" element={<VideoCallPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
