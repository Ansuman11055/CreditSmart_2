// Mock ML Prediction Data Contract
// This structure is designed to be directly replaceable by FastAPI backend responses
// without requiring UI refactors

export interface RiskFeature {
  name: string;
  impact: "positive" | "negative";
  reason: string;
}

export interface MLPrediction {
  risk_score: number; // 0-100
  risk_band: "low" | "medium" | "high";
  confidence: "low" | "medium" | "high";
  top_features: RiskFeature[];
  recommendation: string;
}

// Mock ML prediction generator
export function generateMockPrediction(creditScore: number, annualIncome: number, monthlyDebt: number): MLPrediction {
  // Simple risk scoring logic for demo purposes
  const debtToIncomeRatio = (monthlyDebt * 12) / annualIncome;
  const creditScoreNormalized = creditScore / 850;
  
  // Calculate risk score (0-100, lower is better)
  let riskScore = 50;
  
  if (creditScore < 600) riskScore += 30;
  else if (creditScore < 700) riskScore += 15;
  else if (creditScore > 750) riskScore -= 20;
  
  if (debtToIncomeRatio > 0.4) riskScore += 20;
  else if (debtToIncomeRatio < 0.2) riskScore -= 15;
  
  if (annualIncome > 100000) riskScore -= 10;
  else if (annualIncome < 40000) riskScore += 15;
  
  // Clamp to 0-100
  riskScore = Math.max(0, Math.min(100, riskScore));
  
  // Determine risk band
  let riskBand: "low" | "medium" | "high";
  if (riskScore < 30) riskBand = "low";
  else if (riskScore < 60) riskBand = "medium";
  else riskBand = "high";
  
  // Determine confidence
  let confidence: "low" | "medium" | "high";
  if (creditScore === 0 || annualIncome === 0) confidence = "low";
  else if (creditScore < 600 || debtToIncomeRatio > 0.5) confidence = "medium";
  else confidence = "high";
  
  // Generate top features
  const topFeatures: RiskFeature[] = [];
  
  if (creditScore >= 750) {
    topFeatures.push({
      name: "Credit Score",
      impact: "positive",
      reason: "Strong credit history demonstrates reliable repayment behavior"
    });
  } else if (creditScore < 650) {
    topFeatures.push({
      name: "Credit Score",
      impact: "negative",
      reason: "Credit history indicates elevated repayment risk"
    });
  }
  
  if (debtToIncomeRatio > 0.35) {
    topFeatures.push({
      name: "Debt-to-Income Ratio",
      impact: "negative",
      reason: "High existing debt obligations may strain repayment capacity"
    });
  } else if (debtToIncomeRatio < 0.2) {
    topFeatures.push({
      name: "Debt-to-Income Ratio",
      impact: "positive",
      reason: "Low existing debt provides strong repayment capacity"
    });
  }
  
  if (annualIncome > 90000) {
    topFeatures.push({
      name: "Annual Income",
      impact: "positive",
      reason: "High income supports loan repayment capability"
    });
  } else if (annualIncome < 50000) {
    topFeatures.push({
      name: "Annual Income",
      impact: "negative",
      reason: "Income level may limit repayment flexibility"
    });
  }
  
  // Ensure exactly 3 features (pad with neutral if needed)
  while (topFeatures.length < 3) {
    if (!topFeatures.find(f => f.name === "Employment Stability")) {
      topFeatures.push({
        name: "Employment Stability",
        impact: "positive",
        reason: "Stable employment history supports consistent income"
      });
    } else if (!topFeatures.find(f => f.name === "Loan Amount")) {
      topFeatures.push({
        name: "Loan Amount",
        impact: "positive",
        reason: "Requested amount is within reasonable limits for profile"
      });
    } else {
      break;
    }
  }
  
  // Generate recommendation
  let recommendation: string;
  if (riskBand === "low" && confidence === "high") {
    recommendation = "Approve with standard terms";
  } else if (riskBand === "low" && confidence === "medium") {
    recommendation = "Approve with standard terms, monitor closely";
  } else if (riskBand === "medium" && confidence === "high") {
    recommendation = "Manual review recommended";
  } else if (riskBand === "high") {
    recommendation = "Decline or request additional verification";
  } else {
    recommendation = "Manual review recommended";
  }
  
  return {
    risk_score: Math.round(riskScore),
    risk_band: riskBand,
    confidence,
    top_features: topFeatures.slice(0, 3),
    recommendation
  };
}
