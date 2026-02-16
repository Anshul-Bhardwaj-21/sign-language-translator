import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Video, Plus, LogIn as LoginIcon, Clock, Users, Settings,
  LogOut, User, Calendar, TrendingUp, Award, Bell, Search
} from 'lucide-react';
import { api } from '../services/api';

interface UserInfo {
  email: string;
  name: string;
  id: string;
  isGuest?: boolean;
}

interface RecentMeeting {
  id: string;
  roomCode: string;
  date: string;
  duration: string;
  participants: number;
}

export default function HomePage() {
  const navigate = useNavigate();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [roomCode, setRoomCode] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState('');
  const [recentMeetings] = useState<RecentMeeting[]>([
    {
      id: '1',
      roomCode: 'ABC123',
      date: 'Today, 2:30 PM',
      duration: '45 min',
      participants: 5
    },
    {
      id: '2',
      roomCode: 'XYZ789',
      date: 'Yesterday, 10:00 AM',
      duration: '1h 20min',
      participants: 3
    }
  ]);

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (!userStr) {
      navigate('/');
      return;
    }
    setUser(JSON.parse(userStr));
  }, [navigate]);

  const handleCreateRoom = async () => {
    setIsCreating(true);
    setError('');
    
    try {
      const userId = user?.id || 'user_' + Math.random().toString(36).substr(2, 9);
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

  const handleLogout = () => {
    localStorage.removeItem('user');
    navigate('/');
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Header */}
      <header className="bg-black/20 backdrop-blur-xl border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Video className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold text-white">SignMeet</span>
            </div>

            {/* Search */}
            <div className="hidden md:flex flex-1 max-w-md mx-8">
              <div className="relative w-full">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search meetings..."
                  className="w-full pl-10 pr-4 py-2 bg-white/10 text-white rounded-lg border border-white/20 focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>

            {/* User Menu */}
            <div className="flex items-center gap-4">
              <button className="relative p-2 text-gray-300 hover:text-white transition-colors">
                <Bell className="w-6 h-6" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
              
              <div className="flex items-center gap-3 px-4 py-2 bg-white/10 rounded-lg">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-white" />
                </div>
                <div className="hidden md:block">
                  <div className="text-white text-sm font-medium">{user.name}</div>
                  <div className="text-gray-400 text-xs">{user.isGuest ? 'Guest' : 'Premium'}</div>
                </div>
              </div>

              <button
                onClick={handleLogout}
                className="p-2 text-gray-300 hover:text-white transition-colors"
                title="Logout"
              >
                <LogOut className="w-6 h-6" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            Welcome back, {user.name}! 👋
          </h1>
          <p className="text-gray-300">
            Start a new meeting or join an existing one
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {/* Create Meeting Card */}
          <div className="bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl p-8 shadow-2xl">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  Start New Meeting
                </h2>
                <p className="text-blue-100">
                  Create an instant meeting room
                </p>
              </div>
              <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                <Plus className="w-6 h-6 text-white" />
              </div>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg">
                <p className="text-red-200 text-sm">{error}</p>
              </div>
            )}

            <button
              onClick={handleCreateRoom}
              disabled={isCreating}
              className="w-full py-4 bg-white text-blue-600 font-semibold rounded-xl hover:bg-gray-100 transition-all shadow-lg disabled:opacity-50"
            >
              {isCreating ? 'Creating...' : 'Create Meeting'}
            </button>
          </div>

          {/* Join Meeting Card */}
          <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-8 shadow-2xl border border-white/20">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  Join Meeting
                </h2>
                <p className="text-gray-300">
                  Enter a meeting code to join
                </p>
              </div>
              <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center">
                <LoginIcon className="w-6 h-6 text-white" />
              </div>
            </div>

            <div className="space-y-4">
              <input
                type="text"
                value={roomCode}
                onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
                onKeyPress={(e) => e.key === 'Enter' && handleJoinRoom()}
                placeholder="Enter room code"
                className="w-full px-4 py-3 bg-black/30 text-white rounded-xl border border-white/20 focus:border-blue-500 focus:outline-none text-center text-lg font-mono"
                maxLength={8}
              />
              
              <button
                onClick={handleJoinRoom}
                className="w-full py-4 bg-white/10 text-white font-semibold rounded-xl hover:bg-white/20 transition-all border border-white/20"
              >
                Join Now
              </button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white/10 backdrop-blur-xl rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between mb-2">
              <Clock className="w-8 h-8 text-blue-400" />
              <TrendingUp className="w-5 h-5 text-green-400" />
            </div>
            <div className="text-3xl font-bold text-white mb-1">24</div>
            <div className="text-gray-400 text-sm">Total Meetings</div>
          </div>

          <div className="bg-white/10 backdrop-blur-xl rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between mb-2">
              <Users className="w-8 h-8 text-purple-400" />
              <TrendingUp className="w-5 h-5 text-green-400" />
            </div>
            <div className="text-3xl font-bold text-white mb-1">156</div>
            <div className="text-gray-400 text-sm">Participants</div>
          </div>

          <div className="bg-white/10 backdrop-blur-xl rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between mb-2">
              <Calendar className="w-8 h-8 text-green-400" />
              <TrendingUp className="w-5 h-5 text-green-400" />
            </div>
            <div className="text-3xl font-bold text-white mb-1">48h</div>
            <div className="text-gray-400 text-sm">Meeting Time</div>
          </div>

          <div className="bg-white/10 backdrop-blur-xl rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between mb-2">
              <Award className="w-8 h-8 text-yellow-400" />
              <TrendingUp className="w-5 h-5 text-green-400" />
            </div>
            <div className="text-3xl font-bold text-white mb-1">98%</div>
            <div className="text-gray-400 text-sm">Satisfaction</div>
          </div>
        </div>

        {/* Recent Meetings */}
        <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">Recent Meetings</h2>
            <button className="text-blue-400 hover:text-blue-300 text-sm font-medium">
              View All
            </button>
          </div>

          <div className="space-y-3">
            {recentMeetings.map((meeting) => (
              <div
                key={meeting.id}
                className="flex items-center justify-between p-4 bg-white/5 rounded-xl hover:bg-white/10 transition-all cursor-pointer"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <Video className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <div className="text-white font-medium">Room {meeting.roomCode}</div>
                    <div className="text-gray-400 text-sm">{meeting.date}</div>
                  </div>
                </div>
                <div className="flex items-center gap-6 text-sm">
                  <div className="text-gray-400">
                    <Clock className="w-4 h-4 inline mr-1" />
                    {meeting.duration}
                  </div>
                  <div className="text-gray-400">
                    <Users className="w-4 h-4 inline mr-1" />
                    {meeting.participants}
                  </div>
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                    Rejoin
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
