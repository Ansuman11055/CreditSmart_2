// Prediction Adapter Layer
// Responsible for fetching, validating, and normalizing ML prediction data from FastAPI backend
// UI components consume normalized data only - never raw API responses

import { MLPrediction, RiskFeature } from './mockPrediction';

// Environment-aware API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const PREDICT_ENDPOINT = `${API_BASE_URL}/api/v1/predict`;

// Backend API response shape (may differ slightly from frontend contract)
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

// Input data for prediction request
export interface PredictionInput {
  annualIncome: number;
  monthlyDebt: number;
  creditScore: number;
  loanAmount: number;
  employmentYears: number;
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
 * Provides safe fallbacks for all required fields
 */
function normalizePrediction(response: BackendPredictionResponse): MLPrediction {
  // Validate and normalize risk score
  let riskScore = typeof response.risk_score === 'number' ? response.risk_score : 50;
  riskScore = Math.max(0, Math.min(100, riskScore)); // Clamp to 0-100

  // Validate and normalize risk band
  const riskBand = normalizeRiskBand(response.risk_band || "medium");

  // Validate and normalize confidence
  const confidence = normalizeConfidence(response.confidence || "medium");

  // Validate and normalize features (ensure exactly 3)
  let features: RiskFeature[] = [];
  if (Array.isArray(response.top_features)) {
    features = response.top_features.slice(0, 3).map(normalizeFeature);
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
    response.recommendation || "Manual review recommended"
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
    const response = await fetch(PREDICT_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        annual_income: input.annualIncome,
        monthly_debt: input.monthlyDebt,
        credit_score: input.creditScore,
        loan_amount: input.loanAmount,
        employment_years: input.employmentYears
      })
    });

    if (!response.ok) {
      throw new Error(`Prediction API failed: ${response.status}`);
    }

    const data: BackendPredictionResponse = await response.json();
    
    // Normalize and validate response
    return normalizePrediction(data);
  } catch (error) {
    // Log error for debugging (can be sent to monitoring service)
    console.error('Prediction fetch error:', error);
    
    // Re-throw with user-friendly message
    throw new Error('Failed to fetch prediction from backend');
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
