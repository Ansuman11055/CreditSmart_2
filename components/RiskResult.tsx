import React from 'react';
import { RiskAnalysis } from '../types';

interface RiskResultProps {
  analysis: RiskAnalysis | null;
  loading: boolean;
}

export const RiskResult: React.FC<RiskResultProps> = ({ analysis, loading }) => {
  if (loading) {
    return (
      <div className="glass-panel p-8 rounded-xl min-h-[400px] flex flex-col items-center justify-center text-center">
        <div className="w-16 h-16 mb-6 rounded-full border-2 border-brand-500 border-t-transparent animate-spin"></div>
        <h3 className="text-xl font-display font-medium text-white mb-2">Analyzing Financial Vectors</h3>
        <p className="text-slate-400 max-w-sm">
          Gemini 2.5 is processing income stability, debt ratios, and credit history...
        </p>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="glass-panel p-8 rounded-xl min-h-[400px] flex flex-col items-center justify-center text-center border-dashed border-2 border-white/10">
        <div className="w-16 h-16 mb-4 rounded-full bg-white/5 flex items-center justify-center text-slate-500">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-white">No Analysis Generated</h3>
        <p className="text-slate-400 text-sm mt-1">Submit the applicant profile to generate a risk report.</p>
      </div>
    );
  }

  const getRiskColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'low': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      case 'medium': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
      case 'high': return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
      case 'critical': return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
      default: return 'text-slate-400 bg-slate-500/10';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 800) return '#34d399'; // Emerald 400
    if (score >= 700) return '#38bdf8'; // Sky 400
    if (score >= 600) return '#fbbf24'; // Amber 400
    return '#f43f5e'; // Rose 400
  };

  return (
    <div className="glass-panel rounded-xl overflow-hidden animate-fade-in">
      <div className="p-6 border-b border-white/5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h3 className="text-xl font-display font-bold text-white">Risk Assessment Report</h3>
          <p className="text-sm text-slate-400">Generated via Gemini 3.0 Flash</p>
        </div>
        <div className={`px-4 py-1.5 rounded-full border text-sm font-bold tracking-wide uppercase ${getRiskColor(analysis.riskLevel)}`}>
          {analysis.riskLevel} Risk
        </div>
      </div>

      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Score Radial */}
        <div className="flex flex-col items-center justify-center p-4 bg-white/5 rounded-lg border border-white/5">
           <div className="relative w-32 h-32 flex items-center justify-center mb-4">
             <svg className="w-full h-full transform -rotate-90">
               <circle
                 cx="64"
                 cy="64"
                 r="56"
                 stroke="currentColor"
                 strokeWidth="8"
                 fill="transparent"
                 className="text-slate-700/50"
               />
               <circle
                 cx="64"
                 cy="64"
                 r="56"
                 stroke={getScoreColor(analysis.score)}
                 strokeWidth="8"
                 fill="transparent"
                 strokeDasharray={351.86}
                 strokeDashoffset={351.86 - (351.86 * analysis.score) / 1000}
                 className="transition-all duration-1000 ease-out"
               />
             </svg>
             <div className="absolute inset-0 flex flex-col items-center justify-center">
               <span className="text-3xl font-bold text-white">{analysis.score}</span>
               <span className="text-xs text-slate-400 uppercase">Score</span>
             </div>
           </div>
           <p className="text-sm text-slate-400 text-center">
             Proprietary CreditSmart Score™ based on ML predictive modeling.
           </p>
        </div>

        {/* Key Factors */}
        <div>
          <h4 className="text-sm font-medium text-slate-300 mb-3 uppercase tracking-wide">Key Risk Factors</h4>
          <ul className="space-y-2">
            {analysis.factors.map((factor, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-slate-300">
                <svg className="w-5 h-5 text-brand-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                {factor}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="p-6 bg-white/5 border-t border-white/5">
        <h4 className="text-sm font-medium text-slate-300 mb-2 uppercase tracking-wide">Executive Summary</h4>
        <p className="text-slate-300 leading-relaxed text-sm mb-4">
          {analysis.summary}
        </p>
        
        <div className="bg-brand-500/10 border-l-4 border-brand-500 p-4 rounded-r-lg">
          <h5 className="text-brand-400 font-bold text-sm mb-1 uppercase">Recommendation</h5>
          <p className="text-white font-medium">{analysis.recommendation}</p>
        </div>
      </div>
    </div>
  );
};