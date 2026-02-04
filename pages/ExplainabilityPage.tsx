// CreditSmart Phase 3E/4 integration - Explainability Page
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Layout } from '../components/Layout';
import { View } from '../types';
import { usePrediction } from '../src/hooks/usePrediction';
import { RiskFeature } from '../src/lib/mockPrediction';

const STORAGE_KEY = 'creditsmart_last_explanation';

export const ExplainabilityPage: React.FC = () => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const [{ prediction }] = usePrediction();
  const [cachedFeatures, setCachedFeatures] = useState<RiskFeature[] | null>(null);

  // Load cached explanation from localStorage
  useEffect(() => {
    const cached = localStorage.getItem(STORAGE_KEY);
    if (cached) {
      try {
        setCachedFeatures(JSON.parse(cached));
      } catch (e) {
        console.error('Failed to parse cached explanation:', e);
      }
    }
  }, []);

  // Cache new explanation when prediction updates
  useEffect(() => {
    if (prediction?.top_features) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(prediction.top_features));
      setCachedFeatures(prediction.top_features);
    }
  }, [prediction]);

  const displayFeatures = prediction?.top_features || cachedFeatures || [];
  const hasData = displayFeatures.length > 0;

  const getImpactColor = (impact: string) => {
    return impact === 'positive' 
      ? 'bg-green-500/10 border-green-500/30 text-green-400'
      : 'bg-red-500/10 border-red-500/30 text-red-400';
  };

  const getImpactIcon = (impact: string) => {
    return impact === 'positive' ? (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
      </svg>
    ) : (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
      </svg>
    );
  };

  return (
    <Layout currentView={View.LANDING} onViewChange={() => {}}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Header */}
        <motion.div
          className="text-center mb-12"
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-5xl font-display font-bold mb-4">
            AI<span className="text-brand-400"> Explainability</span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            Transparent feature importance analysis powered by SHAP values
          </p>
        </motion.div>

        {hasData ? (
          <>
            {/* Explanation Source */}
            <motion.div
              className="glass-panel p-6 rounded-xl mb-8 border-brand-500/20"
              initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
            >
              <div className="flex items-center gap-3">
                <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-slate-400">
                  {prediction ? 'Live explanation from latest prediction' : 'Cached explanation from previous analysis'}
                </span>
              </div>
            </motion.div>

            {/* Feature Importance Cards */}
            <div className="space-y-6">
              {displayFeatures.slice(0, 5).map((feature, index) => (
                <motion.div
                  key={index}
                  className="glass-panel p-8 rounded-xl"
                  initial={prefersReducedMotion ? {} : { opacity: 0, x: -30 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.2 + index * 0.1 }}
                >
                  <div className="flex items-start gap-6">
                    {/* Impact Indicator */}
                    <div className={`p-4 rounded-xl border ${getImpactColor(feature.impact)}`}>
                      {getImpactIcon(feature.impact)}
                    </div>

                    {/* Feature Details */}
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-2xl font-bold text-white">{feature.name}</h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase ${
                          feature.impact === 'positive' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                        }`}>
                          {feature.impact}
                        </span>
                      </div>
                      <p className="text-slate-400 leading-relaxed">{feature.reason}</p>
                    </div>

                    {/* Ranking Badge */}
                    <div className="flex flex-col items-center">
                      <div className="w-12 h-12 rounded-full bg-brand-500/10 border border-brand-500/30 flex items-center justify-center">
                        <span className="text-xl font-bold text-brand-400">#{index + 1}</span>
                      </div>
                      <span className="text-xs text-slate-500 mt-2">Rank</span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Summary Stats */}
            <motion.div
              className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6"
              initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.8 }}
            >
              <div className="glass-panel p-6 rounded-xl text-center">
                <div className="text-3xl font-bold text-brand-400 mb-2">{displayFeatures.length}</div>
                <div className="text-sm text-slate-500">Total Features Analyzed</div>
              </div>
              <div className="glass-panel p-6 rounded-xl text-center">
                <div className="text-3xl font-bold text-green-400 mb-2">
                  {displayFeatures.filter(f => f.impact === 'positive').length}
                </div>
                <div className="text-sm text-slate-500">Positive Factors</div>
              </div>
              <div className="glass-panel p-6 rounded-xl text-center">
                <div className="text-3xl font-bold text-red-400 mb-2">
                  {displayFeatures.filter(f => f.impact === 'negative').length}
                </div>
                <div className="text-sm text-slate-500">Risk Factors</div>
              </div>
            </motion.div>

            {/* Methodology */}
            <motion.div
              className="mt-12 glass-panel p-8 rounded-xl"
              initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 1.0 }}
            >
              <h3 className="text-xl font-bold text-white mb-4">How It Works</h3>
              <p className="text-slate-400 leading-relaxed mb-4">
                Our explainability engine uses SHAP (SHapley Additive exPlanations) values to break down each prediction
                into individual feature contributions. This approach provides mathematically rigorous, model-agnostic
                explanations that satisfy regulatory requirements for transparency.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                <div className="p-4 bg-dark-800 rounded-lg">
                  <div className="text-brand-400 font-semibold mb-2">📊 Feature Ranking</div>
                  <div className="text-sm text-slate-500">Ordered by absolute impact on prediction</div>
                </div>
                <div className="p-4 bg-dark-800 rounded-lg">
                  <div className="text-brand-400 font-semibold mb-2">🎯 Direction</div>
                  <div className="text-sm text-slate-500">Positive or negative contribution to risk</div>
                </div>
                <div className="p-4 bg-dark-800 rounded-lg">
                  <div className="text-brand-400 font-semibold mb-2">✅ Audit Ready</div>
                  <div className="text-sm text-slate-500">Full traceability for compliance teams</div>
                </div>
              </div>
            </motion.div>
          </>
        ) : (
          <motion.div
            className="glass-panel p-16 rounded-xl text-center"
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <svg className="w-20 h-20 text-slate-600 mx-auto mb-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
            </svg>
            <h3 className="text-2xl font-bold text-slate-400 mb-3">No Explanation Available</h3>
            <p className="text-slate-500 mb-6 max-w-md mx-auto">
              Run a prediction from the Dashboard or Risk Engine to generate feature importance analysis
            </p>
            <a
              href="/dashboard"
              className="inline-block px-6 py-3 bg-brand-600 hover:bg-brand-500 text-white font-medium rounded-lg transition-colors"
            >
              Go to Dashboard
            </a>
          </motion.div>
        )}
      </div>
    </Layout>
  );
};
