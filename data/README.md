# Dataset Information

## Source
**Lending Club Loan Data**
- Original Size: 2,260,668 loan records
- Original Columns: 145 features
- Source File Size: 1.1 GB

## Preparation
The original dataset has been processed to match our feature schema:
- **Mapped Columns**: Transformed from Lending Club schema to our 11-feature schema
- **Derived Features**: Credit scores estimated from credit history factors
- **Sample Size**: 50,000 loans (randomly sampled with stratification)
- **Output File**: `data/raw/raw.csv` (3.4 MB)

## Data Characteristics

### Class Distribution
- **Default Rate**: 12.81%
- **Non-Default**: 43,596 loans (87.19%)
- **Default**: 6,404 loans (12.81%)

This reflects real-world loan portfolio characteristics with class imbalance.

### Features (11 input → 22 engineered)

**Numeric Features:**
1. `loan_amount` - Principal amount borrowed
2. `annual_income` - Borrower's annual income
3. `monthly_debt` - Monthly debt obligations
4. `credit_score` - Estimated credit score (300-850)
5. `loan_term_months` - Loan duration (12, 24, 36, 48, 60)
6. `employment_length_years` - Years at current employer
7. `number_of_open_accounts` - Open credit accounts
8. `delinquencies_2y` - Delinquencies in last 2 years
9. `inquiries_6m` - Credit inquiries in last 6 months

**Categorical Features:**
10. `home_ownership` - RENT, OWN, MORTGAGE
11. `purpose` - Loan purpose (debt_consolidation, home_improvement, etc.)

**Target Variable:**
- `default` - Binary indicator (0 = paid, 1 = defaulted)

## Column Mapping

Original Lending Club → Our Schema:
- `loan_amnt` → `loan_amount`
- `annual_inc` → `annual_income`
- `dti` + `annual_inc` → `monthly_debt` (calculated)
- `term` → `loan_term_months` (extracted numeric)
- `emp_length` → `employment_length_years` (parsed)
- `open_acc` → `number_of_open_accounts`
- `delinq_2yrs` → `delinquencies_2y`
- `inq_last_6mths` → `inquiries_6m`
- `home_ownership` → `home_ownership`
- `purpose` → `purpose`
- `loan_status` → `default` (binary: Charged Off, Default, Late → 1)
- Credit score estimated from multiple factors

## Data Quality

### Cleaning Steps
1. Removed 1,671 invalid records (0.07%)
2. Filtered for positive loan amounts and income
3. Validated loan terms (12, 24, 36, 48, 60 months only)
4. Mapped home ownership to valid categories
5. Capped credit history features to valid ranges:
   - `number_of_open_accounts`: 0-50
   - `delinquencies_2y`: 0-20
   - `inquiries_6m`: 0-20

### Missing Values
- Minimal missing values after cleaning
- Employment length: Filled with 0 for missing/n/a
- Credit history features: Filled with 0 for missing

## Usage

### Regenerate Dataset
To prepare the dataset from original Lending Club data:
```bash
python scripts/prepare_original_data.py
```

Options in script:
- `sample_size`: Number of records to sample (default: 50,000)
- `random_state`: Random seed for reproducibility (default: 42)
- Set `sample_size=None` to use all 2.26M records

### Training
```bash
python -m src.train
```

## Model Performance

With 50K samples:
- **Test Accuracy**: 70.49%
- **ROC AUC**: 62.77%
- **Recall**: 41.45% (catches 41% of defaults)
- **Precision**: 19.44% (19% of flagged loans actually default)

Performance reflects the challenging nature of credit risk prediction with imbalanced real-world data.

## Data Splits

Pipeline automatically creates:
- **Training**: 30,000 loans (60%)
- **Validation**: 10,000 loans (20%)
- **Test**: 10,000 loans (20%)

All splits maintain class distribution (stratified).

## Notes

1. **Credit Score Estimation**: Since credit scores aren't directly available in the Lending Club data, we estimate them using:
   - Base score: 650
   - Adjustments for: delinquencies, inquiries, open accounts, income
   - Random noise for realism
   - Clipped to 300-850 range

2. **Default Definition**: Based on loan_status:
   - Default: Charged Off, Default, Late (31-120 days), Late (16-30 days)
   - No Default: Current, Fully Paid, In Grace Period

3. **Sample Size**: 50K provides good balance between training speed and model quality. Increase for production.

4. **Data Privacy**: This is public Lending Club data. No personally identifiable information (PII) included.
