import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { GradientHeading } from '../components/ui/GradientHeading';
import { GlowButton } from '../components/ui/GlowButton';
import { GlassCard } from '../components/ui/GlassCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useApp } from '../contexts/AppContext';
import { 
  Video, 
  Users, 
  MessageSquare, 
  TrendingUp, 
  Clock,
  Zap,
  Activity
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';

export default function DashboardNew() {
  const navigate = useNavigate();
  const { aiStatus, totalWordsRecognized, isInCall } = useApp();
  const [animatedCount, setAnimatedCount] = useState(0);

  // Animated counter
  useEffect(() => {
    const duration = 1000;
    const steps = 60;
    const increment = totalWordsRecognized / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= totalWordsRecognized) {
        setAnimatedCount(totalWordsRecognized);
        clearInterval(timer);
      } else {
        setAnimatedCount(Math.floor(current));
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [totalWordsRecognized]);

  // Mock usage data
  const usageData = [
    { time: '00:00', words: 0 },
    { time: '04:00', words: 12 },
    { time: '08:00', words: 45 },
    { time: '12:00', words: 89 },
    { time: '16:00', words: 134 },
    { time: '20:00', words: totalWordsRecognized },
  ];

  const recentConversations = [
    { id: 1, name: 'Team Meeting', time: '2 hours ago', words: 234 },
    { id: 2, name: 'Client Call', time: '5 hours ago', words: 156 },
    { id: 3, name: 'Quick Chat', time: 'Yesterday', words: 89 },
  ];

  const handleStartCall = () => {
    navigate('/home');
  };

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <GradientHeading level={1} className="mb-2">
            Welcome to SignBridge
          </GradientHeading>
          <p className="text-gray-400 text-lg">
            Your real-time sign language communication platform
          </p>
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <GlassCard className="p-8 text-center">
            <Video className="w-16 h-16 mx-auto mb-4 text-blue-400" />
            <h2 className="text-2xl font-bold mb-2">Start a New Call</h2>
            <p className="text-gray-400 mb-6">
              Connect with others using real-time sign language interpretation
            </p>
            <GlowButton
              size="lg"
              onClick={handleStartCall}
              icon={<Video className="w-5 h-5" />}
            >
              Launch Video Call
            </GlowButton>
          </GlassCard>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* AI Status */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <GlassCard className="p-6">
              <div className="flex items-center justify-between mb-4">
                <Zap className="w-8 h-8 text-blue-400" />
                <StatusBadge
                  status={aiStatus === 'connected' ? 'online' : aiStatus === 'mock' ? 'warning' : 'error'}
                  label={aiStatus === 'connected' ? 'Connected' : aiStatus === 'mock' ? 'Mock Mode' : 'Offline'}
                  pulse
                />
              </div>
              <h3 className="text-lg font-semibold mb-1">AI Engine</h3>
              <p className="text-sm text-gray-400">
                {aiStatus === 'mock' ? 'Running in demo mode' : 'Real-time processing'}
              </p>
            </GlassCard>
          </motion.div>

          {/* Words Recognized */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <GlassCard className="p-6">
              <MessageSquare className="w-8 h-8 text-purple-400 mb-4" />
              <h3 className="text-lg font-semibold mb-1">Words Recognized</h3>
              <div className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                {animatedCount.toLocaleString()}
              </div>
            </GlassCard>
          </motion.div>

          {/* Active Call Status */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <GlassCard className="p-6">
              <div className="flex items-center justify-between mb-4">
                <Users className="w-8 h-8 text-green-400" />
                <StatusBadge
                  status={isInCall ? 'online' : 'offline'}
                  label={isInCall ? 'In Call' : 'Available'}
                  pulse={isInCall}
                />
              </div>
              <h3 className="text-lg font-semibold mb-1">Call Status</h3>
              <p className="text-sm text-gray-400">
                {isInCall ? 'Currently in a call' : 'Ready to connect'}
              </p>
            </GlassCard>
          </motion.div>

          {/* Session Time */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
          >
            <GlassCard className="p-6">
              <Clock className="w-8 h-8 text-orange-400 mb-4" />
              <h3 className="text-lg font-semibold mb-1">Session Time</h3>
              <div className="text-3xl font-bold bg-gradient-to-r from-orange-400 to-red-400 bg-clip-text text-transparent">
                2h 34m
              </div>
            </GlassCard>
          </motion.div>
        </div>

        {/* Usage Chart */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
        >
          <GlassCard className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <TrendingUp className="w-6 h-6 text-blue-400" />
              <h2 className="text-xl font-bold">Usage Analytics</h2>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={usageData}>
                <defs>
                  <linearGradient id="colorWords" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="words"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  fill="url(#colorWords)"
                  dot={{ fill: '#3b82f6', r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </GlassCard>
        </motion.div>

        {/* Recent Conversations */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
        >
          <GlassCard className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <Activity className="w-6 h-6 text-purple-400" />
              <h2 className="text-xl font-bold">Recent Conversations</h2>
            </div>
            <div className="space-y-4">
              {recentConversations.map((conv, index) => (
                <motion.div
                  key={conv.id}
                  className="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors cursor-pointer"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.4, delay: 0.8 + index * 0.1 }}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                      <Video className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="font-semibold">{conv.name}</h3>
                      <p className="text-sm text-gray-400">{conv.time}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-blue-400">{conv.words}</div>
                    <div className="text-xs text-gray-400">words</div>
                  </div>
                </motion.div>
              ))}
            </div>
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
}
