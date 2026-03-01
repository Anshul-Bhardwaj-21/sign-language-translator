import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Video, Plus, LogIn, Calendar, Clock, Users, Eye, LogOut, Moon, Sun, Shield } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { generateMeetingCode, formatDate } from '../utils/meetingUtils';
import demoData from '../data/demo.json';

interface Meeting {
  id: string;
  code: string;
  name: string;
  date: string;
  duration: string;
  participants: number;
}

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [roomCode, setRoomCode] = useState('');

  // Redirect admin to admin dashboard
  useEffect(() => {
    if (user?.isAdmin) {
      navigate('/admin');
    }
  }, [user, navigate]);

  // Load user stats from demo data
  const userStats = demoData.users.find(u => u.email === user?.email);
  const stats = {
    totalMeetings: userStats?.stats.totalMeetings || 0,
    totalTime: userStats?.stats.totalTime || '0h 0m',
    activeParticipants: 24,
    accessibilityUsage: '35%',
  };

  // Load user's meetings from demo data
  const recentMeetings: Meeting[] = demoData.meetings
    .filter(m => m.hostId === user?.id || m.participants.some(p => p.id === user?.id))
    .slice(0, 5)
    .map(m => ({
      id: m.id,
      code: m.code,
      name: m.name,
      date: formatDate(m.date),
      duration: m.duration,
      participants: m.participants.length,
    }));

  const handleCreateMeeting = () => {
    const code = generateMeetingCode();
    navigate(`/lobby?room=${code}`);
  };

  const handleJoinMeeting = () => {
    if (roomCode.trim()) {
      navigate(`/lobby?room=${roomCode.trim()}`);
      setShowJoinModal(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-600 rounded-lg">
                <Video className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">VideoCall</h1>
            </div>

            {/* User Profile & Actions */}
            <div className="flex items-center gap-4">
              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                aria-label="Toggle theme"
              >
                {theme === 'dark' ? (
                  <Sun className="w-5 h-5 text-yellow-500" />
                ) : (
                  <Moon className="w-5 h-5 text-gray-700" />
                )}
              </button>

              {/* User Info */}
              <div className="flex items-center gap-3 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold">
                  {user?.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                    {user?.name}
                    {user?.isAdmin && <Shield className="w-4 h-4 text-yellow-500" />}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {user?.isGuest ? 'Guest' : user?.email}
                  </p>
                </div>
              </div>

              {/* Logout */}
              <button
                onClick={handleLogout}
                className="p-2 rounded-lg bg-red-100 dark:bg-red-900/30 hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
                aria-label="Logout"
              >
                <LogOut className="w-5 h-5 text-red-600 dark:text-red-400" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Welcome back, {user?.name}! 👋
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Ready to start your next meeting?
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Video className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mb-1">{stats.totalMeetings}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Meetings</p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <Clock className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mb-1">{stats.totalTime}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Time</p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Users className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mb-1">{stats.activeParticipants}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Active Participants</p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                <Eye className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mb-1">{stats.accessibilityUsage}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Accessibility Usage</p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-8">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={handleCreateMeeting}
              className="flex items-center gap-3 p-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <Plus className="w-6 h-6" />
              <div className="text-left">
                <p className="font-semibold">Create New Meeting</p>
                <p className="text-sm text-blue-100">Start an instant meeting</p>
              </div>
            </button>

            <button
              onClick={() => setShowJoinModal(true)}
              className="flex items-center gap-3 p-4 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
            >
              <LogIn className="w-6 h-6" />
              <div className="text-left">
                <p className="font-semibold">Join Meeting</p>
                <p className="text-sm text-green-100">Enter a room code</p>
              </div>
            </button>

            <button
              disabled
              className="flex items-center gap-3 p-4 bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded-lg cursor-not-allowed"
            >
              <Calendar className="w-6 h-6" />
              <div className="text-left">
                <p className="font-semibold">Schedule Meeting</p>
                <p className="text-sm">Coming soon</p>
              </div>
            </button>
          </div>
        </div>

        {/* Recent Meetings */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Recent Meetings</h3>
          <div className="space-y-4">
            {recentMeetings.map((meeting) => (
              <div
                key={meeting.id}
                className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                    <Video className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">{meeting.name}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Code: {meeting.code} • {meeting.date} • {meeting.duration} • {meeting.participants} participants
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => navigate(`/lobby?room=${meeting.code}`)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-semibold"
                >
                  Rejoin
                </button>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Join Meeting Modal */}
      {showJoinModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-md w-full p-6">
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Join Meeting</h3>
            <input
              type="text"
              placeholder="Enter room code"
              value={roomCode}
              onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
              className="w-full px-4 py-3 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
            />
            <div className="flex gap-3">
              <button
                onClick={() => setShowJoinModal(false)}
                className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleJoinMeeting}
                disabled={!roomCode.trim()}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Join
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;
