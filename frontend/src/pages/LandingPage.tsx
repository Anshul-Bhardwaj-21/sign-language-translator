import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

export default function LandingPage() {
  const navigate = useNavigate();
  const [roomCode, setRoomCode] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState('');

  const handleCreateRoom = async () => {
    setIsCreating(true);
    setError('');
    
    try {
      const userId = 'user_' + Math.random().toString(36).substr(2, 9);
      const result = await api.createRoom(userId, false);
      navigate(`/lobby/${result.room_code}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create room');
    } finally {
      setIsCreating(false);
    }
  };

  const handleJoinRoom = () => {
    if (!roomCode.trim()) {
      setError('Please enter a room code');
      return;
    }
    navigate(`/lobby/${roomCode.trim().toUpperCase()}`);
  };

  return (
    <div className="min-h-screen bg-meet-dark flex items-center justify-center p-8">
      <div className="max-w-md w-full">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">
            🧏 Sign Language Video Call
          </h1>
          <p className="text-gray-400 text-lg">
            Accessible video meetings with real-time sign language recognition
          </p>
        </div>

        <div className="bg-meet-gray rounded-lg p-8 shadow-2xl">
          {error && (
            <div className="mb-6 p-4 bg-red-900 border border-red-700 rounded-lg">
              <p className="text-red-200 text-sm">{error}</p>
            </div>
          )}

          <button
            onClick={handleCreateRoom}
            disabled={isCreating}
            className="w-full px-6 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed mb-6"
          >
            {isCreating ? 'Creating Room...' : '➕ Create New Room'}
          </button>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-600"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-meet-gray text-gray-400">OR</span>
            </div>
          </div>

          <div className="space-y-4">
            <input
              type="text"
              value={roomCode}
              onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
              onKeyPress={(e) => e.key === 'Enter' && handleJoinRoom()}
              placeholder="Enter room code"
              className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none text-center text-lg font-mono"
              maxLength={8}
            />
            
            <button
              onClick={handleJoinRoom}
              className="w-full px-6 py-3 bg-gray-700 text-white font-semibold rounded-lg hover:bg-gray-600 transition-colors"
            >
              Join Room
            </button>
          </div>
        </div>

        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>✓ No account required</p>
          <p>✓ End-to-end encrypted</p>
          <p>✓ Accessibility first</p>
        </div>
      </div>
    </div>
  );
}
