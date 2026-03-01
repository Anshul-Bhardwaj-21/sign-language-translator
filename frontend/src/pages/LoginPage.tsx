import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Video, Mail, Lock, User, Moon, Sun, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, signup, loginAsGuest } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);

  const validateEmail = (email: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const validatePassword = (password: string) => {
    return password.length >= 8 && /[A-Z]/.test(password) && /[0-9]/.test(password);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setIsLoading(true);

    try {
      if (mode === 'signup') {
        // Validate signup
        const newErrors: Record<string, string> = {};
        if (!formData.name || formData.name.length < 2) {
          newErrors.name = 'Name must be at least 2 characters';
        }
        if (!validateEmail(formData.email)) {
          newErrors.email = 'Invalid email format';
        }
        if (!validatePassword(formData.password)) {
          newErrors.password = 'Password must be 8+ chars with uppercase and number';
        }
        if (formData.password !== formData.confirmPassword) {
          newErrors.confirmPassword = 'Passwords do not match';
        }

        if (Object.keys(newErrors).length > 0) {
          setErrors(newErrors);
          setIsLoading(false);
          return;
        }

        await signup(formData.name, formData.email, formData.password);
      } else {
        // Validate login
        if (!validateEmail(formData.email)) {
          setErrors({ email: 'Invalid email format' });
          setIsLoading(false);
          return;
        }
        if (!formData.password) {
          setErrors({ password: 'Password is required' });
          setIsLoading(false);
          return;
        }

        await login(formData.email, formData.password);
      }

      navigate('/dashboard');
    } catch (error) {
      setErrors({ general: 'Authentication failed. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGuestLogin = () => {
    const guestName = prompt('Enter your name:');
    if (guestName && guestName.trim()) {
      loginAsGuest(guestName.trim());
      navigate('/dashboard');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 dark:from-gray-900 dark:via-blue-900 dark:to-purple-900 relative overflow-hidden flex items-center justify-center p-4">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
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

      {/* Login Card */}
      <div className="relative z-10 w-full max-w-md">
        <div className="bg-white/10 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-8">
          {/* Logo */}
          <div className="flex justify-center mb-6">
            <div className="p-4 rounded-full bg-white/10">
              <Video className="w-12 h-12 text-white" />
            </div>
          </div>

          <h2 className="text-3xl font-bold text-white text-center mb-2">
            {mode === 'login' ? 'Welcome Back' : 'Create Account'}
          </h2>
          <p className="text-white/70 text-center mb-8">
            {mode === 'login' ? 'Sign in to continue' : 'Sign up to get started'}
          </p>

          {/* Tab Switcher */}
          <div className="flex gap-2 mb-6 p-1 bg-white/10 rounded-full">
            <button
              onClick={() => setMode('login')}
              className={`flex-1 py-2 rounded-full font-semibold transition-all ${
                mode === 'login'
                  ? 'bg-white text-blue-600'
                  : 'text-white hover:bg-white/10'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setMode('signup')}
              className={`flex-1 py-2 rounded-full font-semibold transition-all ${
                mode === 'signup'
                  ? 'bg-white text-blue-600'
                  : 'text-white hover:bg-white/10'
              }`}
            >
              Sign Up
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'signup' && (
              <div>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/50" />
                  <input
                    type="text"
                    placeholder="Full Name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full pl-12 pr-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/50"
                  />
                </div>
                {errors.name && <p className="text-red-300 text-sm mt-1">{errors.name}</p>}
              </div>
            )}

            <div>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/50" />
                <input
                  type="email"
                  placeholder="Email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full pl-12 pr-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/50"
                />
              </div>
              {errors.email && <p className="text-red-300 text-sm mt-1">{errors.email}</p>}
            </div>

            <div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/50" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full pl-12 pr-12 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/50"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-white/50 hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.password && <p className="text-red-300 text-sm mt-1">{errors.password}</p>}
            </div>

            {mode === 'signup' && (
              <div>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/50" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Confirm Password"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    className="w-full pl-12 pr-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/50"
                  />
                </div>
                {errors.confirmPassword && <p className="text-red-300 text-sm mt-1">{errors.confirmPassword}</p>}
              </div>
            )}

            {errors.general && (
              <p className="text-red-300 text-sm text-center">{errors.general}</p>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-white text-blue-600 rounded-xl font-semibold hover:bg-blue-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          {/* Guest Login */}
          <div className="mt-6 text-center">
            <button
              onClick={handleGuestLogin}
              className="text-white/80 hover:text-white underline text-sm"
            >
              Continue as Guest
            </button>
          </div>

          {/* Admin Info */}
          <div className="mt-6 p-4 bg-white/5 rounded-xl border border-white/10">
            <p className="text-white/60 text-xs text-center">
              Admin: admin@videocall.com / Admin@2024<br />
              Moderator: moderator@videocall.com / Mod@2024
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
