// usePrediction Hook
// Custom React hook for managing ML prediction state with live backend integration
// Handles loading, error states, and provides normalized prediction data

import { useState, useCallback } from 'react';
import { MLPrediction, generateMockPrediction } from '../lib/mockPrediction';
import { fetchPrediction, PredictionInput } from '../lib/predictionAdapter';

// Feature flag for mock/live data toggle (rollback safety)
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_PREDICTION === 'true';

export interface PredictionState {
  prediction: MLPrediction | null;
  loading: boolean;
  error: string | null;
  analyzed: boolean;
}

export interface PredictionActions {
  runPrediction: (input: PredictionInput) => Promise<void>;
  reset: () => void;
}

/**
 * Custom hook for ML prediction state management
 * Supports both live backend and mock data fallback
 */
export function usePrediction(): [PredictionState, PredictionActions] {
  const [state, setState] = useState<PredictionState>({
    prediction: null,
    loading: false,
    error: null,
    analyzed: false
  });

  /**
   * Execute prediction request
   * Uses live backend by default, falls back to mock if flag is enabled
   */
  const runPrediction = useCallback(async (input: PredictionInput) => {
    // Reset error state
    setState(prev => ({
      ...prev,
      loading: true,
      error: null
    }));

    try {
      let prediction: MLPrediction;

      if (USE_MOCK_DATA) {
        // Mock data path (rollback safety)
        await new Promise(resolve => setTimeout(resolve, 500)); // Simulate network delay
        prediction = generateMockPrediction(
          input.creditScore,
          input.annualIncome,
          input.monthlyDebt
        );
      } else {
        // Live backend path
        prediction = await fetchPrediction(input);
      }

      setState({
        prediction,
        loading: false,
        error: null,
        analyzed: true
      });
    } catch (error) {
      setState({
        prediction: null,
        loading: false,
        error: 'Prediction temporarily unavailable',
        analyzed: false
      });
    }
  }, []);

  /**
   * Reset prediction state
   */
  const reset = useCallback(() => {
    setState({
      prediction: null,
      loading: false,
      error: null,
      analyzed: false
    });
  }, []);

  return [
    state,
    { runPrediction, reset }
  ];
}
