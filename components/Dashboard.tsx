import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { FinancialProfile } from '../types';
import { usePrediction } from '../src/hooks/usePrediction';
import { useCurrency } from '../src/context/CurrencyContext';
import { formatCurrency, convertToUSD, convertFromUSD } from '../src/utils/currency';
import { sanitizeNumberInput } from '../src/utils/formValidation';
import { PredictionHeader } from './PredictionHeader';
import { ModelConfidence } from './ModelConfidence';
import { KeyRiskDrivers } from './KeyRiskDrivers';
import { RecommendationPanel } from './RecommendationPanel';

// Phase 4C UX Stability Fix - String-based form state to prevent input reset
interface FormState {
  annualIncome: string;
  monthlyDebt: string;
  creditScore: string;
  loanAmount: string;
  employmentYears: string;
}

const INITIAL_FORM: FormState = {
  annualIncome: '85000',
  monthlyDebt: '1200',
  creditScore: '720',
  loanAmount: '25000',
  employmentYears: '5'
};

export const Dashboard: React.FC = () => {
  const [formData, setFormData] = useState<FormState>(INITIAL_FORM);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [{ prediction, loading, error }, { runPrediction }] = usePrediction();
  const { currency } = useCurrency();
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Phase 4C UX Stability Fix - NO parsing during typing, preserve raw input
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    
    // Store raw string value, allowing intermediate states like "12." or ""
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear validation error when user starts typing
    if (validationError) {
      setValidationError(null);
    }
  };

  // Phase 4C UX Stability Fix - Parse and validate ONLY on submission
  const handleAnalyze = async () => {
    // Parse all string inputs to numbers
    const annualIncomeNum = sanitizeNumberInput(formData.annualIncome);
    const monthlyDebtNum = sanitizeNumberInput(formData.monthlyDebt);
    const creditScoreNum = sanitizeNumberInput(formData.creditScore);
    const loanAmountNum = sanitizeNumberInput(formData.loanAmount);
    const employmentYearsNum = sanitizeNumberInput(formData.employmentYears);

    // Validate all required fields
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

    // Convert display currency to USD for backend
    const annualIncomeUSD = convertToUSD(annualIncomeNum, currency);
    const monthlyDebtUSD = convertToUSD(monthlyDebtNum, currency);
    const loanAmountUSD = convertToUSD(loanAmountNum, currency);

    // Backend always receives USD values
    await runPrediction({
      annualIncome: annualIncomeUSD,
      monthlyDebt: monthlyDebtUSD,
      creditScore: creditScoreNum,
      loanAmount: loanAmountUSD,
      employmentYears: employmentYearsNum
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <motion.div 
        className="mb-10"
        initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      >
        <h2 className="text-3xl font-display font-bold text-white mb-2">Risk Analysis Console</h2>
        <p className="text-slate-400">Enter applicant financial data for real-time ML-powered assessment.</p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Input Form */}
        <motion.div 
          className="lg:col-span-4 space-y-6"
          initial={prefersReducedMotion ? {} : { opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.1, ease: 'easeOut' }}
        >
          <div className="glass-panel p-6 rounded-xl">
            <h3 className="text-lg font-medium text-white mb-6 flex items-center gap-2">
              <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Applicant Data
            </h3>
            
            {/* Phase 4C UX Stability Fix - Validation error display */}
            {validationError && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                <p className="text-sm text-red-400">{validationError}</p>
              </div>
            )}
            
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1 uppercase tracking-wide">
                  Annual Income ({currency})
                </label>
                <input
                  type="text"
                  inputMode="decimal"
                  name="annualIncome"
                  value={formData.annualIncome}
                  onChange={handleInputChange}
                  placeholder="e.g., 85000"
                  className="w-full bg-dark-800 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1 uppercase tracking-wide">
                  Monthly Debt ({currency})
                </label>
                <input
                  type="text"
                  inputMode="decimal"
                  name="monthlyDebt"
                  value={formData.monthlyDebt}
                  onChange={handleInputChange}
                  placeholder="e.g., 1200"
                  className="w-full bg-dark-800 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1 uppercase tracking-wide">Credit Score</label>
                <input
                  type="text"
                  inputMode="numeric"
                  name="creditScore"
                  value={formData.creditScore}
                  onChange={handleInputChange}
                  placeholder="e.g., 720"
                  className="w-full bg-dark-800 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1 uppercase tracking-wide">
                  Loan Amount ({currency})
                </label>
                <input
                  type="text"
                  inputMode="decimal"
                  name="loanAmount"
                  value={formData.loanAmount}
                  onChange={handleInputChange}
                  placeholder="e.g., 25000"
                  className="w-full bg-dark-800 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1 uppercase tracking-wide">Employment (Years)</label>
                <input
                  type="text"
                  inputMode="numeric"
                  name="employmentYears"
                  value={formData.employmentYears}
                  onChange={handleInputChange}
                  placeholder="e.g., 5"
                  className="w-full bg-dark-800 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                />
              </div>

              <motion.button
                onClick={handleAnalyze}
                disabled={loading}
                className="w-full mt-6 bg-brand-600 hover:bg-brand-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg shadow-lg shadow-brand-500/20 transition-all duration-200 flex items-center justify-center gap-2"
                whileHover={!prefersReducedMotion && !loading ? { scale: 1.02 } : {}}
                whileTap={!prefersReducedMotion && !loading ? { scale: 0.98 } : {}}
                transition={{ duration: 0.15 }}
              >
                {loading ? 'Analyzing...' : 'Run Analysis'}
              </motion.button>
            </div>
          </div>
        </motion.div>

        {/* ML Results - Right Column */}
        <motion.div 
          className="lg:col-span-8 space-y-6"
          initial={prefersReducedMotion ? {} : { opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.2, ease: 'easeOut' }}
        >
          {loading ? (
            /* Loading State - Minimal Skeleton */
            <div className="glass-panel p-12 rounded-xl text-center">
              <div className="inline-block w-12 h-12 border-4 border-slate-700 border-t-brand-500 rounded-full animate-spin mb-4" />
              <h3 className="text-lg font-medium text-slate-400">Analyzing risk profile...</h3>
            </div>
          ) : error ? (
            /* Error State - Single Line Fallback */
            <div className="glass-panel p-12 rounded-xl text-center">
              <svg className="w-16 h-16 text-slate-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-lg font-medium text-slate-400 mb-2">{error}</h3>
              <p className="text-sm text-slate-500">
                Please try again or contact support if the issue persists
              </p>
            </div>
          ) : prediction ? (
            <>
              {/* 1. Prediction Summary (PRIMARY FOCUS) */}
              <PredictionHeader 
                riskScore={prediction.risk_score}
                riskBand={prediction.risk_band}
              />

              {/* 2. Model Confidence */}
              <ModelConfidence 
                confidence={prediction.confidence}
              />

              {/* 3. Key Risk Drivers (Explainability Preview) */}
              <KeyRiskDrivers 
                features={prediction.top_features}
              />

              {/* 4. Recommendation (Decision Layer) */}
              <RecommendationPanel 
                recommendation={prediction.recommendation}
                riskBand={prediction.risk_band}
              />
            </>
          ) : (
            <div className="glass-panel p-12 rounded-xl text-center">
              <svg className="w-16 h-16 text-slate-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <h3 className="text-lg font-medium text-slate-400 mb-2">No Analysis Yet</h3>
              <p className="text-sm text-slate-500">
                Enter applicant data and click "Run Analysis" to generate a risk assessment
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
};
