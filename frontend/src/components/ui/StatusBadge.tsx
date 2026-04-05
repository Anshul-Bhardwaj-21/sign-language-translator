import React from 'react';
import { motion } from 'framer-motion';

interface StatusBadgeProps {
  status: 'online' | 'offline' | 'warning' | 'error';
  label: string;
  pulse?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label, pulse = false }) => {
  const colors = {
    online: 'bg-green-500/20 text-green-400 border-green-500/50',
    offline: 'bg-gray-500/20 text-gray-400 border-gray-500/50',
    warning: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
    error: 'bg-red-500/20 text-red-400 border-red-500/50',
  };

  const dotColors = {
    online: 'bg-green-500',
    offline: 'bg-gray-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500',
  };

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border ${colors[status]}`}>
      <motion.div
        className={`w-2 h-2 rounded-full ${dotColors[status]}`}
        animate={pulse ? { scale: [1, 1.2, 1], opacity: [1, 0.7, 1] } : undefined}
        transition={pulse ? { duration: 2, repeat: Infinity } : undefined}
      />
      <span className="text-sm font-medium">{label}</span>
    </div>
  );
};
