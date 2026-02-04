# Frontend Integration Guide - Explainability API

**Phase 4D Explainability** - Quick Reference for Frontend Developers

---

## 🚀 Quick Start

### 1. Make a Prediction

```typescript
const response = await fetch('/api/v1/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    annual_income: 75000,
    monthly_debt: 1200,
    credit_score: 720,
    loan_amount: 25000,
    loan_term_months: 60,
    employment_length_years: 5,
    home_ownership: "MORTGAGE",
    purpose: "debt_consolidation",
    number_of_open_accounts: 8,
    delinquencies_2y: 0,
    inquiries_6m: 1
  })
});

const prediction = await response.json();
console.log("Risk Score:", prediction.data.risk_score);
console.log("Request ID:", prediction.request_id);  // Save this!
```

### 2. Get Explanation

```typescript
const explanationResponse = await fetch(
  `/api/v1/explain/${prediction.request_id}`
);

const explanation = await explanationResponse.json();
```

---

## 📋 Response Schema

### ExplanationResponse

```typescript
interface ExplanationResponse {
  request_id: string;
  model_version: string;
  risk_score: number;  // 0.0 to 1.0
  risk_band: "low" | "medium" | "high";
  risk_band_description: string;
  
  top_positive_features: FeatureContribution[];  // Max 3
  top_negative_features: FeatureContribution[];  // Max 3
  
  what_helped: string[];    // Natural language (3-5 items)
  what_hurt: string[];      // Natural language (3-5 items)
  how_to_improve: string[]; // Actionable suggestions (max 3)
  
  disclaimer: string;  // Always present
  status: "success" | "error";
}

interface FeatureContribution {
  feature_name: string;      // "credit_score"
  human_name: string;        // "Credit Score"
  shap_value: number;        // SHAP contribution
  feature_value: any;        // Actual value (750)
  impact: "positive" | "negative";
  magnitude: "low" | "medium" | "high";
  explanation: string;       // Natural language
}
```

---

## 🎨 UI Components

### Risk Band Badge

```tsx
const RiskBandBadge = ({ riskBand }: { riskBand: string }) => {
  const colors = {
    low: "bg-green-100 text-green-800",
    medium: "bg-yellow-100 text-yellow-800",
    high: "bg-red-100 text-red-800"
  };
  
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors[riskBand]}`}>
      {riskBand.toUpperCase()} RISK
    </span>
  );
};
```

### Feature Contributions List

```tsx
const FeatureList = ({ features }: { features: FeatureContribution[] }) => {
  return (
    <ul className="space-y-2">
      {features.map((feature, idx) => (
        <li key={idx} className="flex items-start gap-2">
          <span className={`
            inline-block w-2 h-2 mt-2 rounded-full
            ${feature.impact === 'positive' ? 'bg-green-500' : 'bg-red-500'}
          `} />
          <div>
            <p className="font-medium">{feature.human_name}</p>
            <p className="text-sm text-gray-600">{feature.explanation}</p>
          </div>
        </li>
      ))}
    </ul>
  );
};
```

### Improvement Suggestions

```tsx
const ImprovementSuggestions = ({ suggestions }: { suggestions: string[] }) => {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <h3 className="font-semibold text-blue-900 mb-2">💡 How to Improve</h3>
      <ul className="space-y-1">
        {suggestions.map((suggestion, idx) => (
          <li key={idx} className="text-sm text-blue-800">
            • {suggestion}
          </li>
        ))}
      </ul>
    </div>
  );
};
```

### Complete Explanation Panel

```tsx
const ExplanationPanel = ({ requestId }: { requestId: string }) => {
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetch(`/api/v1/explain/${requestId}`)
      .then(r => r.json())
      .then(data => {
        setExplanation(data);
        setLoading(false);
      });
  }, [requestId]);
  
  if (loading) return <div>Loading explanation...</div>;
  if (!explanation) return <div>Explanation not available</div>;
  
  return (
    <div className="space-y-6">
      {/* Risk Band */}
      <div>
        <RiskBandBadge riskBand={explanation.risk_band} />
        <p className="text-sm text-gray-600 mt-1">
          {explanation.risk_band_description}
        </p>
      </div>
      
      {/* What Helped */}
      <div>
        <h3 className="font-semibold text-green-900 mb-2">✅ What Helped</h3>
        <FeatureList features={explanation.top_positive_features} />
      </div>
      
      {/* What Hurt */}
      <div>
        <h3 className="font-semibold text-red-900 mb-2">⚠️ What Hurt</h3>
        <FeatureList features={explanation.top_negative_features} />
      </div>
      
      {/* Improvement Suggestions */}
      <ImprovementSuggestions suggestions={explanation.how_to_improve} />
      
      {/* Disclaimer */}
      <p className="text-xs text-gray-500 border-t pt-4">
        {explanation.disclaimer}
      </p>
    </div>
  );
};
```

---

## 🎯 Best Practices

### 1. **Always Cache the Request ID**

```typescript
// After prediction, store request_id
localStorage.setItem(`explanation_${userId}`, prediction.request_id);

// Later, retrieve explanation
const requestId = localStorage.getItem(`explanation_${userId}`);
const explanation = await fetchExplanation(requestId);
```

### 2. **Handle Missing Explanations**

```typescript
const fetchExplanation = async (requestId: string) => {
  try {
    const response = await fetch(`/api/v1/explain/${requestId}`);
    
    if (response.status === 404) {
      return {
        error: "Explanation expired or not available",
        fallback: true
      };
    }
    
    return await response.json();
  } catch (error) {
    console.error("Explanation fetch failed:", error);
    return null;
  }
};
```

### 3. **Display Empty States Gracefully**

```typescript
{explanation.what_helped.length === 0 ? (
  <p className="text-gray-500">No specific positive factors identified</p>
) : (
  <FeatureList features={explanation.top_positive_features} />
)}
```

### 4. **Respect TTL (1 hour)**

```typescript
// Explanations expire after 1 hour
const EXPLANATION_TTL = 60 * 60 * 1000; // 1 hour in ms

const isExplanationExpired = (timestamp: number) => {
  return Date.now() - timestamp > EXPLANATION_TTL;
};
```

---

## 🔍 Example: Full Workflow

```typescript
// Step 1: Submit prediction
const submitPrediction = async (formData: FormData) => {
  const response = await fetch('/api/v1/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData)
  });
  
  const result = await response.json();
  
  // Step 2: Store request ID
  setRequestId(result.request_id);
  setPrediction(result.data);
  
  return result;
};

// Step 3: Fetch explanation (automatically or on user click)
const fetchExplanation = async (requestId: string) => {
  const response = await fetch(`/api/v1/explain/${requestId}`);
  
  if (!response.ok) {
    if (response.status === 404) {
      setError("Explanation not found or expired");
    } else {
      setError("Failed to load explanation");
    }
    return null;
  }
  
  const explanation = await response.json();
  setExplanation(explanation);
  
  return explanation;
};

// Step 4: Display in UI
return (
  <div>
    {/* Prediction Results */}
    <PredictionDisplay prediction={prediction} />
    
    {/* Explanation (collapsible) */}
    <Collapsible title="View Explanation">
      {explanation ? (
        <ExplanationPanel requestId={requestId} />
      ) : (
        <button onClick={() => fetchExplanation(requestId)}>
          Load Explanation
        </button>
      )}
    </Collapsible>
  </div>
);
```

---

## 🚨 Error Handling

### 404: Explanation Not Found

```typescript
if (response.status === 404) {
  return (
    <div className="text-yellow-800 bg-yellow-50 border border-yellow-200 p-4 rounded">
      ⚠️ Explanation has expired. Please re-run the prediction.
    </div>
  );
}
```

### 500: Server Error

```typescript
if (response.status === 500) {
  return (
    <div className="text-red-800 bg-red-50 border border-red-200 p-4 rounded">
      ❌ Server error. Please try again later.
    </div>
  );
}
```

---

## 📊 Data Visualization

### SHAP Value Chart (Optional)

```tsx
const SHAPChart = ({ features }: { features: FeatureContribution[] }) => {
  return (
    <div className="space-y-2">
      {features.map((feature, idx) => {
        const width = Math.abs(feature.shap_value) * 100;
        const isPositive = feature.impact === 'positive';
        
        return (
          <div key={idx}>
            <p className="text-sm font-medium">{feature.human_name}</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    isPositive ? 'bg-green-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${width}%` }}
                />
              </div>
              <span className="text-xs text-gray-600">{feature.magnitude}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
```

---

## ✅ Checklist for Integration

- [ ] Import TypeScript interfaces
- [ ] Implement fetchExplanation() function
- [ ] Add error handling for 404/500
- [ ] Display risk band badge
- [ ] Show top positive features
- [ ] Show top negative features
- [ ] Display improvement suggestions
- [ ] Include disclaimer (required for compliance)
- [ ] Handle loading state
- [ ] Handle empty states
- [ ] Test with expired explanations (> 1 hour)

---

## 🔗 API Reference

**Endpoint:** `GET /api/v1/explain/{prediction_id}`

**Parameters:**
- `prediction_id` (path): Request ID from `/api/v1/predict`

**Response Codes:**
- `200`: Success
- `404`: Explanation not found or expired
- `500`: Server error

**Example Request:**
```bash
curl http://localhost:8000/api/v1/explain/abc-123-def-456
```

**Example Response:**
```json
{
  "request_id": "abc-123-def-456",
  "model_version": "ml_v1.0.0",
  "risk_score": 0.25,
  "risk_band": "low",
  "risk_band_description": "Strong financial profile with minimal default risk",
  "top_positive_features": [...],
  "top_negative_features": [...],
  "what_helped": [...],
  "what_hurt": [...],
  "how_to_improve": [...],
  "disclaimer": "This assessment is advisory...",
  "status": "success"
}
```

---

**Need Help?** Check [PHASE_4D_EXPLAINABILITY_COMPLETE.md](./PHASE_4D_EXPLAINABILITY_COMPLETE.md) for full documentation.
