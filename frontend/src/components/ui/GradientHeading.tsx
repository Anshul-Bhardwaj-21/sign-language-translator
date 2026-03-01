import React, { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface GradientHeadingProps {
  children: ReactNode;
  level?: 1 | 2 | 3 | 4;
  className?: string;
  animate?: boolean;
}

export const GradientHeading: React.FC<GradientHeadingProps> = ({
  children,
  level = 1,
  className = '',
  animate = false,
}) => {
  const sizes = {
    1: 'text-5xl md:text-6xl font-bold',
    2: 'text-4xl md:text-5xl font-bold',
    3: 'text-3xl md:text-4xl font-semibold',
    4: 'text-2xl md:text-3xl font-semibold',
  };

  const Component = motion[`h${level}` as keyof typeof motion];

  return (
    <Component
      className={`
        bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400
        bg-clip-text text-transparent
        ${sizes[level]}
        ${className}
      `}
      initial={animate ? { opacity: 0, y: 20 } : undefined}
      animate={animate ? { opacity: 1, y: 0 } : undefined}
      transition={animate ? { duration: 0.6 } : undefined}
    >
      {children}
    </Component>
  );
};
