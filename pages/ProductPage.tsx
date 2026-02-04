// CreditSmart Phase 3E/4 integration - Product Overview Page
import React from 'react';
import { motion } from 'framer-motion';
import { Layout } from '../components/Layout';
import { View } from '../types';

export const ProductPage: React.FC = () => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const features = [
    {
      icon: (
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      title: "Credit Risk Assessment",
      description: "ML-powered risk scoring with 95%+ accuracy. Our Random Forest model analyzes 11+ financial indicators to predict default probability in real-time.",
      metrics: [
        { label: "Model Accuracy", value: "95.2%" },
        { label: "Inference Time", value: "<50ms" },
        { label: "Daily Predictions", value: "50K+" }
      ]
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      title: "ML-Driven Decisioning",
      description: "Automated approval workflows with configurable risk thresholds. Policy engine integrates seamlessly with your existing decisioning framework.",
      metrics: [
        { label: "Auto-Approve Rate", value: "68%" },
        { label: "False Positive", value: "<2%" },
        { label: "Processing Time", value: "3.2s avg" }
      ]
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
        </svg>
      ),
      title: "Explainable AI for Trust",
      description: "SHAP-based feature importance reveals exactly why each decision was made. Full auditability for compliance teams and transparency for applicants.",
      metrics: [
        { label: "Compliance Ready", value: "100%" },
        { label: "Feature Tracking", value: "11 factors" },
        { label: "Audit Trail", value: "Complete" }
      ]
    }
  ];

  return (
    <Layout currentView={View.LANDING} onViewChange={() => {}}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Hero Section */}
        <motion.div
          className="text-center mb-20"
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-5xl md:text-6xl font-display font-bold mb-6">
            Enterprise Credit
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-brand-600">
              Risk Intelligence
            </span>
          </h1>
          <p className="text-xl text-slate-400 max-w-3xl mx-auto leading-relaxed">
            Production-grade ML platform for real-time credit decisioning.
            Built for financial institutions requiring accuracy, speed, and regulatory compliance.
          </p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              className="glass-panel p-8 rounded-xl hover:border-brand-500/30 transition-all duration-300"
              initial={prefersReducedMotion ? {} : { opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <div className="text-brand-400 mb-4">{feature.icon}</div>
              <h3 className="text-2xl font-bold text-white mb-3">{feature.title}</h3>
              <p className="text-slate-400 mb-6 leading-relaxed">{feature.description}</p>
              
              {/* Metrics */}
              <div className="space-y-3 pt-4 border-t border-white/10">
                {feature.metrics.map((metric) => (
                  <div key={metric.label} className="flex justify-between items-center">
                    <span className="text-sm text-slate-500">{metric.label}</span>
                    <span className="text-sm font-semibold text-brand-400">{metric.value}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Tech Stack */}
        <motion.div
          className="glass-panel p-8 rounded-xl text-center"
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <h3 className="text-xl font-bold text-white mb-6">Production Stack</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <div className="text-3xl font-bold text-brand-400 mb-1">FastAPI</div>
              <div className="text-sm text-slate-500">Backend</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-brand-400 mb-1">Random Forest</div>
              <div className="text-sm text-slate-500">ML Model</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-brand-400 mb-1">SHAP</div>
              <div className="text-sm text-slate-500">Explainability</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-brand-400 mb-1">React</div>
              <div className="text-sm text-slate-500">Frontend</div>
            </div>
          </div>
        </motion.div>
      </div>
    </Layout>
  );
};
