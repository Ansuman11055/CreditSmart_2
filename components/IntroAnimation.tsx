import React from 'react';
import { motion } from 'framer-motion';

export const IntroAnimation: React.FC = () => {
  // Container animation
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.4,
        delayChildren: 0.2,
      },
    },
  };

  // Individual item animation - subtle upward motion
  const itemVariants = {
    hidden: { 
      opacity: 0, 
      y: 20,
      scale: 0.98,
    },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        duration: 0.8,
        ease: [0.25, 0.46, 0.45, 0.94] as const, // Custom ease for premium feel
      },
    },
  };

  // Headline animation - even more subtle
  const headlineVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 1,
        ease: [0.25, 0.1, 0.25, 1] as const, // easeOut as cubic-bezier array
      },
    },
  };

  const steps = [
    {
      title: 'Signals',
      description: 'Real-time data aggregation',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
    },
    {
      title: 'Intelligence',
      description: 'ML-powered risk analysis',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      ),
    },
    {
      title: 'Decisions',
      description: 'Confident credit outcomes',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
  ];

  return (
    <section className="relative w-full bg-black text-white py-32 overflow-hidden">
      {/* Subtle background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-black via-dark-900/50 to-black pointer-events-none" />
      
      {/* Minimal grain texture */}
      <div className="absolute inset-0 bg-noise opacity-[0.02] pointer-events-none mix-blend-overlay" />

      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6">
        {/* Headline */}
        <motion.div
          variants={headlineVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="text-center mb-20"
        >
          <h2 className="text-3xl md:text-4xl font-display font-light tracking-tight text-white/90">
            How CreditSmart <span className="text-brand-400 font-normal">Thinks</span>
          </h2>
        </motion.div>

        {/* Animated Steps */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12"
        >
          {steps.map((step, index) => (
            <motion.div
              key={step.title}
              variants={itemVariants}
              className="relative group"
            >
              {/* Connection line (desktop only, not on last item) */}
              {index < steps.length - 1 && (
                <div className="hidden md:block absolute top-8 left-full w-12 h-px bg-gradient-to-r from-white/20 to-transparent" />
              )}

              {/* Card */}
              <div className="relative p-8 rounded-2xl bg-white/[0.02] border border-white/5 backdrop-blur-sm transition-all duration-500 hover:bg-white/[0.04] hover:border-white/10">
                {/* Icon */}
                <div className="mb-6 w-12 h-12 rounded-xl bg-gradient-to-br from-brand-500/10 to-brand-600/5 border border-brand-400/20 flex items-center justify-center text-brand-400 group-hover:border-brand-400/40 transition-colors duration-500">
                  {step.icon}
                </div>

                {/* Title */}
                <h3 className="text-xl font-display font-medium text-white mb-2">
                  {step.title}
                </h3>

                {/* Description */}
                <p className="text-sm text-slate-400 font-light leading-relaxed">
                  {step.description}
                </p>

                {/* Subtle number indicator */}
                <div className="absolute top-4 right-4 text-5xl font-display font-light text-white/[0.03] pointer-events-none">
                  {index + 1}
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};
