"""
Script to prepare original Lending Club dataset for training pipeline.
Maps original columns to expected feature schema.
"""
import pandas as pd
import numpy as np
from pathlib import Path


def map_loan_status_to_default(status: str) -> int:
    """Map loan status to binary default indicator."""
    default_statuses = [
        'Charged Off',
        'Default',
        'Does not meet the credit policy. Status:Charged Off',
        'Late (31-120 days)',
        'Late (16-30 days)'
    ]
    return 1 if status in default_statuses else 0


def parse_employment_length(emp_length: str) -> float:
    """Parse employment length string to years."""
    if pd.isna(emp_length) or emp_length == 'n/a':
        return 0.0
    
    emp_length = str(emp_length).strip()
    
    if '< 1 year' in emp_length:
        return 0.5
    elif '10+ years' in emp_length:
        return 10.0
    elif 'year' in emp_length:
        # Extract number from strings like "2 years", "3 years"
        try:
            return float(emp_length.split()[0])
        except:
            return 0.0
    else:
        return 0.0


def prepare_data(
    input_path: str = "data/raw/raw_original.csv",
    output_path: str = "data/raw/raw.csv",
    sample_size: int = None,
    random_state: int = 42
):
    """
    Prepare original dataset for training pipeline.
    
    Args:
        input_path: Path to original CSV file
        output_path: Path to save prepared data
        sample_size: Optional sample size (None = use all data)
        random_state: Random state for sampling
    """
    print(f"Loading data from {input_path}...")
    
    # Read in chunks to handle large file
    chunk_size = 100000
    chunks = []
    total_rows = 0
    
    for chunk in pd.read_csv(input_path, chunksize=chunk_size, low_memory=False):
        total_rows += len(chunk)
        chunks.append(chunk)
        print(f"  Loaded {total_rows:,} rows...", end='\r')
    
    df = pd.concat(chunks, ignore_index=True)
    print(f"\nLoaded {len(df):,} records with {len(df.columns)} columns")
    
    # Map columns to expected schema
    print("\nMapping columns to schema...")
    mapped_df = pd.DataFrame()
    
    # Direct mappings
    mapped_df['loan_amount'] = df['loan_amnt']
    mapped_df['annual_income'] = df['annual_inc']
    mapped_df['home_ownership'] = df['home_ownership']
    mapped_df['purpose'] = df['purpose']
    
    # Derived mappings
    mapped_df['credit_score'] = np.nan  # Not directly available, will need to derive
    mapped_df['monthly_debt'] = (df['dti'] / 100) * (df['annual_inc'] / 12)  # From debt-to-income ratio
    mapped_df['employment_length_years'] = df['emp_length'].apply(parse_employment_length)
    
    # Term in months (from " 36 months" or " 60 months")
    mapped_df['loan_term_months'] = df['term'].str.extract(r'(\d+)').astype(float)
    
    # Credit history features (clip to valid ranges per schema)
    mapped_df['number_of_open_accounts'] = np.clip(df['open_acc'].fillna(0), 0, 50).astype(int)
    mapped_df['delinquencies_2y'] = np.clip(df['delinq_2yrs'].fillna(0), 0, 20).astype(int)
    mapped_df['inquiries_6m'] = np.clip(df['inq_last_6mths'].fillna(0), 0, 20).astype(int)
    
    # Target variable
    mapped_df['default'] = df['loan_status'].apply(map_loan_status_to_default)
    
    print("Column mapping complete")
    print(f"  Mapped {len(mapped_df.columns)} columns")
    
    # Handle missing credit scores - derive from other credit factors
    print("\nDeriving credit scores...")
    # Simple credit score estimation based on available factors
    # This is a rough approximation for demonstration purposes
    base_score = 650
    
    # Adjust based on delinquencies (negative impact)
    delinq_penalty = mapped_df['delinquencies_2y'] * 30
    
    # Adjust based on inquiries (negative impact)
    inquiry_penalty = mapped_df['inquiries_6m'] * 10
    
    # Adjust based on open accounts (positive impact if moderate)
    account_bonus = np.clip(mapped_df['number_of_open_accounts'] * 5, 0, 50)
    
    # Adjust based on income (positive impact)
    income_bonus = np.clip(mapped_df['annual_income'] / 10000 * 5, 0, 100)
    
    # Combine factors
    estimated_score = base_score - delinq_penalty - inquiry_penalty + account_bonus + income_bonus
    
    # Add some noise for realism
    np.random.seed(random_state)
    noise = np.random.normal(0, 20, len(mapped_df))
    estimated_score = estimated_score + noise
    
    # Handle NaN values
    estimated_score = estimated_score.fillna(650)
    
    # Clip to valid range
    mapped_df['credit_score'] = np.clip(estimated_score, 300, 850).astype(int)
    
    # Clean data
    print("\nCleaning data...")
    initial_count = len(mapped_df)
    
    # Remove rows with missing critical values
    mapped_df = mapped_df.dropna(subset=['loan_amount', 'annual_income', 'home_ownership', 'purpose'])
    
    # Filter valid values
    mapped_df = mapped_df[mapped_df['loan_amount'] > 0]
    mapped_df = mapped_df[mapped_df['annual_income'] > 0]
    mapped_df = mapped_df[mapped_df['loan_term_months'].isin([12, 24, 36, 48, 60])]
    
    # Map home_ownership to valid values
    home_ownership_map = {
        'RENT': 'RENT',
        'OWN': 'OWN',
        'MORTGAGE': 'MORTGAGE',
        'ANY': 'OWN',
        'NONE': 'RENT',
        'OTHER': 'RENT'
    }
    mapped_df['home_ownership'] = mapped_df['home_ownership'].map(home_ownership_map).fillna('RENT')
    
    # Map purpose to valid values
    valid_purposes = ['debt_consolidation', 'home_improvement', 'major_purchase', 'medical', 
                      'business', 'car', 'vacation', 'wedding', 'moving', 'other']
    mapped_df.loc[~mapped_df['purpose'].isin(valid_purposes), 'purpose'] = 'other'
    
    cleaned_count = len(mapped_df)
    print(f"  Removed {initial_count - cleaned_count:,} invalid rows")
    print(f"  Remaining: {cleaned_count:,} rows")
    
    # Sample if requested
    if sample_size and sample_size < len(mapped_df):
        print(f"\nSampling {sample_size:,} rows...")
        mapped_df = mapped_df.sample(n=sample_size, random_state=random_state)
    
    # Check class distribution
    default_rate = mapped_df['default'].mean()
    print(f"\nDataset statistics:")
    print(f"  Total records: {len(mapped_df):,}")
    print(f"  Default rate: {default_rate:.2%}")
    print(f"  Default=0: {(mapped_df['default']==0).sum():,} ({(1-default_rate):.2%})")
    print(f"  Default=1: {(mapped_df['default']==1).sum():,} ({default_rate:.2%})")
    
    # Save
    print(f"\nSaving to {output_path}...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    mapped_df.to_csv(output_path, index=False)
    print("Done!")
    
    return mapped_df


if __name__ == "__main__":
    # Prepare data with reasonable sample size for training
    # Use sample_size=None to use all data (will be slower)
    df = prepare_data(
        input_path="data/raw/raw_original.csv",
        output_path="data/raw/raw.csv",
        sample_size=50000,  # Use 50k samples for faster training
        random_state=42
    )
