# API Endpoint Tests

## Test 1: Low Risk Applicant (Advisor)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/advisor \
  -H "Content-Type: application/json" \
  -d '{
    "annual_income": 75000,
    "monthly_debt": 1200,
    "credit_score": 720,
    "loan_amount": 25000,
    "loan_term_months": 60,
    "employment_length_years": 5,
    "home_ownership": "MORTGAGE",
    "purpose": "debt_consolidation",
    "number_of_open_accounts": 8,
    "delinquencies_2y": 0,
    "inquiries_6m": 1
  }'
```

Expected:
- Status: 200
- Assessment: "Strong financial position"
- Current score: ~0.20
- Potential score: ~0.18
- Few recommendations (mostly optimization)

## Test 2: High Risk Applicant (Advisor)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/advisor \
  -H "Content-Type: application/json" \
  -d '{
    "annual_income": 30000,
    "monthly_debt": 2000,
    "credit_score": 550,
    "loan_amount": 40000,
    "loan_term_months": 84,
    "employment_length_years": 0.5,
    "home_ownership": "RENT",
    "purpose": "other",
    "number_of_open_accounts": 15,
    "delinquencies_2y": 4,
    "inquiries_6m": 6
  }'
```

Expected:
- Status: 200
- Assessment: "High risk profile requiring immediate action"
- Current score: ~0.99
- Potential score: ~0.50
- Multiple HIGH priority recommendations
