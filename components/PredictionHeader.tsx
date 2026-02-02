import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface PredictionHeaderProps {
  riskScore: number; // 0-100
  riskBand: "low" | "medium" | "high";
}

export const PredictionHeader: React.FC<PredictionHeaderProps> = ({ riskScore, riskBand }) => {
  const [animatedScore, setAnimatedScore] = useState(0);
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Animate score on first render
  useEffect(() => {
    if (prefersReducedMotion) {
      setAnimatedScore(riskScore);
      return;
    }

    const duration = 600; // ms
    const steps = 30;
    const increment = riskScore / steps;
    const stepDuration = duration / steps;

    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= riskScore) {
        setAnimatedScore(riskScore);
        clearInterval(timer);
      } else {
        setAnimatedScore(Math.floor(current));
      }
    }, stepDuration);

    return () => clearInterval(timer);
  }, [riskScore, prefersReducedMotion]);

  // Risk band colors and labels
  const bandConfig = {
    low: {
      label: "Low Risk",
      color: "text-emerald-400",
      bgColor: "bg-emerald-500/10",
      borderColor: "border-emerald-500/30"
    },
    medium: {
      label: "Medium Risk",
      color: "text-amber-400",
      bgColor: "bg-amber-500/10",
      borderColor: "border-amber-500/30"
    },
    high: {
      label: "High Risk",
      color: "text-rose-400",
      bgColor: "bg-rose-500/10",
      borderColor: "border-rose-500/30"
    }
  };

  const config = bandConfig[riskBand];
  
  // Calculate stroke dash offset for circular progress
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (animatedScore / 100) * circumference;

  return (
    <div className="glass-panel p-8 rounded-xl">
      <div className="flex items-center justify-between">
        {/* Left: Circular Progress */}
        <div className="relative">
          <svg className="transform -rotate-90" width="180" height="180">
            {/* Background circle */}
            <circle
              cx="90"
              cy="90"
              r={radius}
              stroke="currentColor"
              strokeWidth="8"
              fill="none"
              className="text-white/5"
            />
            {/* Progress circle */}
            <motion.circle
              cx="90"
              cy="90"
              r={radius}
              stroke="currentColor"
              strokeWidth="8"
              fill="none"
              strokeLinecap="round"
              className={config.color}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: prefersReducedMotion ? strokeDashoffset : strokeDashoffset }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
              style={{
                strokeDasharray: circumference,
                strokeDashoffset: strokeDashoffset
              }}
            />
          </svg>
          {/* Score in center */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-5xl font-display font-bold text-white">
              {animatedScore}
            </div>
            <div className="text-xs text-slate-500 uppercase tracking-wide mt-1">
              Risk Score
            </div>
          </div>
        </div>

        {/* Right: Risk Band */}
        <div className="flex-1 ml-12">
          <div className="space-y-4">
            <div>
              <div className="text-xs text-slate-500 uppercase tracking-wide mb-2">
                Risk Classification
              </div>
              <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${config.bgColor} border ${config.borderColor}`}>
                <div className={`w-2 h-2 rounded-full ${config.color.replace('text-', 'bg-')}`} />
                <span className={`text-lg font-medium ${config.color}`}>
                  {config.label}
                </span>
              </div>
            </div>
            <p className="text-sm text-slate-400 leading-relaxed max-w-md">
              {riskBand === "low" && "This profile demonstrates strong creditworthiness with minimal default risk indicators."}
              {riskBand === "medium" && "This profile shows moderate risk factors that warrant careful consideration."}
              {riskBand === "high" && "This profile exhibits elevated risk signals requiring additional scrutiny."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
