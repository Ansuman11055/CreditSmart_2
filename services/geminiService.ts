import { GoogleGenAI } from "@google/genai";
import { FinancialProfile, RiskAnalysis } from "../types";

const processEnvApiKey = process.env.API_KEY;

export const analyzeRisk = async (profile: FinancialProfile): Promise<RiskAnalysis> => {
  if (!processEnvApiKey) {
    // Fallback mock if no API key is present for demo purposes
    return new Promise(resolve => setTimeout(() => resolve({
      score: 785,
      riskLevel: 'Low',
      summary: 'Based on the provided financial profile, the applicant demonstrates strong repayment capacity. The debt-to-income ratio is healthy, and the credit score indicates a history of responsible credit usage.',
      factors: [
        'High credit score (700+)',
        'Low debt-to-income ratio',
        'Stable employment history'
      ],
      recommendation: 'Approve loan with competitive interest rate.'
    }), 1500));
  }

  const ai = new GoogleGenAI({ apiKey: processEnvApiKey });

  const prompt = `
    Act as a senior credit risk underwriter. Analyze the following financial profile for a loan application:
    
    Annual Income: $${profile.annualIncome}
    Monthly Debt Obligations: $${profile.monthlyDebt}
    Credit Score: ${profile.creditScore}
    Requested Loan Amount: $${profile.loanAmount}
    Years of Employment: ${profile.employmentYears}

    Provide a JSON response with the following structure:
    {
      "score": number (0-1000 proprietary risk score, higher is better),
      "riskLevel": "Low" | "Medium" | "High" | "Critical",
      "summary": "A brief 2-3 sentence professional summary of the risk profile.",
      "factors": ["Key factor 1", "Key factor 2", "Key factor 3"],
      "recommendation": "A concise recommendation for the loan officer."
    }
  `;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: prompt,
      config: {
        responseMimeType: 'application/json'
      }
    });

    const text = response.text;
    if (!text) throw new Error("No response from AI");
    
    return JSON.parse(text) as RiskAnalysis;
  } catch (error) {
    console.error("AI Analysis failed", error);
    throw error;
  }
};