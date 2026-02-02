import React from 'react';
import { motion } from 'framer-motion';

interface HeroSectionProps {
  onExplore: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onExplore }) => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  return (
    <div className="relative w-full h-screen overflow-hidden bg-black text-white selection:bg-brand-500/30">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-dark-900" />
      
      {/* Abstract Orb Illusion - Center */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80vh] h-[80vh] opacity-80 pointer-events-none animate-pulse-slow">
         {/* Deep Glow */}
         <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-brand-900/40 via-indigo-900/20 to-transparent blur-[100px]" />
         
         {/* Structural Gradient */}
         <div className="absolute top-[10%] left-[10%] w-[80%] h-[80%] rounded-full bg-gradient-to-br from-white/5 to-transparent blur-[80px]" />
         
         {/* Rim Light */}
         <div className="absolute inset-0 rounded-full border border-brand-500/10 shadow-[0_0_120px_rgba(56,189,248,0.05)]" />
      </div>

      {/* Grain Overlay */}
      <div className="absolute inset-0 bg-noise opacity-[0.04] pointer-events-none mix-blend-overlay" />

      {/* Main Content */}
      <div className="relative z-10 h-full flex flex-col items-center justify-center px-4 sm:px-6">
        <div className="max-w-6xl mx-auto text-center space-y-12">
          <motion.h1 
            className="text-5xl md:text-7xl lg:text-8xl font-display font-medium leading-[0.95] tracking-tight text-transparent bg-clip-text bg-gradient-to-b from-white via-white/90 to-white/40"
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
          >
            Will your credit decision <br />
            <span className="text-white/30">create opportunity</span> <br />
            <span className="italic font-light text-brand-200/80">— or risk?</span>
          </motion.h1>

          <motion.p 
            className="text-lg md:text-xl text-slate-400 font-light tracking-wide max-w-xl mx-auto"
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2, ease: 'easeOut' }}
          >
            AI-powered intelligence for smarter lending decisions.
          </motion.p>

          <motion.div 
            className="pt-4"
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4, ease: 'easeOut' }}
          >
            <motion.button 
              onClick={onExplore}
              className="group relative px-10 py-5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 backdrop-blur-md transition-all duration-300 ease-out hover:border-brand-500/30 overflow-hidden"
              whileHover={prefersReducedMotion ? {} : { scale: 1.02 }}
              whileTap={prefersReducedMotion ? {} : { scale: 0.98 }}
              transition={{ duration: 0.15 }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
              <span className="relative flex items-center gap-4 text-sm font-medium tracking-widest uppercase text-white/90 group-hover:text-white">
                Explore Credit Intelligence
                <svg className="w-4 h-4 text-brand-400 transform group-hover:translate-x-1 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </span>
            </motion.button>
          </motion.div>
        </div>
      </div>

      {/* Decorative Bottom Fade */}
      <div className="absolute bottom-0 left-0 w-full h-40 bg-gradient-to-t from-dark-900 via-dark-900/50 to-transparent pointer-events-none z-20" />
    </div>
  );
};