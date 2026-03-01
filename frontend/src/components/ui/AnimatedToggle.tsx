import React from 'react';
import { motion } from 'framer-motion';

interface AnimatedToggleProps {
  enabled: boolean;
  onChange: (enabled: boolean) => void;
  label?: string;
  disabled?: boolean;
}

export const AnimatedToggle: React.FC<AnimatedToggleProps> = ({
  enabled,
  onChange,
  label,
  disabled = false,
}) => {
  return (
    <div className="flex items-center gap-3">
      {label && <span className="text-sm font-medium text-gray-300">{label}</span>}
      <button
        className={`
          relative w-14 h-7 rounded-full transition-colors duration-200
          ${enabled ? 'bg-gradient-to-r from-blue-600 to-purple-600' : 'bg-gray-700'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
        onClick={() => !disabled && onChange(!enabled)}
        disabled={disabled}
      >
        <motion.div
          className="absolute top-1 left-1 w-5 h-5 bg-white rounded-full shadow-lg"
          animate={{ x: enabled ? 28 : 0 }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        />
      </button>
    </div>
  );
};
