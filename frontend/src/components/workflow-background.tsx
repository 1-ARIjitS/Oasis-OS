"use client";

import { useEffect, useState } from "react";

interface Particle {
  id: number;
  left: number;
  top: number;
  width: number;
  height: number;
  animationDelay: number;
  animationDuration: number;
}

export function WorkflowBackground() {
  const [particles, setParticles] = useState<Particle[]>([]);

  useEffect(() => {
    // Generate particles on client side only to avoid hydration mismatch
    const newParticles: Particle[] = [];
    
    // Use a deterministic seed based on a fixed value
    const seed = 42;
    let random = seed;
    
    // Simple deterministic random number generator
    const getRandom = () => {
      random = (random * 1103515245 + 12345) & 0x7fffffff;
      return random / 0x7fffffff;
    };
    
    for (let i = 0; i < 20; i++) {
      newParticles.push({
        id: i,
        left: getRandom() * 100,
        top: getRandom() * 100,
        width: getRandom() * 4 + 2,
        height: getRandom() * 4 + 2,
        animationDelay: getRandom() * 10,
        animationDuration: getRandom() * 20 + 15,
      });
    }
    
    setParticles(newParticles);
  }, []);

  // Don't render anything on server side to avoid hydration mismatch
  if (typeof window === 'undefined') {
    return null;
  }

  return (
    <div className="fixed inset-0 overflow-hidden -z-10 pointer-events-none">
      {particles.map((particle) => (
        <div
          key={particle.id}
          className="absolute rounded-full bg-blue-500/10 dark:bg-blue-400/10 animate-float"
          style={{
            left: `${particle.left}%`,
            top: `${particle.top}%`,
            width: `${particle.width}px`,
            height: `${particle.height}px`,
            animationDelay: `${particle.animationDelay}s`,
            animationDuration: `${particle.animationDuration}s`,
          }}
        />
      ))}
    </div>
  );
} 