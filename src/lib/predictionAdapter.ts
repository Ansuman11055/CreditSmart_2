// Prediction Adapter Layer
// Responsible for fetching, validating, and normalizing ML prediction data from FastAPI backend
// UI components consume normalized data only - never raw API responses

import { MLPrediction, RiskFeature } from './mockPrediction';

// Environment-aware API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const PREDICT_ENDPOINT = `${API_BASE_URL}/api/v1/predict`;

// UXSafePredictionResponse from backend (new structure after Phase 4)
interface UXSafePredictionResponse {
  status: 'success' | 'error';
  request_id: string;
  model_version: string;
  prediction: number | null;  // risk_score (0.0 to 1.0)
  confidence: number | null;  // confidence_level (0.0 to 1.0)
  error: string | null;
  prediction_timestamp?: string;
  inference_time_ms?: number;
  data?: {
    risk_score: number;
    risk_level: string;  // LOW, MEDIUM, HIGH
    recommended_action: string;  // APPROVE, REVIEW, REJECT
    confidence_level: string;  // LOW, MEDIUM, HIGH
    explanation: string;
    key_factors?: Record<string, any>;
  };
}

// Legacy backend API response shape (kept for backward compatibility)
interface BackendPredictionResponse {
  risk_score?: number;
  risk_band?: string;
  confidence?: string;
  top_features?: Array<{
    name?: string;
    impact?: string;
    reason?: string;
  }>;
  recommendation?: string;
}

// Input data for prediction request (extended to match backend requirements)
export interface PredictionInput {
  annualIncome: number;
  monthlyDebt: number;
  creditScore: number;
  loanAmount: number;
  employmentYears: number;
  // Additional required fields (with defaults if not provided)
  loanTermMonths?: number;
  homeOwnership?: string;
  purpose?: string;
  numberOfOpenAccounts?: number;
  delinquencies2y?: number;
  inquiries6m?: number;
}

/**
 * Validates and normalizes risk band value
 */
function normalizeRiskBand(value: any): "low" | "medium" | "high" {
  const normalized = String(value).toLowerCase();
  if (normalized === "low" || normalized === "medium" || normalized === "high") {
    return normalized as "low" | "medium" | "high";
  }
  // Safe fallback
  return "medium";
}

/**
 * Validates and normalizes confidence value
 */
function normalizeConfidence(value: any): "low" | "medium" | "high" {
  const normalized = String(value).toLowerCase();
  if (normalized === "low" || normalized === "medium" || normalized === "high") {
    return normalized as "low" | "medium" | "high";
  }
  // Safe fallback
  return "medium";
}

/**
 * Validates and normalizes feature impact
 */
function normalizeImpact(value: any): "positive" | "negative" {
  const normalized = String(value).toLowerCase();
  if (normalized === "positive" || normalized === "negative") {
    return normalized as "positive" | "negative";
  }
  // Safe fallback
  return "positive";
}

/**
 * Normalizes backend feature data into frontend contract
 */
function normalizeFeature(feature: any): RiskFeature {
  return {
    name: String(feature?.name || "Unknown Factor"),
    impact: normalizeImpact(feature?.impact),
    reason: String(feature?.reason || "Impact analysis unavailable")
  };
}

/**
 * Normalizes backend prediction response into frontend ML contract
 * Handles both UXSafePredictionResponse and legacy BackendPredictionResponse formats
 * Provides safe fallbacks for all required fields
 */
function normalizePrediction(response: UXSafePredictionResponse | BackendPredictionResponse): MLPrediction {
  // Check if it's the new UXSafePredictionResponse format
  if ('status' in response && response.status === 'success' && response.data) {
    // New format: use data object
    const data = response.data;
    
    // Convert risk_score (0.0-1.0) to percentage (0-100)
    const riskScore = Math.round((data.risk_score || 0) * 100);
    
    // Map risk_level (LOW/MEDIUM/HIGH) to risk_band (low/medium/high)
    const riskBand = normalizeRiskBand(data.risk_level || 'MEDIUM');
    
    // Map confidence_level to confidence
    const confidence = normalizeConfidence(data.confidence_level || 'MEDIUM');
    
    // Extract top 3 features from key_factors
    const features: RiskFeature[] = [];
    if (data.key_factors) {
      const factorEntries = Object.entries(data.key_factors).slice(0, 3);
      for (const [name, value] of factorEntries) {
        if (typeof value === 'object' && value !== null) {
          const factorData = value as any;
          features.push({
            name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
            impact: factorData.impact === 'negative' ? 'negative' : 'positive',
            reason: `Value: ${factorData.value}, Risk contribution: ${factorData.risk_contribution}%`
          });
        }
      }
    }
    
    // Pad with default features if less than 3
    while (features.length < 3) {
      features.push({
        name: "Additional Factor",
        impact: "positive",
        reason: "Supplementary risk assessment factor"
      });
    }
    
    return {
      risk_score: riskScore,
      risk_band: riskBand,
      confidence,
      top_features: features,
      recommendation: data.explanation || data.recommended_action || "Manual review recommended"
    };
  }
  
  // Legacy format fallback
  const legacyResponse = response as BackendPredictionResponse;
  
  // Validate and normalize risk score
  let riskScore = typeof legacyResponse.risk_score === 'number' ? legacyResponse.risk_score : 50;
  riskScore = Math.max(0, Math.min(100, riskScore)); // Clamp to 0-100

  // Validate and normalize risk band
  const riskBand = normalizeRiskBand(legacyResponse.risk_band || "medium");

  // Validate and normalize confidence
  const confidence = normalizeConfidence(legacyResponse.confidence || "medium");

  // Validate and normalize features (ensure exactly 3)
  let features: RiskFeature[] = [];
  if (Array.isArray(legacyResponse.top_features)) {
    features = legacyResponse.top_features.slice(0, 3).map(normalizeFeature);
  }
  
  // Pad with default features if less than 3
  while (features.length < 3) {
    features.push({
      name: "Additional Factor",
      impact: "positive",
      reason: "Supplementary risk assessment factor"
    });
  }

  // Validate recommendation
  const recommendation = String(
    legacyResponse.recommendation || "Manual review recommended"
  );

  return {
    risk_score: riskScore,
    risk_band: riskBand,
    confidence,
    top_features: features,
    recommendation
  };
}

/**
 * Fetches ML prediction from FastAPI backend
 * Returns normalized prediction data or throws error
 */
export async function fetchPrediction(input: PredictionInput): Promise<MLPrediction> {
  try {
    // Build request payload with all required fields
    // Provide sensible defaults for optional fields not provided by frontend
    const requestBody = {
      annual_income: input.annualIncome,
      monthly_debt: input.monthlyDebt,
      credit_score: input.creditScore,
      loan_amount: input.loanAmount,
      loan_term_months: input.loanTermMonths || 60,  // Default: 5 years
      employment_length_years: input.employmentYears,
      home_ownership: input.homeOwnership || 'RENT',  // Default: RENT
      purpose: input.purpose || 'debt_consolidation',  // Default purpose
      number_of_open_accounts: input.numberOfOpenAccounts || 5,  // Default
      delinquencies_2y: input.delinquencies2y || 0,  // Default: no delinquencies
      inquiries_6m: input.inquiries6m || 1  // Default: 1 inquiry
    };

    const response = await fetch(PREDICT_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    });

    // Handle HTTP errors
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      console.error('Prediction API HTTP error:', {
        status: response.status,
        statusText: response.statusText,
        errorData
      });
      
      // Provide specific error messages based on status code
      if (response.status === 422) {
        throw new Error('Invalid input data. Please check all fields and try again.');
      } else if (response.status === 504) {
        throw new Error('Prediction timeout. Please try again with different inputs.');
      } else if (response.status >= 500) {
        throw new Error('Server error. Please try again later.');
      } else {
        throw new Error(`Prediction failed: ${response.status} ${response.statusText}`);
      }
    }

    const data: any = await response.json();
    
    // Check if backend returned an error in the response body
    if (data.status === 'error') {
      const backendError = data.error || 'Unknown backend error';
      console.error('Backend returned error:', {
        request_id: data.request_id,
        error: backendError,
        model_version: data.model_version
      });
      throw new Error(backendError);
    }
    
    // Normalize and validate response
    return normalizePrediction(data);
  } catch (error) {
    // Log error for debugging (can be sent to monitoring service)
    console.error('Prediction fetch error:', error);
    
    // Re-throw with preserved message if it's already an Error
    if (error instanceof Error) {
      throw error;
    }
    
    // Otherwise create a generic network error
    throw new Error('Network error. Please check your connection and try again.');
  }
}

/**
 * Health check for prediction API
 */
export async function checkPredictionHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
      method: 'GET',
    });
    return response.ok;
  } catch {
    return false;
  }
}
