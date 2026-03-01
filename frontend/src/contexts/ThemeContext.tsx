import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface ThemeContextType {
  theme: 'dark' | 'light';
  toggleTheme: () => void;
  accessibilityMode: boolean;
  toggleAccessibility: () => void;
  fontSize: 'normal' | 'large' | 'extra-large';
  setFontSize: (size: 'normal' | 'large' | 'extra-large') => void;
  highContrast: boolean;
  toggleHighContrast: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    return (localStorage.getItem('theme') as 'dark' | 'light') || 'dark';
  });

  const [accessibilityMode, setAccessibilityMode] = useState(() => {
    return localStorage.getItem('accessibilityMode') === 'true';
  });

  const [fontSize, setFontSize] = useState<'normal' | 'large' | 'extra-large'>(() => {
    return (localStorage.getItem('fontSize') as any) || 'normal';
  });

  const [highContrast, setHighContrast] = useState(() => {
    return localStorage.getItem('highContrast') === 'true';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-font-size', fontSize);
    document.documentElement.setAttribute('data-high-contrast', String(highContrast));
    document.documentElement.setAttribute('data-accessibility', String(accessibilityMode));
  }, [theme, fontSize, highContrast, accessibilityMode]);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
  };

  const toggleAccessibility = () => {
    const newMode = !accessibilityMode;
    setAccessibilityMode(newMode);
    localStorage.setItem('accessibilityMode', String(newMode));
  };

  const handleSetFontSize = (size: 'normal' | 'large' | 'extra-large') => {
    setFontSize(size);
    localStorage.setItem('fontSize', size);
  };

  const toggleHighContrast = () => {
    const newContrast = !highContrast;
    setHighContrast(newContrast);
    localStorage.setItem('highContrast', String(newContrast));
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        toggleTheme,
        accessibilityMode,
        toggleAccessibility,
        fontSize,
        setFontSize: handleSetFontSize,
        highContrast,
        toggleHighContrast,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
