/**
 * Currency Utility - Frontend Display Only
 * 
 * IMPORTANT: Backend and ML model always use USD as base currency.
 * This utility is for DISPLAY purposes only.
 */

export type Currency = 'USD' | 'INR' | 'EUR' | 'GBP';

export interface CurrencyConfig {
  code: Currency;
  symbol: string;
  name: string;
  rate: number; // Conversion rate from USD
}

// Static conversion rates (hardcoded for frontend display)
export const CURRENCY_CONFIGS: Record<Currency, CurrencyConfig> = {
  USD: {
    code: 'USD',
    symbol: '$',
    name: 'US Dollar',
    rate: 1.0
  },
  INR: {
    code: 'INR',
    symbol: '₹',
    name: 'Indian Rupee',
    rate: 83.0
  },
  EUR: {
    code: 'EUR',
    symbol: '€',
    name: 'Euro',
    rate: 0.92
  },
  GBP: {
    code: 'GBP',
    symbol: '£',
    name: 'British Pound',
    rate: 0.79
  }
};

/**
 * Convert amount from USD to target currency
 * @param amountUSD - Amount in USD (base currency)
 * @param targetCurrency - Target currency code
 * @returns Converted amount
 */
export function convertFromUSD(amountUSD: number, targetCurrency: Currency): number {
  if (!amountUSD || isNaN(amountUSD)) return 0;
  
  const config = CURRENCY_CONFIGS[targetCurrency];
  if (!config) return amountUSD; // Fallback to USD
  
  return amountUSD * config.rate;
}

/**
 * Convert amount from any currency back to USD (for backend submission)
 * @param amount - Amount in source currency
 * @param sourceCurrency - Source currency code
 * @returns Amount in USD
 */
export function convertToUSD(amount: number, sourceCurrency: Currency): number {
  if (!amount || isNaN(amount)) return 0;
  
  const config = CURRENCY_CONFIGS[sourceCurrency];
  if (!config) return amount; // Already USD
  
  return amount / config.rate;
}

/**
 * Format currency value with proper symbol and locale formatting
 * @param amountUSD - Amount in USD (base currency)
 * @param targetCurrency - Currency to display in
 * @param options - Formatting options
 * @returns Formatted currency string
 */
export function formatCurrency(
  amountUSD: number,
  targetCurrency: Currency = 'USD',
  options: {
    showSymbol?: boolean;
    decimals?: number;
    compact?: boolean;
  } = {}
): string {
  const {
    showSymbol = true,
    decimals = 0,
    compact = false
  } = options;

  try {
    // Convert to target currency
    const convertedAmount = convertFromUSD(amountUSD, targetCurrency);
    const config = CURRENCY_CONFIGS[targetCurrency];
    
    if (!config) {
      // Fallback formatting
      return `$${amountUSD.toLocaleString('en-US')}`;
    }

    // Format with locale
    let formatted: string;
    
    if (compact && convertedAmount >= 1000) {
      // Compact notation for large numbers
      const formatter = new Intl.NumberFormat('en-US', {
        notation: 'compact',
        compactDisplay: 'short',
        maximumFractionDigits: 1
      });
      formatted = formatter.format(convertedAmount);
    } else {
      // Standard formatting
      const formatter = new Intl.NumberFormat('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
      });
      formatted = formatter.format(convertedAmount);
    }

    // Add currency symbol
    if (showSymbol) {
      return `${config.symbol}${formatted}`;
    }
    
    return formatted;
  } catch (error) {
    // Fallback on error
    console.error('Currency formatting error:', error);
    return `$${amountUSD.toLocaleString('en-US')}`;
  }
}

/**
 * Get currency configuration
 */
export function getCurrencyConfig(currency: Currency): CurrencyConfig {
  return CURRENCY_CONFIGS[currency] || CURRENCY_CONFIGS.USD;
}

/**
 * Validate currency code
 */
export function isValidCurrency(code: string): code is Currency {
  return code in CURRENCY_CONFIGS;
}
