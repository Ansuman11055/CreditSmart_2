import axios from 'axios';

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
 * Placeholder service for Credit Risk API
 */
export const creditRiskApi = {
  /**
   * Calculate risk score based on input parameters.
   * @param input Dictionary of financial data
   * @returns Promise with risk score data
   */
  getRiskScore: async (input: Record<string, any>) => {
    // SCALAR: This is a placeholder. In production, uncomment the API call.
    // return apiClient.post('/risk/evaluate', input);
    
    // Placeholder mock response for UI development
    console.log('[API Scaffold] getRiskScore called with:', input);
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          data: {
            score: 750,
            probability_of_default: 0.05,
            timestamp: new Date().toISOString(),
            status: 'success'
          }
        });
      }, 800);
    });
  },

  /**
   * Check API health status
   */
  healthCheck: async () => {
    return apiClient.get('/health');
  }
};