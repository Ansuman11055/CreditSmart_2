import React from 'react';

export const LoginPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center">
      <div className="text-center space-y-6">
        <h1 className="text-5xl font-display font-bold mb-4">
          Sign<span className="text-brand-400"> In</span>
        </h1>
        <p className="text-slate-400 text-lg">Authentication coming soon...</p>
        <div className="pt-8">
          <div className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-white/5 border border-white/10">
            <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <span className="text-sm text-slate-300">Secure authentication in development</span>
          </div>
        </div>
      </div>
    </div>
  );
};
