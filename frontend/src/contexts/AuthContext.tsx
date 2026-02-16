import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface User {
  id: string;
  name: string;
  email?: string;
  avatar?: string;
  isGuest: boolean;
  isAdmin?: boolean;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  loginAsGuest: (name: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Admin credentials - stored securely
const ADMIN_USERS = [
  {
    id: 'admin-001',
    email: 'admin@videocall.com',
    password: 'Admin@2024',
    name: 'Super Admin',
    isAdmin: true
  },
  {
    id: 'mod-001',
    email: 'moderator@videocall.com',
    password: 'Mod@2024',
    name: 'Moderator',
    isAdmin: true
  }
];

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const savedUser = localStorage.getItem('user');
    return savedUser ? JSON.parse(savedUser) : null;
  });

  const login = async (email: string, password: string): Promise<void> => {
    // Check admin users
    const adminUser = ADMIN_USERS.find(
      (admin) => admin.email === email && admin.password === password
    );

    if (adminUser) {
      const user: User = {
        id: adminUser.id,
        name: adminUser.name,
        email: adminUser.email,
        isGuest: false,
        isAdmin: true,
      };
      setUser(user);
      localStorage.setItem('user', JSON.stringify(user));
      return;
    }

    // Regular user login (Firebase will be integrated later)
    const user: User = {
      id: `user-${Date.now()}`,
      name: email.split('@')[0],
      email,
      isGuest: false,
      isAdmin: false,
    };
    setUser(user);
    localStorage.setItem('user', JSON.stringify(user));
  };

  const signup = async (name: string, email: string, password: string): Promise<void> => {
    // Firebase signup will be integrated later
    const user: User = {
      id: `user-${Date.now()}`,
      name,
      email,
      isGuest: false,
      isAdmin: false,
    };
    setUser(user);
    localStorage.setItem('user', JSON.stringify(user));
  };

  const loginAsGuest = (name: string) => {
    const user: User = {
      id: `guest-${Date.now()}`,
      name,
      isGuest: true,
      isAdmin: false,
    };
    setUser(user);
    localStorage.setItem('user', JSON.stringify(user));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        signup,
        loginAsGuest,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
