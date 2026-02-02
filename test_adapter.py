"""Test script for the new /api/v1/risk-analysis adapter endpoint.

Validates that the frontend-compatible endpoint works correctly.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Frontend-style data (5 fields only)
frontend_input = {
    "annualIncome": 85000,
    "monthlyDebt": 1200,
    "creditScore": 720,
    "loanAmount": 25000,
    "employmentYears": 5
}

print("╔═══════════════════════════════════════════════════════════════╗")
print("║  TESTING FRONTEND ADAPTER ENDPOINT                            ║")
print("║  POST /api/v1/risk-analysis                                   ║")
print("╚═══════════════════════════════════════════════════════════════╝\n")

print("Frontend Input (5 fields):")
print(json.dumps(frontend_input, indent=2))
print()

try:
    response = requests.post(
        f"{BASE_URL}/risk-analysis",
        json=frontend_input,
        timeout=15
    )
    
    print(f"Response Status: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print("✓ SUCCESS - Frontend-Compatible Response:")
        print(json.dumps(data, indent=2))
        print()
        
        # Verify structure
        required_fields = ["score", "riskLevel", "summary", "factors", "recommendation"]
        has_all_fields = all(field in data for field in required_fields)
        
        if has_all_fields:
            print("✓ All required fields present:")
            print(f"  - score: {data['score']}")
            print(f"  - riskLevel: {data['riskLevel']}")
            print(f"  - summary: {data['summary'][:80]}...")
            print(f"  - factors: {len(data['factors'])} factors")
            print(f"  - recommendation: {data['recommendation'][:80]}...")
        else:
            print("✗ Missing required fields!")
            
    else:
        print("✗ FAILED - Error Response:")
        print(response.text)
        
except requests.exceptions.RequestException as e:
    print(f"✗ Connection Error: {e}")
    print("\nMake sure backend is running:")
    print("  uvicorn app.main:app --port 8000")
