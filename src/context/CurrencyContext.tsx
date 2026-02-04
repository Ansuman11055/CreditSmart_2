/**
 * Currency Context - Global Currency State Management
 * 
 * Manages user's selected currency preference.
 * Persists to localStorage for cross-session consistency.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Currency, isValidCurrency } from '../utils/currency';

const STORAGE_KEY = 'creditsmart_currency';
const DEFAULT_CURRENCY: Currency = 'USD';

interface CurrencyContextValue {
  currency: Currency;
  setCurrency: (currency: Currency) => void;
}

const CurrencyContext = createContext<CurrencyContextValue | undefined>(undefined);

interface CurrencyProviderProps {
  children: ReactNode;
}

export function CurrencyProvider({ children }: CurrencyProviderProps) {
  const [currency, setCurrencyState] = useState<Currency>(DEFAULT_CURRENCY);

  // Load currency from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored && isValidCurrency(stored)) {
        setCurrencyState(stored);
      }
    } catch (error) {
      console.error('Failed to load currency from localStorage:', error);
    }
  }, []);

  // Update currency and persist to localStorage
  const setCurrency = (newCurrency: Currency) => {
    try {
      setCurrencyState(newCurrency);
      localStorage.setItem(STORAGE_KEY, newCurrency);
    } catch (error) {
      console.error('Failed to save currency to localStorage:', error);
    }
  };

  return (
    <CurrencyContext.Provider value={{ currency, setCurrency }}>
      {children}
    </CurrencyContext.Provider>
  );
}

/**
 * Hook to access currency context
 */
export function useCurrency() {
  const context = useContext(CurrencyContext);
  if (!context) {
    throw new Error('useCurrency must be used within CurrencyProvider');
  }
  return context;
}
