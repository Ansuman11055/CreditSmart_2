import React from 'react';

interface ModelConfidenceProps {
  confidence: "low" | "medium" | "high";
}

export const ModelConfidence: React.FC<ModelConfidenceProps> = ({ confidence }) => {
  const confidenceConfig = {
    low: {
      label: "Low Confidence",
      width: "33%",
      color: "bg-slate-500",
      textColor: "text-slate-400"
    },
    medium: {
      label: "Medium Confidence",
      width: "66%",
      color: "bg-brand-500",
      textColor: "text-brand-400"
    },
    high: {
      label: "High Confidence",
      width: "100%",
      color: "bg-emerald-500",
      textColor: "text-emerald-400"
    }
  };

  const config = confidenceConfig[confidence];

  return (
    <div className="glass-panel p-6 rounded-xl">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-slate-300 uppercase tracking-wide">
          Model Confidence
        </h3>
        <div className="group relative">
          <svg className="w-4 h-4 text-slate-500 cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {/* Tooltip */}
          <div className="absolute bottom-full right-0 mb-2 w-64 p-3 bg-dark-800 border border-white/10 rounded-lg text-xs text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
            Based on data quality and model certainty
          </div>
        </div>
      </div>

      {/* Confidence Meter */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className={`text-sm font-medium ${config.textColor}`}>
            {config.label}
          </span>
        </div>
        <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
          <div 
            className={`h-full ${config.color} rounded-full transition-all duration-500 ease-out`}
            style={{ width: config.width }}
          />
        </div>
      </div>
    </div>
  );
};
