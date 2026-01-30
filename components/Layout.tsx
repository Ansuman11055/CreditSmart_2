import React from 'react';
import { View } from '../types';
import { Navbar } from './Navbar';

interface LayoutProps {
  children: React.ReactNode;
  currentView: View;
  onViewChange: (view: View) => void;
}

export const Layout: React.FC<LayoutProps> = ({ children, currentView, onViewChange }) => {
  return (
    <div className="min-h-screen flex flex-col font-sans text-slate-300 selection:bg-brand-500/30">
      
      <Navbar currentView={currentView} onViewChange={onViewChange} />

      {/* Main Content */}
      <main className="flex-grow pt-24 relative">
        {/* Background Gradients */}
        <div className="fixed inset-0 pointer-events-none z-[-1] overflow-hidden">
          <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-brand-900/10 blur-[120px]" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-900/10 blur-[120px]" />
        </div>
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 relative z-10 bg-black/40 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center gap-6">
          <p className="text-slate-500 text-sm">© 2024 CreditSmart Intelligence Inc. All rights reserved.</p>
          <div className="flex gap-6 text-slate-500">
            <a href="#" className="hover:text-brand-400 transition-colors text-sm">Privacy</a>
            <a href="#" className="hover:text-brand-400 transition-colors text-sm">Terms</a>
            <a href="#" className="hover:text-brand-400 transition-colors text-sm">Status</a>
          </div>
        </div>
      </footer>
    </div>
  );
};