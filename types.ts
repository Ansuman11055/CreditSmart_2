export interface FinancialProfile {
  annualIncome: number;
  monthlyDebt: number;
  creditScore: number;
  loanAmount: number;
  employmentYears: number;
}

export interface RiskAnalysis {
  score: number;
  riskLevel: 'Low' | 'Medium' | 'High' | 'Critical';
  summary: string;
  factors: string[];
  recommendation: string;
}

export enum View {
  LANDING = 'LANDING',
  DASHBOARD = 'DASHBOARD'
}