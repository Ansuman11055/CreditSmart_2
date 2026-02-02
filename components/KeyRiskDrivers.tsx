import React from 'react';

interface RiskFeature {
  name: string;
  impact: "positive" | "negative";
  reason: string;
}

interface KeyRiskDriversProps {
  features: RiskFeature[];
}

export const KeyRiskDrivers: React.FC<KeyRiskDriversProps> = ({ features }) => {
  return (
    <div className="glass-panel p-6 rounded-xl">
      <h3 className="text-sm font-medium text-slate-300 uppercase tracking-wide mb-4">
        Key Risk Drivers
      </h3>
      
      <div className="space-y-4">
        {features.map((feature, index) => (
          <div 
            key={index}
            className="flex items-start gap-4 p-4 rounded-lg bg-white/[0.02] border border-white/5 hover:border-white/10 transition-colors"
          >
            {/* Impact Icon */}
            <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${
              feature.impact === "positive" 
                ? "bg-emerald-500/10 text-emerald-400" 
                : "bg-rose-500/10 text-rose-400"
            }`}>
              {feature.impact === "positive" ? (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                </svg>
              )}
            </div>

            {/* Feature Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="text-sm font-medium text-white">
                  {feature.name}
                </h4>
                <span className={`text-xs ${
                  feature.impact === "positive" 
                    ? "text-emerald-400" 
                    : "text-rose-400"
                }`}>
                  {feature.impact === "positive" ? "↓ Reduced risk" : "↑ Increased risk"}
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                {feature.reason}
              </p>
            </div>
          </div>
        ))}
      </div>

      <p className="text-xs text-slate-500 mt-4 italic">
        These are the top 3 features influencing this prediction
      </p>
    </div>
  );
};
