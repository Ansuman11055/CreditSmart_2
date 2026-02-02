"""Quick validation of production ML inference."""
from app.ml.model import get_model
from app.schemas.request import CreditRiskRequest

# Get model
model = get_model()

# Create request
request = CreditRiskRequest(
    annual_income=60000,
    monthly_debt=1200,
    credit_score=700,
    loan_amount=20000,
    loan_term_months=48,
    employment_length_years=4.0,
    home_ownership='MORTGAGE',
    purpose='car',
    number_of_open_accounts=5,
    delinquencies_2y=0,
    inquiries_6m=1
)

# Get prediction
response = model.predict(request)

print(f'Risk Score: {response.risk_score:.4f}')
print(f'Risk Level: {response.risk_level.value}')
print(f'Action: {response.recommended_action}')
print(f'Model: {response.model_version}')

# Get model info
info = model.get_model_info()
print(f'Engine: {info["model_type"]}')
print(f'Loaded: {info["is_loaded"]}')
