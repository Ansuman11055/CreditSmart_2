import React, { useState } from 'react';
import { FinancialProfile, RiskAnalysis } from '../types';
import { analyzeRisk } from '../services/geminiService';
import { RiskResult } from './RiskResult';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const INITIAL_PROFILE: FinancialProfile = {
  annualIncome: 85000,
  monthlyDebt: 1200,
  creditScore: 720,
  loanAmount: 25000,
  employmentYears: 5
};

export const Dashboard: React.FC = () => {
  const [profile, setProfile] = useState<FinancialProfile>(INITIAL_PROFILE);
  const [analysis, setAnalysis] = useState<RiskAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setProfile(prev => ({
      ...prev,
      [name]: parseFloat(value) || 0
    }));
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyzeRisk(profile);
      setAnalysis(result);
    } catch (err) {
      setError("Failed to analyze risk. Please check your API key.");
    } finally {
      setLoading(false);
    }
  };

  // Mock data for chart visualization
  const chartData = [
    { name: 'Income', value: profile.annualIncome / 1000, color: '#38bdf8' },
    { name: 'Debt (Ann)', value: (profile.monthlyDebt * 12) / 1000, color: '#f43f5e' },
    { name: 'Loan', value: profile.loanAmount / 1000, color: '#fbbf24' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-10">
        <h2 className="text-3xl font-display font-bold text-white mb-2">Risk Analysis Console</h2>
        <p className="text-slate-400">Enter applicant financial data for real-time Gemini-powered assessment.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Input Form */}
        <div className="lg:col-span-4 space-y-6">
          <div className="glass-panel p-6 rounded-xl">
            <h3 className="text-lg font-medium text-white mb-6 flex items-center gap-2">
              <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Applicant Data
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1 uppercase tracking-wide">Annual Income ($)</label>
                <input
                  type="number"
                  name="annualIncome"
                  value={profile.annualIncome}
                  onChange={handleInputChange}
                  className="w-full bg-dark-800 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1 uppercase tracking-wide">Monthly Debt ($)</label>
                <input
                  type="number"
                  name="monthlyDebt"
                  value={profile.monthlyDebt}
                  onChange={handleInputChange}
                  className="w-full bg-dark-800 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1 uppercase tracking-wide">Credit Score</label>
                <input
                  type="number"
                  name="creditScore"
                  value={profile.creditScore}
                  onChange={handleInputChange}
                  className="w-full bg-dark-800 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1 uppercase tracking-wide">Loan Amount ($)</label>
                <input
                  type="number"
                  name="loanAmount"
                  value={profile.loanAmount}
                  onChange={handleInputChange}
                  className="w-full bg-dark-800 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1 uppercase tracking-wide">Employment (Years)</label>
                <input
                  type="number"
                  name="employmentYears"
                  value={profile.employmentYears}
                  onChange={handleInputChange}
                  className="w-full bg-dark-800 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                />
              </div>

              <button
                onClick={handleAnalyze}
                disabled={loading}
                className="w-full mt-6 bg-brand-600 hover:bg-brand-500 disabled:bg-brand-900 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg shadow-lg shadow-brand-500/20 transition-all duration-200 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing
                  </>
                ) : (
                  'Run Analysis'
                )}
              </button>
              {error && <p className="text-red-400 text-sm text-center mt-2">{error}</p>}
            </div>
          </div>
        </div>

        {/* Results Area */}
        <div className="lg:col-span-8 space-y-6">
          {/* Quick Stats Chart */}
          <div className="glass-panel p-6 rounded-xl">
            <h4 className="text-sm font-medium text-slate-400 mb-4 uppercase tracking-wide">Financial Overview (k)</h4>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <XAxis 
                    dataKey="name" 
                    stroke="#64748b" 
                    fontSize={12} 
                    tickLine={false} 
                    axisLine={false}
                  />
                  <YAxis 
                    stroke="#64748b" 
                    fontSize={12} 
                    tickLine={false} 
                    axisLine={false}
                    tickFormatter={(value) => `$${value}k`}
                  />
                  <Tooltip 
                    cursor={{fill: 'rgba(255,255,255,0.05)'}}
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc' }}
                  />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* AI Result Component */}
          <RiskResult analysis={analysis} loading={loading} />
        </div>
      </div>
    </div>
  );
};