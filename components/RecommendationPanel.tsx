import React from 'react';

interface RecommendationPanelProps {
  recommendation: string;
  riskBand: "low" | "medium" | "high";
}

export const RecommendationPanel: React.FC<RecommendationPanelProps> = ({ recommendation, riskBand }) => {
  // Icon and styling based on risk band
  const config = {
    low: {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      bgColor: "bg-emerald-500/5",
      borderColor: "border-emerald-500/20",
      iconColor: "text-emerald-400"
    },
    medium: {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      ),
      bgColor: "bg-amber-500/5",
      borderColor: "border-amber-500/20",
      iconColor: "text-amber-400"
    },
    high: {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      bgColor: "bg-rose-500/5",
      borderColor: "border-rose-500/20",
      iconColor: "text-rose-400"
    }
  };

  const bandConfig = config[riskBand];

  return (
    <div className={`glass-panel p-6 rounded-xl border-2 ${bandConfig.borderColor} ${bandConfig.bgColor}`}>
      <div className="flex items-start gap-4">
        <div className={`flex-shrink-0 ${bandConfig.iconColor}`}>
          {bandConfig.icon}
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-medium text-slate-300 uppercase tracking-wide mb-2">
            Recommended Action
          </h3>
          <p className="text-base font-medium text-white leading-relaxed">
            {recommendation}
          </p>
        </div>
      </div>
    </div>
  );
};
