import { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface GradientHeadingProps {
  children: ReactNode;
  level?: 1 | 2 | 3 | 4;
  className?: string;
  animate?: boolean;
}

export const GradientHeading = ({
  children,
  level = 1,
  className = '',
  animate = false,
}: GradientHeadingProps) => {
  const sizes = {
    1: 'text-5xl md:text-6xl font-bold',
    2: 'text-4xl md:text-5xl font-bold',
    3: 'text-3xl md:text-4xl font-semibold',
    4: 'text-2xl md:text-3xl font-semibold',
  };

  const baseClasses = `
    bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400
    bg-clip-text text-transparent
    ${sizes[level]}
    ${className}
  `;

  const animationProps = animate
    ? {
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.6 },
      }
    : {};

  switch (level) {
    case 1:
      return (
        <motion.h1 className={baseClasses} {...animationProps}>
          {children}
        </motion.h1>
      );
    case 2:
      return (
        <motion.h2 className={baseClasses} {...animationProps}>
          {children}
        </motion.h2>
      );
    case 3:
      return (
        <motion.h3 className={baseClasses} {...animationProps}>
          {children}
        </motion.h3>
      );
    case 4:
      return (
        <motion.h4 className={baseClasses} {...animationProps}>
          {children}
        </motion.h4>
      );
    default:
      return (
        <motion.h1 className={baseClasses} {...animationProps}>
          {children}
        </motion.h1>
      );
  }
};

