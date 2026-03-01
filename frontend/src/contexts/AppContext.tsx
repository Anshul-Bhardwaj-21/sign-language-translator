import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type Theme = 'dark' | 'light';
export type AIStatus = 'connected' | 'mock' | 'disconnected' | 'error';

interface User {
  id: string;
  name: string;
  avatar?: string;
}

interface AppState {
  theme: Theme;
  user: User | null;
  aiStatus: AIStatus;
  totalWordsRecognized: number;
  isInCall: boolean;
  connectionStrength: number; // 0-100
}

interface AppContextType extends AppState {
  setTheme: (theme: Theme) => void;
  setUser: (user: User | null) => void;
  setAIStatus: (status: AIStatus) => void;
  incrementWordsRecognized: () => void;
  setIsInCall: (inCall: boolean) => void;
  setConnectionStrength: (strength: number) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>('dark');
  const [user, setUser] = useState<User | null>(null);
  const [aiStatus, setAIStatus] = useState<AIStatus>('mock');
  const [totalWordsRecognized, setTotalWordsRecognized] = useState(0);
  const [isInCall, setIsInCall] = useState(false);
  const [connectionStrength, setConnectionStrength] = useState(100);

  // Load theme from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as Theme;
    if (savedTheme) {
      setTheme(savedTheme);
    }
  }, []);

  // Apply theme to document
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('theme', theme);
  }, [theme]);

  const incrementWordsRecognized = () => {
    setTotalWordsRecognized(prev => prev + 1);
  };

  const value: AppContextType = {
    theme,
    user,
    aiStatus,
    totalWordsRecognized,
    isInCall,
    connectionStrength,
    setTheme,
    setUser,
    setAIStatus,
    incrementWordsRecognized,
    setIsInCall,
    setConnectionStrength,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useApp = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};
