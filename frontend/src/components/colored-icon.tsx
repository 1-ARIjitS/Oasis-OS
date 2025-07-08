"use client";

import { motion } from "motion/react";
import { ReactNode } from "react";

interface ColoredIconProps {
  children: ReactNode;
  color: string;
  glowColor: string;
  className?: string;
}

export function ColoredIcon({ children, color, glowColor, className = "" }: ColoredIconProps) {
  return (
    <motion.div
      className={`relative w-16 h-16 rounded-2xl flex items-center justify-center ${className}`}
      style={{
        background: `linear-gradient(135deg, ${color}20, ${color}10)`,
        border: `1px solid ${color}30`,
        backdropFilter: 'blur(10px)',
        WebkitBackdropFilter: 'blur(10px)',
        boxShadow: `0 8px 32px ${color}20, inset 0 1px 0 ${color}40`,
      }}
      whileHover={{
        scale: 1.05,
        boxShadow: `0 12px 40px ${color}30, inset 0 1px 0 ${color}50`,
      }}
      animate={{
        boxShadow: [
          `0 8px 32px ${color}20, inset 0 1px 0 ${color}40`,
          `0 10px 36px ${color}25, inset 0 1px 0 ${color}45`,
          `0 8px 32px ${color}20, inset 0 1px 0 ${color}40`,
        ],
      }}
      transition={{
        duration: 3,
        repeat: Infinity,
        ease: "easeInOut",
      }}
    >
      {/* Animated background orb */}
      <motion.div
        className="absolute inset-2 rounded-xl opacity-20"
        style={{
          background: `radial-gradient(circle, ${glowColor}, transparent 70%)`,
        }}
        animate={{
          scale: [1, 1.1, 1],
          opacity: [0.2, 0.4, 0.2],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      
      {/* Icon container */}
      <motion.div
        className="relative z-10 text-2xl"
        style={{ color }}
        animate={{
          scale: [1, 1.05, 1],
        }}
        transition={{
          duration: 2.5,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >
        {children}
      </motion.div>
      
      {/* Shimmer effect */}
      <motion.div
        className="absolute inset-0 rounded-2xl"
        style={{
          background: `linear-gradient(45deg, transparent 30%, ${color}10 50%, transparent 70%)`,
        }}
        animate={{
          x: ['-100%', '100%'],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut",
          repeatDelay: 2,
        }}
      />
    </motion.div>
  );
} 