import React, { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';

export const CreditSmartWordReveal: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Track scroll progress of this specific section
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"]
  });

  // Split the word into letters
  const word = "CreditSmart";
  const letters = word.split('');

  // Create animation values for each letter based on scroll progress
  const getLetterAnimations = (index: number, total: number) => {
    // Calculate individual progress range for each letter
    const start = index / total * 0.25; // Start staggered
    const end = start + 0.35; // Animation duration in scroll range

    const opacity = useTransform(
      scrollYProgress,
      [start, end],
      [0, 1]
    );

    // VERY subtle blur (2px max as per requirements)
    const blur = useTransform(
      scrollYProgress,
      [start, end],
      [2, 0]
    );

    const scale = useTransform(
      scrollYProgress,
      [start, end],
      [0.97, 1]
    );

    // Varied offset directions, max ±60px
    const directions = [
      { x: -40, y: -30 },
      { x: 50, y: 20 },
      { x: -60, y: 10 },
      { x: 30, y: -40 },
      { x: -50, y: 30 },
      { x: 60, y: -20 },
      { x: -30, y: 40 },
      { x: 45, y: -35 },
      { x: -55, y: 25 },
      { x: 35, y: -25 },
      { x: -45, y: 35 },
    ];

    const offset = directions[index % directions.length];

    const x = useTransform(
      scrollYProgress,
      [start, end],
      [offset.x, 0]
    );

    const y = useTransform(
      scrollYProgress,
      [start, end],
      [offset.y, 0]
    );

    return { opacity, blur, scale, x, y };
  };

  return (
    <section 
      ref={containerRef}
      className="relative w-full bg-black text-white flex items-center justify-center overflow-hidden"
      style={{ minHeight: '90vh' }}
    >
      {/* Clean dark background - no gradients or distractions */}
      <div className="absolute inset-0 bg-black" />
      
      {/* Ultra-minimal grain texture */}
      <div className="absolute inset-0 bg-noise opacity-[0.015] pointer-events-none mix-blend-overlay" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex justify-center items-center">
          <div className="relative">
            {/* The word assembled letter by letter */}
            <div className="flex justify-center items-center">
              {letters.map((letter, index) => {
                const { opacity, blur, scale, x, y } = getLetterAnimations(index, letters.length);
                
                // Determine if this letter is part of "Credit" or "Smart"
                const isCredit = index < 6;

                return (
                  <motion.span
                    key={index}
                    style={{
                      opacity,
                      filter: `blur(${blur.get() || 0}px)`,
                      scale,
                      x,
                      y,
                    }}
                    className={`inline-block text-6xl md:text-8xl lg:text-9xl font-sans font-light tracking-tight ${
                      isCredit 
                        ? 'text-white' 
                        : 'text-brand-400'
                    }`}
                  >
                    {letter}
                  </motion.span>
                );
              })}
            </div>
          </div>
        </div>

        {/* Clean tagline - no excessive animation */}
        <motion.div
          style={{
            opacity: useTransform(scrollYProgress, [0.6, 0.85], [0, 1]),
          }}
          className="text-center mt-16"
        >
          <p className="text-base md:text-lg text-slate-500 font-light tracking-wide">
            AI-powered intelligence for credit decisions
          </p>
        </motion.div>
      </div>
    </section>
  );
};
