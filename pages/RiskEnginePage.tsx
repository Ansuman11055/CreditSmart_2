// CreditSmart Phase 3E/4 integration - Risk Engine Page
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Layout } from '../components/Layout';
import { View } from '../types';
import { usePrediction } from '../src/hooks/usePrediction';
import { useCurrency } from '../src/context/CurrencyContext';
import { convertFromUSD, convertToUSD } from '../src/utils/currency';
import { sanitizeNumberInput } from '../src/utils/formValidation';

// Phase 4C UX Stability Fix - String-based form state
interface FormState {
  annualIncome: string;
  monthlyDebt: string;
  creditScore: string;
  loanAmount: string;
  employmentYears: string;
}

export const RiskEnginePage: React.FC = () => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const [{ prediction, loading, error }, { runPrediction }] = usePrediction();
  const { currency } = useCurrency();

  const [formData, setFormData] = useState<FormState>({
    annualIncome: '75000',
    monthlyDebt: '1200',
    creditScore: '720',
    loanAmount: '25000',
    employmentYears: '5'
  });
  const [validationError, setValidationError] = useState<string | null>(null);

  // Phase 4C UX Stability Fix - NO parsing during typing
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    if (validationError) {
      setValidationError(null);
    }
  };

  // Phase 4C UX Stability Fix - Parse and validate on submission only
  const handleAnalyze = async () => {
    const annualIncomeNum = sanitizeNumberInput(formData.annualIncome);
    const monthlyDebtNum = sanitizeNumberInput(formData.monthlyDebt);
    const creditScoreNum = sanitizeNumberInput(formData.creditScore);
    const loanAmountNum = sanitizeNumberInput(formData.loanAmount);
    const employmentYearsNum = sanitizeNumberInput(formData.employmentYears);

    if (annualIncomeNum === null || annualIncomeNum <= 0) {
      setValidationError('Please enter a valid annual income');
      return;
    }
    if (monthlyDebtNum === null || monthlyDebtNum < 0) {
      setValidationError('Please enter a valid monthly debt amount');
      return;
    }
    if (creditScoreNum === null || creditScoreNum < 300 || creditScoreNum > 850) {
      setValidationError('Credit score must be between 300 and 850');
      return;
    }
    if (loanAmountNum === null || loanAmountNum <= 0) {
      setValidationError('Please enter a valid loan amount');
      return;
    }
    if (employmentYearsNum === null || employmentYearsNum < 0) {
      setValidationError('Please enter valid employment years');
      return;
    }

    const annualIncomeUSD = convertToUSD(annualIncomeNum, currency);
    const monthlyDebtUSD = convertToUSD(monthlyDebtNum, currency);
    const loanAmountUSD = convertToUSD(loanAmountNum, currency);

    await runPrediction({
      annualIncome: annualIncomeUSD,
      monthlyDebt: monthlyDebtUSD,
      creditScore: creditScoreNum,
      loanAmount: loanAmountUSD,
      employmentYears: employmentYearsNum
    });
  };

  const getRiskColor = (band: string) => {
    switch (band) {
      case 'low': return 'text-green-400 bg-green-500/10 border-green-500/30';
      case 'medium': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
      case 'high': return 'text-red-400 bg-red-500/10 border-red-500/30';
      default: return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
    }
  };

  return (
    <Layout currentView={View.LANDING} onViewChange={() => {}}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Header */}
        <motion.div
          className="text-center mb-12"
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-5xl font-display font-bold mb-4">
            Risk<span className="text-brand-400"> Engine</span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            Live credit risk assessment powered by production ML models
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Form */}
          <motion.div
            className="glass-panel p-8 rounded-xl"
            initial={prefersReducedMotion ? {} : { opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <h2 className="text-2xl font-bold text-white mb-6">Applicant Profile</h2>
            
            {/* Phase 4C UX Stability Fix - Validation error display */}
            {validationError && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                <p className="text-sm text-red-400">{validationError}</p>
              </div>
            )}
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">
                  Annual Income ({currency})
                </label>
                <input
                  type="text"
                  inputMode="decimal"
                  name="annualIncome"
                  value={formData.annualIncome}
                  onChange={handleInputChange}
                  placeholder="e.g., 75000"
                  className="w-full bg-dark-800 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">
                  Monthly Debt ({currency})
                </label>
                <input
                  type="text"
                  inputMode="decimal"
                  name="monthlyDebt"
                  value={formData.monthlyDebt}
                  onChange={handleInputChange}
                  placeholder="e.g., 1200"
                  className="w-full bg-dark-800 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">
                  Credit Score
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  name="creditScore"
                  value={formData.creditScore}
                  onChange={handleInputChange}
                  placeholder="e.g., 720"
                  className="w-full bg-dark-800 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">
                  Loan Amount ({currency})
                </label>
                <input
                  type="text"
                  inputMode="decimal"
                  name="loanAmount"
                  value={formData.loanAmount}
                  onChange={handleInputChange}
                  placeholder="e.g., 25000"
                  className="w-full bg-dark-800 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">
                  Employment Years
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  name="employmentYears"
                  value={formData.employmentYears}
                  onChange={handleInputChange}
                  placeholder="e.g., 5"
                  className="w-full bg-dark-800 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <button
                onClick={handleAnalyze}
                disabled={loading}
                className="w-full mt-6 bg-brand-600 hover:bg-brand-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg transition-colors"
              >
                {loading ? 'Analyzing...' : 'Run Risk Assessment'}
              </button>
            </div>
          </motion.div>

          {/* Results Panel */}
          <motion.div
            className="space-y-6"
            initial={prefersReducedMotion ? {} : { opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            {loading ? (
              <div className="glass-panel p-12 rounded-xl text-center">
                <div className="inline-block w-12 h-12 border-4 border-slate-700 border-t-brand-500 rounded-full animate-spin mb-4" />
                <h3 className="text-lg font-medium text-slate-400">Processing risk assessment...</h3>
              </div>
            ) : error ? (
              <div className="glass-panel p-12 rounded-xl text-center">
                <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 className="text-lg font-medium text-red-400 mb-2">Assessment Failed</h3>
                <p className="text-sm text-slate-500">{error}</p>
              </div>
            ) : prediction ? (
              <>
                {/* Risk Score */}
                <div className="glass-panel p-8 rounded-xl">
                  <h3 className="text-lg font-medium text-slate-400 mb-4">Risk Score</h3>
                  <div className="flex items-baseline gap-2 mb-2">
                    <span className="text-6xl font-bold text-white">{prediction.risk_score}</span>
                    <span className="text-2xl text-slate-500">/100</span>
                  </div>
                  <div className={`inline-block px-4 py-2 rounded-lg border ${getRiskColor(prediction.risk_band)}`}>
                    <span className="font-semibold uppercase text-sm">{prediction.risk_band} Risk</span>
                  </div>
                </div>

                {/* Decision */}
                <div className="glass-panel p-8 rounded-xl">
                  <h3 className="text-lg font-medium text-slate-400 mb-4">Decision</h3>
                  <p className="text-white text-lg leading-relaxed">{prediction.recommendation}</p>
                  <div className="mt-4 pt-4 border-t border-white/10">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-500">Confidence</span>
                      <span className="text-sm font-semibold text-brand-400 uppercase">{prediction.confidence}</span>
                    </div>
                  </div>
                </div>

                {/* Top Risk Factors */}
                <div className="glass-panel p-8 rounded-xl">
                  <h3 className="text-lg font-medium text-slate-400 mb-4">Key Risk Factors</h3>
                  <div className="space-y-3">
                    {prediction.top_features.slice(0, 3).map((feature, idx) => (
                      <div key={idx} className="flex items-start gap-3">
                        <div className={`mt-1 w-2 h-2 rounded-full ${feature.impact === 'positive' ? 'bg-green-400' : 'bg-red-400'}`} />
                        <div className="flex-1">
                          <div className="font-medium text-white">{feature.name}</div>
                          <div className="text-sm text-slate-500">{feature.reason}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="glass-panel p-12 rounded-xl text-center">
                <svg className="w-16 h-16 text-slate-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <h3 className="text-lg font-medium text-slate-400 mb-2">Ready to Analyze</h3>
                <p className="text-sm text-slate-500">Enter applicant data and run assessment</p>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </Layout>
  );
};
