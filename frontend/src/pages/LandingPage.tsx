import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Video, Users, Shield, Zap, Moon, Sun } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 dark:from-gray-900 dark:via-blue-900 dark:to-purple-900 relative overflow-hidden">
      {/* Animated background blobs */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000"></div>
      </div>

      {/* Theme toggle */}
      <button
        onClick={toggleTheme}
        className="absolute top-6 right-6 p-3 rounded-full bg-white/10 backdrop-blur-md hover:bg-white/20 transition-all z-10"
        aria-label="Toggle theme"
      >
        {theme === 'dark' ? (
          <Sun className="w-6 h-6 text-yellow-300" />
        ) : (
          <Moon className="w-6 h-6 text-blue-900" />
        )}
      </button>

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 text-center">
        {/* Logo */}
        <div className="mb-8 p-6 rounded-full bg-white/10 backdrop-blur-md">
          <Video className="w-16 h-16 text-white" />
        </div>

        {/* Title */}
        <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 animate-fade-in">
          Welcome to VideoCall
        </h1>
        <p className="text-xl md:text-2xl text-white/90 mb-12 max-w-2xl animate-fade-in-delay">
          Professional video meetings with sign language support, secure moderation, and luxury design
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 mb-16 animate-fade-in-delay-2">
          <button
            onClick={() => navigate('/login')}
            className="px-8 py-4 bg-white text-blue-600 rounded-full font-semibold text-lg hover:bg-blue-50 transform hover:scale-105 transition-all shadow-xl"
          >
            Get Started
          </button>
          <button
            onClick={() => navigate('/login')}
            className="px-8 py-4 bg-white/10 backdrop-blur-md text-white rounded-full font-semibold text-lg hover:bg-white/20 transform hover:scale-105 transition-all border-2 border-white/30"
          >
            Sign In
          </button>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl animate-fade-in-delay-3">
          <div className="p-6 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 hover:bg-white/15 transition-all">
            <Users className="w-12 h-12 text-white mb-4 mx-auto" />
            <h3 className="text-xl font-semibold text-white mb-2">Multi-Participant</h3>
            <p className="text-white/80">Host meetings with multiple participants and grid layout</p>
          </div>
          <div className="p-6 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 hover:bg-white/15 transition-all">
            <Shield className="w-12 h-12 text-white mb-4 mx-auto" />
            <h3 className="text-xl font-semibold text-white mb-2">Secure & Moderated</h3>
            <p className="text-white/80">Admin controls to prevent raids and ensure safe meetings</p>
          </div>
          <div className="p-6 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 hover:bg-white/15 transition-all">
            <Zap className="w-12 h-12 text-white mb-4 mx-auto" />
            <h3 className="text-xl font-semibold text-white mb-2">Sign Language Support</h3>
            <p className="text-white/80">Real-time sign language recognition and captions</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
