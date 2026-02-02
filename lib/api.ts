import axios from 'axios';
import { FinancialProfile, RiskAnalysis } from '../types';

// Environment variable for API base URL
// Defaults to local placeholder if not set
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  timeout: 10000, // 10s timeout
});

// Request Interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Scaffold for future auth token injection
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Scaffold for global error handling (logging, redirects, etc.)
    console.warn('API Request Failed:', error.response ? error.response.data : error.message);
    return Promise.reject(error);
  }
);

/**
 * Production Credit Risk API service
 * Connects to FastAPI backend at /api/v1/risk-analysis
 */
export const creditRiskApi = {
  /**
   * Calculate risk score based on financial profile.
   * @param input FinancialProfile from frontend form
   * @returns Promise with RiskAnalysis response
   */
  getRiskScore: async (input: FinancialProfile): Promise<{ data: RiskAnalysis }> => {
    // Production API call to FastAPI backend
    const response = await apiClient.post<RiskAnalysis>('/risk-analysis', input);
    return { data: response.data };
  },

  /**
   * Check API health status
   */
  healthCheck: async () => {
    return apiClient.get('/health');
  }
};