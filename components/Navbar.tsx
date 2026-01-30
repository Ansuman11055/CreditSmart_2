import React, { useState, useEffect } from 'react';
import { View } from '../types';

interface NavbarProps {
  currentView: View;
  onViewChange: (view: View) => void;
  className?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ currentView, onViewChange, className = '' }) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: 'Product', href: '#' },
    { name: 'Risk Engine', href: '#' },
    { name: 'Explainability', href: '#' },
    { name: 'Developers', href: '#' },
  ];

  return (
    <nav 
      className={`fixed top-0 left-0 w-full z-50 transition-all duration-300 ${
        isScrolled || isMobileMenuOpen 
          ? 'bg-dark-900/80 backdrop-blur-md border-b border-white/5 py-4' 
          : 'bg-transparent py-6'
      } ${className}`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          {/* Brand */}
          <div 
            className="flex items-center gap-2 cursor-pointer group" 
            onClick={() => onViewChange(View.LANDING)}
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center shadow-lg shadow-brand-500/20 group-hover:shadow-brand-500/40 transition-shadow">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <span className="font-display font-bold text-xl tracking-tight text-white group-hover:text-white/90 transition-colors">
              Credit<span className="text-brand-400">Smart</span>
            </span>
          </div>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <a 
                key={link.name} 
                href={link.href}
                className="text-sm font-medium text-slate-400 hover:text-white transition-colors"
              >
                {link.name}
              </a>
            ))}
          </div>

          {/* Actions */}
          <div className="hidden md:flex items-center gap-6">
            <button className="text-sm font-medium text-slate-400 hover:text-white transition-colors">
              Sign In
            </button>
            <button 
              onClick={() => onViewChange(View.DASHBOARD)}
              className={`px-5 py-2.5 rounded-full text-sm font-medium transition-all duration-300 ${
                currentView === View.DASHBOARD 
                  ? 'bg-white/10 text-white cursor-default border border-white/10' 
                  : 'bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-500/20 hover:translate-y-[-1px]'
              }`}
            >
              Launch Console
            </button>
          </div>

          {/* Mobile Menu Button */}
          <button 
            className="md:hidden p-2 text-slate-400 hover:text-white"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            {isMobileMenuOpen ? (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div className="md:hidden absolute top-full left-0 w-full bg-dark-900/95 backdrop-blur-xl border-b border-white/5 animate-fade-in">
          <div className="px-4 py-6 space-y-4">
            {navLinks.map((link) => (
              <a 
                key={link.name} 
                href={link.href}
                className="block text-base font-medium text-slate-300 hover:text-white transition-colors"
              >
                {link.name}
              </a>
            ))}
            <div className="pt-4 border-t border-white/10 flex flex-col gap-4">
              <button className="text-base font-medium text-slate-300 hover:text-white transition-colors text-left">
                Sign In
              </button>
              <button 
                onClick={() => {
                  onViewChange(View.DASHBOARD);
                  setIsMobileMenuOpen(false);
                }}
                className="w-full py-3 rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-medium text-center shadow-lg shadow-brand-500/20"
              >
                Launch Console
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};