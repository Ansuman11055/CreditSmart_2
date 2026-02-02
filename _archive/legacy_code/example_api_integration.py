"""
API Integration Example
======================

This example shows how the preprocessing pipeline integrates with the FastAPI backend.

Scenario: User submits credit application via frontend → Backend processes with 
preprocessing pipeline → Returns risk score
"""

import pandas as pd
from src.preprocess import preprocess_inference_data, DataPreprocessor
from app.ml.inference import CreditRiskInferenceEngine

# ===========================
# 1. LOAD FITTED PIPELINE
# ===========================
# This happens once at server startup

preprocessor = DataPreprocessor(data_dir="data")

print("Loading preprocessing artifacts...")
try:
    preprocessor.load_pipeline()
    print("✓ Loaded preprocessing pipeline from models/preprocessor.joblib")
except FileNotFoundError as e:
    print(f"✗ Error: {e}")
    print("Please train the model first to generate preprocessing artifacts.")
    exit(1)

inference_engine = CreditRiskInferenceEngine()

print("✓ Loaded preprocessing pipeline and inference engine")


# ===========================
# 2. API REQUEST HANDLER
# ===========================
# This runs for each /predict request

def predict_risk(request_data: dict) -> dict:
    """
    Handle credit risk prediction request.
    
    Args:
        request_data: Dictionary from API request body
        
    Returns:
        Dictionary with risk score and explanation
    """
    
    # Step 1: Convert API request to DataFrame
    df_input = pd.DataFrame([request_data])
    
    print(f"API Request:")
    print(f"  annual_income: ${request_data['annual_income']:,.0f}")
    print(f"  credit_score: {request_data['credit_score']}")
    print(f"  loan_amount: ${request_data['loan_amount']:,.0f}")
    
    # Step 2: Preprocess using fitted pipeline
    X_processed = preprocess_inference_data(df_input, preprocessor)
    
    print(f"\nPreprocessed Features:")
    print(f"  Shape: {X_processed.shape}")
    print(f"  Features: {list(X_processed.columns)[:3]}... (16 total)")
    
    # Step 3: Run inference
    risk_score = inference_engine.predict(request_data)
    
    print(f"\nRisk Score: {risk_score:.3f}")
    
    # Step 4: Return response
    return {
        "risk_score": round(risk_score, 4),
        "risk_level": "HIGH" if risk_score > 0.5 else "MEDIUM" if risk_score > 0.3 else "LOW",
        "processed_features": len(X_processed.columns),
    }


# ===========================
# 3. EXAMPLE USAGE
# ===========================

# Low risk applicant
low_risk_applicant = {
    "annual_income": 120000,
    "monthly_debt": 1500,
    "credit_score": 780,
    "loan_amount": 25000,
    "loan_term_months": 48,
    "employment_length_years": 10,
    "home_ownership": "OWN",
    "purpose": "debt_consolidation",
    "number_of_open_accounts": 8,
    "delinquencies_2y": 0,
    "inquiries_6m": 1,
}

print("\n" + "="*60)
print("EXAMPLE 1: Low Risk Applicant")
print("="*60)
result = predict_risk(low_risk_applicant)
print(f"\n✓ Result: {result}")


# High risk applicant
high_risk_applicant = {
    "annual_income": 35000,
    "monthly_debt": 2000,
    "credit_score": 580,
    "loan_amount": 40000,
    "loan_term_months": 60,
    "employment_length_years": 0.5,
    "home_ownership": "RENT",
    "purpose": "major_purchase",
    "number_of_open_accounts": 15,
    "delinquencies_2y": 3,
    "inquiries_6m": 8,
}

print("\n" + "="*60)
print("EXAMPLE 2: High Risk Applicant")
print("="*60)
result = predict_risk(high_risk_applicant)
print(f"\n✓ Result: {result}")


# ===========================
# 4. BATCH PROCESSING
# ===========================

def predict_batch(requests: list) -> list:
    """
    Handle batch prediction requests.
    
    Args:
        requests: List of request dictionaries
        
    Returns:
        List of prediction results
    """
    
    # Convert all requests to DataFrame
    df_batch = pd.DataFrame(requests)
    
    # Preprocess batch (single pipeline call)
    X_batch = preprocess_inference_data(df_batch, preprocessor)
    
    # Run inference on batch
    results = []
    for i, request in enumerate(requests):
        risk_score = inference_engine.predict(request)
        results.append({
            "request_id": i,
            "risk_score": round(risk_score, 4),
            "risk_level": "HIGH" if risk_score > 0.5 else "MEDIUM" if risk_score > 0.3 else "LOW",
        })
    
    return results


print("\n" + "="*60)
print("EXAMPLE 3: Batch Processing")
print("="*60)

batch_requests = [low_risk_applicant, high_risk_applicant]
batch_results = predict_batch(batch_requests)

for result in batch_results:
    print(f"Request {result['request_id']}: {result['risk_level']} risk ({result['risk_score']})")


# ===========================
# 5. ERROR HANDLING
# ===========================

def predict_with_error_handling(request_data: dict) -> dict:
    """
    Predict with comprehensive error handling.
    """
    from src.core.validation import ValidationError
    
    try:
        # Validate request
        if not request_data:
            return {"error": "Empty request"}
        
        # Check required fields
        required_fields = [
            "annual_income", "monthly_debt", "credit_score",
            "loan_amount", "loan_term_months", "employment_length_years",
            "home_ownership", "purpose"
        ]
        
        missing_fields = [f for f in required_fields if f not in request_data]
        if missing_fields:
            return {"error": f"Missing required fields: {', '.join(missing_fields)}"}
        
        # Validate ranges
        if request_data["credit_score"] < 300 or request_data["credit_score"] > 850:
            return {"error": "credit_score must be between 300 and 850"}
        
        if request_data["annual_income"] < 0:
            return {"error": "annual_income must be positive"}
        
        # Preprocess and predict
        df_input = pd.DataFrame([request_data])
        X_processed = preprocess_inference_data(df_input, preprocessor)
        risk_score = inference_engine.predict(request_data)
        
        return {
            "success": True,
            "risk_score": round(risk_score, 4),
            "risk_level": "HIGH" if risk_score > 0.5 else "MEDIUM" if risk_score > 0.3 else "LOW",
        }
        
    except ValidationError as e:
        return {"error": f"Validation failed: {str(e)}"}
    
    except Exception as e:
        return {"error": f"Internal error: {str(e)}"}


print("\n" + "="*60)
print("EXAMPLE 4: Error Handling")
print("="*60)

# Invalid request (credit score out of range)
invalid_request = {
    **low_risk_applicant,
    "credit_score": 950,  # Invalid: max is 850
}

result = predict_with_error_handling(invalid_request)
print(f"Invalid request result: {result}")


# ===========================
# 6. PERFORMANCE METRICS
# ===========================

import time

def benchmark_prediction(n_requests: int = 100):
    """Benchmark prediction performance."""
    
    print(f"\nBenchmarking {n_requests} predictions...")
    
    requests = [low_risk_applicant.copy() for _ in range(n_requests)]
    
    # Time preprocessing
    start = time.time()
    df_batch = pd.DataFrame(requests)
    X_batch = preprocess_inference_data(df_batch, preprocessor)
    preprocess_time = time.time() - start
    
    # Time inference
    start = time.time()
    for request in requests:
        _ = inference_engine.predict(request)
    inference_time = time.time() - start
    
    total_time = preprocess_time + inference_time
    
    print(f"\nResults:")
    print(f"  Preprocessing: {preprocess_time*1000:.2f} ms ({preprocess_time/n_requests*1000:.2f} ms/request)")
    print(f"  Inference: {inference_time*1000:.2f} ms ({inference_time/n_requests*1000:.2f} ms/request)")
    print(f"  Total: {total_time*1000:.2f} ms ({total_time/n_requests*1000:.2f} ms/request)")
    print(f"  Throughput: {n_requests/total_time:.0f} requests/second")


print("\n" + "="*60)
print("EXAMPLE 5: Performance Benchmark")
print("="*60)
benchmark_prediction(100)


print("\n" + "="*60)
print("✓ All examples completed successfully!")
print("="*60)
