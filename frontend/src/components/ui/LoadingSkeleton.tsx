import React from 'react';
import { motion } from 'framer-motion';

interface LoadingSkeletonProps {
  width?: string;
  height?: string;
  className?: string;
  circle?: boolean;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  width = 'w-full',
  height = 'h-4',
  className = '',
  circle = false,
}) => {
  return (
    <motion.div
      className={`
        bg-gradient-to-r from-gray-800 via-gray-700 to-gray-800
        ${circle ? 'rounded-full' : 'rounded-lg'}
        ${width} ${height}
        ${className}
      `}
      animate={{
        backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
      }}
      transition={{
        duration: 2,
        repeat: Infinity,
        ease: 'linear',
      }}
      style={{
        backgroundSize: '200% 100%',
      }}
    />
  );
};

export const LoadingSpinner: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({ size = 'md' }) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <motion.div
      className={`${sizes[size]} border-4 border-blue-500/30 border-t-blue-500 rounded-full`}
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
    />
  );
};
