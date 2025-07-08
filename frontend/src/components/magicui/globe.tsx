"use client";

import createGlobe, { COBEOptions } from "cobe";
import { useMotionValue, useSpring } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { useTheme } from "next-themes";

import { cn } from "@/lib/utils";

const MOVEMENT_DAMPING = 1400;

const GLOBE_CONFIG_LIGHT: COBEOptions = {
  width: 800,
  height: 800,
  onRender: () => {},
  devicePixelRatio: 2,
  phi: 0,
  theta: 0.3,
  dark: 0,
  diffuse: 0.8,
  mapSamples: 24000,
  mapBrightness: 1.8,
  baseColor: [0.9, 0.9, 0.95],
  markerColor: [79 / 255, 70 / 255, 229 / 255],
  glowColor: [0.8, 0.8, 1],
  markers: [
    { location: [40.7128, -74.006], size: 0.08 },
    { location: [51.5074, -0.1278], size: 0.06 },
    { location: [35.6762, 139.6503], size: 0.07 },
    { location: [37.7749, -122.4194], size: 0.06 },
    { location: [55.7558, 37.6176], size: 0.05 },
    { location: [28.6139, 77.2090], size: 0.06 },
    { location: [31.2304, 121.4737], size: 0.07 },
    { location: [-23.5505, -46.6333], size: 0.06 },
    { location: [52.5200, 13.4050], size: 0.05 },
    { location: [48.8566, 2.3522], size: 0.06 },
    { location: [-33.8688, 151.2093], size: 0.05 },
    { location: [1.3521, 103.8198], size: 0.04 },
  ],
};

const GLOBE_CONFIG_DARK: COBEOptions = {
  width: 800,
  height: 800,
  onRender: () => {},
  devicePixelRatio: 2,
  phi: 0,
  theta: 0.3,
  dark: 1,
  diffuse: 0.6,
  mapSamples: 24000,
  mapBrightness: 0.8,
  baseColor: [0.1, 0.1, 0.15],
  markerColor: [139 / 255, 92 / 255, 246 / 255],
  glowColor: [0.4, 0.3, 0.8],
  markers: [
    { location: [40.7128, -74.006], size: 0.08 },
    { location: [51.5074, -0.1278], size: 0.06 },
    { location: [35.6762, 139.6503], size: 0.07 },
    { location: [37.7749, -122.4194], size: 0.06 },
    { location: [55.7558, 37.6176], size: 0.05 },
    { location: [28.6139, 77.2090], size: 0.06 },
    { location: [31.2304, 121.4737], size: 0.07 },
    { location: [-23.5505, -46.6333], size: 0.06 },
    { location: [52.5200, 13.4050], size: 0.05 },
    { location: [48.8566, 2.3522], size: 0.06 },
    { location: [-33.8688, 151.2093], size: 0.05 },
    { location: [1.3521, 103.8198], size: 0.04 },
  ],
};

export function Globe({
  className,
  config,
}: {
  className?: string;
  config?: COBEOptions;
}) {
  let phi = 0;
  let width = 0;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pointerInteracting = useRef<number | null>(null);
  const pointerInteractionMovement = useRef(0);
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  const r = useMotionValue(0);
  const rs = useSpring(r, {
    mass: 1,
    damping: 30,
    stiffness: 100,
  });

  const updatePointerInteraction = (value: number | null) => {
    pointerInteracting.current = value;
    if (canvasRef.current) {
      canvasRef.current.style.cursor = value !== null ? "grabbing" : "grab";
    }
  };

  const updateMovement = (clientX: number) => {
    if (pointerInteracting.current !== null) {
      const delta = clientX - pointerInteracting.current;
      pointerInteractionMovement.current = delta;
      r.set(r.get() + delta / MOVEMENT_DAMPING);
    }
  };

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    
    const onResize = () => {
      if (canvasRef.current) {
        width = canvasRef.current.offsetWidth;
      }
    };

    window.addEventListener("resize", onResize);
    onResize();

    // Choose config based on theme
    const globeConfig = config || (theme === "dark" ? GLOBE_CONFIG_DARK : GLOBE_CONFIG_LIGHT);

    const globe = createGlobe(canvasRef.current!, {
      ...globeConfig,
      width: width * 2,
      height: width * 2,
      onRender: (state) => {
        if (!pointerInteracting.current) phi += 0.003;
        state.phi = phi + rs.get();
        state.width = width * 2;
        state.height = width * 2;
      },
    });

    // Smooth opacity transition
    setTimeout(() => {
      if (canvasRef.current) {
        canvasRef.current.style.opacity = "1";
      }
    }, 100);
    
    return () => {
      globe.destroy();
      window.removeEventListener("resize", onResize);
    };
  }, [rs, config, theme, mounted]);

  if (!mounted) {
    return (
      <div className={cn(
        "absolute inset-0 mx-auto aspect-[1/1] w-full max-w-[600px] flex items-center justify-center",
        className,
      )}>
        <div className="h-32 w-32 bg-muted/20 rounded-full animate-pulse" />
      </div>
    );
  }

  return (
    <div
      className={cn(
        "absolute inset-0 mx-auto aspect-[1/1] w-full max-w-[600px]",
        className,
      )}
    >
      <canvas
        className={cn(
          "size-full opacity-0 transition-opacity duration-700 [contain:layout_paint_size] drop-shadow-2xl",
        )}
        ref={canvasRef}
        onPointerDown={(e) => {
          pointerInteracting.current = e.clientX;
          updatePointerInteraction(e.clientX);
        }}
        onPointerUp={() => updatePointerInteraction(null)}
        onPointerOut={() => updatePointerInteraction(null)}
        onMouseMove={(e) => updateMovement(e.clientX)}
        onTouchMove={(e) =>
          e.touches[0] && updateMovement(e.touches[0].clientX)
        }
      />
    </div>
  );
}
