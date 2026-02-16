import { Sun, Moon, Volume2, Type, Contrast, X } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

interface AccessibilityMenuProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AccessibilityMenu({ isOpen, onClose }: AccessibilityMenuProps) {
  const {
    theme,
    toggleTheme,
    accessibilityMode,
    toggleAccessibility,
    fontSize,
    setFontSize,
    highContrast,
    toggleHighContrast
  } = useTheme();

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
        onClick={onClose}
      />

      {/* Menu Panel */}
      <div className="fixed right-0 top-0 h-full w-80 bg-white dark:bg-gray-900 shadow-2xl z-50 overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Accessibility
            </h2>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <X className="w-6 h-6 text-gray-600 dark:text-gray-400" />
            </button>
          </div>

          {/* Theme Toggle */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Theme
            </label>
            <div className="flex gap-2">
              <button
                onClick={toggleTheme}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border-2 transition-all ${
                  theme === 'light'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                    : 'border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-gray-400 dark:hover:border-gray-600'
                }`}
              >
                <Sun className="w-5 h-5" />
                <span className="font-medium">Light</span>
              </button>
              <button
                onClick={toggleTheme}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border-2 transition-all ${
                  theme === 'dark'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                    : 'border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-gray-400 dark:hover:border-gray-600'
                }`}
              >
                <Moon className="w-5 h-5" />
                <span className="font-medium">Dark</span>
              </button>
            </div>
          </div>

          {/* Accessibility Mode */}
          <div className="mb-6">
            <label className="flex items-center justify-between p-4 rounded-lg border-2 border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600 transition-all cursor-pointer">
              <div className="flex items-center gap-3">
                <Volume2 className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                <div>
                  <div className="font-medium text-gray-900 dark:text-white">
                    Sign Language Mode
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Enable sign language recognition
                  </div>
                </div>
              </div>
              <input
                type="checkbox"
                checked={accessibilityMode}
                onChange={toggleAccessibility}
                className="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
              />
            </label>
          </div>

          {/* Font Size */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              <Type className="w-4 h-4 inline mr-2" />
              Font Size
            </label>
            <div className="space-y-2">
              {(['normal', 'large', 'xlarge'] as const).map((size) => (
                <button
                  key={size}
                  onClick={() => setFontSize(size)}
                  className={`w-full px-4 py-3 rounded-lg border-2 text-left transition-all ${
                    fontSize === size
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                      : 'border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-gray-400 dark:hover:border-gray-600'
                  }`}
                >
                  <span className={`font-medium ${
                    size === 'normal' ? 'text-base' :
                    size === 'large' ? 'text-lg' :
                    'text-xl'
                  }`}>
                    {size === 'normal' ? 'Normal' :
                     size === 'large' ? 'Large' :
                     'Extra Large'}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* High Contrast */}
          <div className="mb-6">
            <label className="flex items-center justify-between p-4 rounded-lg border-2 border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600 transition-all cursor-pointer">
              <div className="flex items-center gap-3">
                <Contrast className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
                <div>
                  <div className="font-medium text-gray-900 dark:text-white">
                    High Contrast
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Increase color contrast
                  </div>
                </div>
              </div>
              <input
                type="checkbox"
                checked={highContrast}
                onChange={toggleHighContrast}
                className="w-5 h-5 text-yellow-600 rounded focus:ring-2 focus:ring-yellow-500"
              />
            </label>
          </div>

          {/* Info */}
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-blue-800 dark:text-blue-300">
              💡 These settings apply across all pages and persist between sessions.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
