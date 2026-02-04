// CreditSmart Phase 3E/4 integration - Developers Documentation Page
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Layout } from '../components/Layout';
import { View } from '../types';

export const DevelopersPage: React.FC = () => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const [copiedEndpoint, setCopiedEndpoint] = useState<string | null>(null);

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedEndpoint(label);
    setTimeout(() => setCopiedEndpoint(null), 2000);
  };

  const endpoints = [
    {
      method: 'POST',
      path: '/api/v1/predict',
      description: 'Generate credit risk prediction with ML model',
      request: {
        annual_income: 75000,
        monthly_debt: 1200,
        credit_score: 720,
        loan_amount: 25000,
        loan_term_months: 60,
        employment_length_years: 5,
        home_ownership: "MORTGAGE",
        purpose: "debt_consolidation",
        number_of_open_accounts: 8,
        delinquencies_2y: 0,
        inquiries_6m: 1
      },
      response: {
        status: "success",
        request_id: "req_abc123",
        model_version: "ml_v1.0.0",
        prediction: 0.23,
        confidence: 0.89,
        data: {
          risk_score: 0.23,
          risk_level: "LOW",
          recommended_action: "APPROVE",
          confidence_level: "HIGH",
          explanation: "Low risk applicant with strong credit profile"
        }
      }
    },
    {
      method: 'GET',
      path: '/api/v1/health',
      description: 'Backend health check endpoint',
      request: null,
      response: {
        status: "ok",
        timestamp: "2024-02-04T10:30:00Z",
        version: "1.0.0"
      }
    },
    {
      method: 'POST',
      path: '/api/v1/advice',
      description: 'Get detailed credit advice with risk assessment',
      request: {
        annual_income: 75000,
        monthly_debt: 1200,
        credit_score: 720,
        loan_amount: 25000,
        loan_term_months: 60,
        employment_length_years: 5,
        home_ownership: "MORTGAGE",
        purpose: "debt_consolidation",
        number_of_open_accounts: 8,
        delinquencies_2y: 0,
        inquiries_6m: 1
      },
      response: {
        decision: {
          decision: "APPROVE",
          risk_tier: "LOW",
          confidence: 0.89
        },
        advisor: {
          summary: "Strong credit profile with low risk indicators",
          key_risk_factors: ["Excellent credit score", "Low DTI ratio"],
          recommended_actions: ["Standard approval", "Monitor repayment"],
          next_steps: "Proceed with loan processing",
          user_tone: "professional"
        }
      }
    }
  ];

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
            Developer<span className="text-brand-400"> Documentation</span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            REST API reference for CreditSmart ML platform
          </p>
        </motion.div>

        {/* Quick Start */}
        <motion.div
          className="glass-panel p-8 rounded-xl mb-12"
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <h2 className="text-2xl font-bold text-white mb-4">Quick Start</h2>
          <div className="space-y-4">
            <div>
              <div className="text-sm text-slate-400 mb-2">Base URL</div>
              <div className="flex items-center gap-3">
                <code className="flex-1 bg-dark-800 px-4 py-3 rounded-lg text-brand-400 font-mono text-sm">
                  http://localhost:8000
                </code>
                <button
                  onClick={() => copyToClipboard('http://localhost:8000', 'base-url')}
                  className="px-4 py-3 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors text-sm font-medium"
                >
                  {copiedEndpoint === 'base-url' ? '✓ Copied' : 'Copy'}
                </button>
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-2">Authentication</div>
              <div className="bg-dark-800 px-4 py-3 rounded-lg text-slate-300">
                Currently using local development mode. Production environment will require API keys.
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-2">Content Type</div>
              <code className="block bg-dark-800 px-4 py-3 rounded-lg text-brand-400 font-mono text-sm">
                Content-Type: application/json
              </code>
            </div>
          </div>
        </motion.div>

        {/* API Endpoints */}
        <div className="space-y-8">
          {endpoints.map((endpoint, index) => (
            <motion.div
              key={endpoint.path}
              className="glass-panel p-8 rounded-xl"
              initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 + index * 0.1 }}
            >
              {/* Endpoint Header */}
              <div className="flex items-center gap-4 mb-4">
                <span className={`px-3 py-1 rounded-lg font-bold text-sm ${
                  endpoint.method === 'GET' 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-blue-500/20 text-blue-400'
                }`}>
                  {endpoint.method}
                </span>
                <code className="text-brand-400 font-mono">{endpoint.path}</code>
              </div>

              <p className="text-slate-400 mb-6">{endpoint.description}</p>

              {/* Request Example */}
              {endpoint.request && (
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-semibold text-white uppercase tracking-wide">Request Body</h4>
                    <button
                      onClick={() => copyToClipboard(JSON.stringify(endpoint.request, null, 2), `request-${index}`)}
                      className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
                    >
                      {copiedEndpoint === `request-${index}` ? '✓ Copied' : 'Copy'}
                    </button>
                  </div>
                  <pre className="bg-dark-800 p-4 rounded-lg overflow-x-auto">
                    <code className="text-sm text-slate-300 font-mono">
                      {JSON.stringify(endpoint.request, null, 2)}
                    </code>
                  </pre>
                </div>
              )}

              {/* Response Example */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-semibold text-white uppercase tracking-wide">Response</h4>
                  <button
                    onClick={() => copyToClipboard(JSON.stringify(endpoint.response, null, 2), `response-${index}`)}
                    className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
                  >
                    {copiedEndpoint === `response-${index}` ? '✓ Copied' : 'Copy'}
                  </button>
                </div>
                <pre className="bg-dark-800 p-4 rounded-lg overflow-x-auto">
                  <code className="text-sm text-slate-300 font-mono">
                    {JSON.stringify(endpoint.response, null, 2)}
                  </code>
                </pre>
              </div>
            </motion.div>
          ))}
        </div>

        {/* SDK & Libraries */}
        <motion.div
          className="mt-12 glass-panel p-8 rounded-xl"
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
        >
          <h2 className="text-2xl font-bold text-white mb-6">SDKs & Client Libraries</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 bg-dark-800 rounded-lg">
              <div className="text-xl font-bold text-brand-400 mb-2">Python</div>
              <code className="text-sm text-slate-400 font-mono">pip install creditsmart-sdk</code>
              <div className="mt-3 text-xs text-slate-500">Coming soon</div>
            </div>
            <div className="p-6 bg-dark-800 rounded-lg">
              <div className="text-xl font-bold text-brand-400 mb-2">JavaScript</div>
              <code className="text-sm text-slate-400 font-mono">npm install @creditsmart/sdk</code>
              <div className="mt-3 text-xs text-slate-500">Coming soon</div>
            </div>
            <div className="p-6 bg-dark-800 rounded-lg">
              <div className="text-xl font-bold text-brand-400 mb-2">curl</div>
              <code className="text-sm text-slate-400 font-mono">Available now</code>
              <div className="mt-3 text-xs text-slate-500">See examples above</div>
            </div>
          </div>
        </motion.div>

        {/* Rate Limits & Support */}
        <motion.div
          className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-8"
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.0 }}
        >
          <div className="glass-panel p-6 rounded-xl">
            <h3 className="text-lg font-bold text-white mb-3">Rate Limits</h3>
            <div className="space-y-2 text-slate-400">
              <div className="flex justify-between">
                <span>Development</span>
                <span className="text-brand-400">Unlimited</span>
              </div>
              <div className="flex justify-between">
                <span>Production</span>
                <span className="text-brand-400">1000 req/min</span>
              </div>
              <div className="flex justify-between">
                <span>Enterprise</span>
                <span className="text-brand-400">Custom</span>
              </div>
            </div>
          </div>
          <div className="glass-panel p-6 rounded-xl">
            <h3 className="text-lg font-bold text-white mb-3">Support</h3>
            <div className="space-y-2 text-slate-400">
              <div>📧 developers@creditsmart.ai</div>
              <div>📖 Full docs: docs.creditsmart.ai</div>
              <div>💬 Discord: discord.gg/creditsmart</div>
            </div>
          </div>
        </motion.div>
      </div>
    </Layout>
  );
};
