/**
 * Currency Selector Component
 * 
 * Dropdown selector for user currency preference.
 * Displays in navbar, persists to localStorage.
 */

import React, { useState, useRef, useEffect } from 'react';
import { Currency, CURRENCY_CONFIGS } from '../utils/currency';
import { useCurrency } from '../context/CurrencyContext';

export const CurrencySelector: React.FC = () => {
  const { currency, setCurrency } = useCurrency();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleSelect = (newCurrency: Currency) => {
    setCurrency(newCurrency);
    setIsOpen(false);
  };

  const currentConfig = CURRENCY_CONFIGS[currency];

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition-colors text-sm font-medium text-slate-300 hover:text-white"
        aria-label="Select currency"
      >
        <span className="text-base">{currentConfig.symbol}</span>
        <span>{currentConfig.code}</span>
        <svg 
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-dark-800 border border-white/10 rounded-lg shadow-xl shadow-black/20 overflow-hidden z-50">
          {(Object.keys(CURRENCY_CONFIGS) as Currency[]).map((currencyCode) => {
            const config = CURRENCY_CONFIGS[currencyCode];
            const isSelected = currencyCode === currency;

            return (
              <button
                key={currencyCode}
                onClick={() => handleSelect(currencyCode)}
                className={`w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors ${
                  isSelected ? 'bg-brand-600/20 text-white' : 'text-slate-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-lg">{config.symbol}</span>
                  <div className="text-left">
                    <div className="text-sm font-medium">{config.code}</div>
                    <div className="text-xs text-slate-500">{config.name}</div>
                  </div>
                </div>
                {isSelected && (
                  <svg className="w-4 h-4 text-brand-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
