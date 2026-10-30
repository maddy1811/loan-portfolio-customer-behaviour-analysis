"""Empirical dataset inspection script for raw LendingClub loan.csv."""
from pathlib import Path
import pandas as pd
import numpy as np

def run_inspection():
    raw_path = Path("data/raw/loan.csv")
    if not raw_path.exists():
        print(f"File not found: {raw_path}")
        return

    df = pd.read_csv(raw_path, low_memory=False)
    print("=" * 60)
    print("1. EMPIRICAL DATASET DIMENSIONS")
    print(f"Total Observations (Rows): {df.shape[0]:,}")
    print(f"Total Variables (Columns):   {df.shape[1]:,}")
    print("=" * 60)

    print("\n2. DUPLICATE CHECK")
    print(f"Exact Duplicate Rows: {df.duplicated().sum():,}")
    if "id" in df.columns:
        print(f"Unique 'id': {df['id'].nunique():,}")
        print(f"Duplicate 'id': {df['id'].duplicated().sum():,}")
    if "member_id" in df.columns:
        print(f"Unique 'member_id': {df['member_id'].nunique():,}")
        print(f"Duplicate 'member_id': {df['member_id'].duplicated().sum():,}")

    print("\n3. LOAN STATUS DISTRIBUTION")
    status_counts = df["loan_status"].value_counts(dropna=False)
    status_pct = (df["loan_status"].value_counts(dropna=False, normalize=True) * 100).round(3)
    for s, c in status_counts.items():
        print(f"  - {s}: {c:,} ({status_pct[s]}%)")

    completed = df[df["loan_status"].isin(["Fully Paid", "Charged Off"])]
    historical_default_rate = (completed["loan_status"] == "Charged Off").mean()
    print(f"\nHistorical Completed Loans: {len(completed):,}")
    print(f"Completed-Loan Default Rate: {historical_default_rate:.4%}")

    print("\n4. MISSING VALUES DIAGNOSTICS")
    null_counts = df.isna().sum()
    all_null_cols = null_counts[null_counts == len(df)].index.tolist()
    print(f"Columns with 100% missing values: {len(all_null_cols)}")
    print(f"Example 100% empty columns: {all_null_cols[:10]}")
    
    partial_nulls = null_counts[(null_counts > 0) & (null_counts < len(df))].sort_values(ascending=False)
    print(f"\nColumns with partial missing values ({len(partial_nulls)}):")
    for col, count in partial_nulls.items():
        pct = (count / len(df)) * 100
        print(f"  - {col}: {count:,} ({pct:.2f}%)")

    print("\n5. KEY FINANCIAL & RISK VARIABLES PREVIEW")
    core_cols = [
        "loan_amnt", "funded_amnt", "funded_amnt_inv", "term", "int_rate",
        "installment", "grade", "sub_grade", "emp_length", "home_ownership",
        "annual_inc", "verification_status", "issue_d", "loan_status", "purpose",
        "dti", "delinq_2yrs", "inq_last_6mths", "open_acc", "pub_rec", "revol_bal",
        "revol_util", "total_acc", "total_pymnt", "total_rec_prncp", "total_rec_int",
        "recoveries", "collection_recovery_fee"
    ]
    existing_core = [c for c in core_cols if c in df.columns]
    print(f"Core analysis columns present: {len(existing_core)} / {len(core_cols)}")
    missing_core = set(core_cols) - set(existing_core)
    if missing_core:
        print(f"Missing core columns: {missing_core}")

    print("\nData Types of Core Columns:")
    for col in existing_core:
        sample_val = df[col].dropna().iloc[0] if not df[col].dropna().empty else "None"
        print(f"  {col:<25} dtype: {str(df[col].dtype):<10} sample: {sample_val}")

    print("\n6. SUMMARY STATISTICS OF CORE NUMERICALS")
    num_sub = df[["loan_amnt", "funded_amnt", "annual_inc", "dti", "total_pymnt", "total_rec_prncp", "recoveries"]]
    print(num_sub.describe().T[["count", "mean", "std", "min", "50%", "max"]])

if __name__ == "__main__":
    run_inspection()
