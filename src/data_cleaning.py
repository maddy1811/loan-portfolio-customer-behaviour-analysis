"""Production-grade Data Cleaning and Feature Engineering for LendingClub Loan Data.

This module cleans raw LendingClub loan portfolio data, handles missing values,
parses string-formatted percentages, normalizes employment tenure, parses dates,
conducts outlier treatment, and engineers credit risk features.

All calculations follow institutional financial risk and accounting definitions.
The original raw dataset is treated as immutable and never modified.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd


# 1. Percentages and Numerics
PERCENT_COLUMNS = ["int_rate", "revol_util"]

NUMERIC_COLUMNS = [
    "loan_amnt", "funded_amnt", "funded_amnt_inv", "installment",
    "annual_inc", "dti", "delinq_2yrs", "inq_last_6mths", "open_acc",
    "pub_rec", "revol_bal", "total_acc", "out_prncp", "out_prncp_inv",
    "total_pymnt", "total_pymnt_inv", "total_rec_prncp", "total_rec_int",
    "total_rec_late_fee", "recoveries", "collection_recovery_fee",
    "last_pymnt_amnt", "pub_rec_bankruptcies"
]

EMP_LENGTH_MAP = {
    "< 1 year": 0,
    "1 year": 1,
    "2 years": 2,
    "3 years": 3,
    "4 years": 4,
    "5 years": 5,
    "6 years": 6,
    "7 years": 7,
    "8 years": 8,
    "9 years": 9,
    "10+ years": 10
}


def parse_percent(series: pd.Series) -> pd.Series:
    """Convert string percentage values (e.g. '10.65%') to float numbers (10.65)."""
    return pd.to_numeric(
        series.astype("string").str.replace("%", "", regex=False).str.strip(),
        errors="coerce"
    )


def clean_loans(input_path: str | Path) -> tuple[pd.DataFrame, dict]:
    """Execute complete data cleaning, preprocessing, and feature engineering.
    
    Args:
        input_path: Path to the raw loan.csv file.
        
    Returns:
        tuple containing the cleaned DataFrame and the data quality audit dictionary.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Source dataset not found at: {input_path}")

    # Load raw data without schema assumptions
    df = pd.read_csv(input_path, low_memory=False)
    original_shape = df.shape
    df.columns = [str(c).strip().lower() for c in df.columns]

    # --- Step 1: Duplicate Audit ---
    duplicate_rows = int(df.duplicated().sum())
    unique_ids = int(df["id"].nunique()) if "id" in df.columns else len(df)
    duplicate_ids = int(df["id"].duplicated().sum()) if "id" in df.columns else 0
    if duplicate_rows > 0:
        df = df.drop_duplicates().copy()

    # --- Step 2: Pruning Zero-Variance & 100% Null Columns ---
    null_counts = df.isna().sum()
    all_null_cols = null_counts[null_counts == len(df)].index.tolist()
    
    # Identify constant single-value columns (zero analytical variance)
    single_val_cols = [c for c in df.columns if df[c].nunique(dropna=False) == 1 and c not in all_null_cols]
    
    cols_to_drop = list(set(all_null_cols + single_val_cols))
    # Also drop free-text URL and unstructured long text columns to optimize memory
    for optional_drop in ["url", "desc"]:
        if optional_drop in df.columns and optional_drop not in cols_to_drop:
            cols_to_drop.append(optional_drop)
            
    df = df.drop(columns=cols_to_drop, errors="ignore").copy()

    # --- Step 3: Type Conversions ---
    for col in PERCENT_COLUMNS:
        if col in df.columns:
            df[col] = parse_percent(df[col])

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Clean loan term into integer months and standardized category
    if "term" in df.columns:
        term_str = df["term"].astype("string").str.strip()
        df["term_months"] = pd.to_numeric(term_str.str.extract(r"(\d+)")[0], errors="coerce").astype("Int64")
        df["term_clean"] = df["term_months"].apply(lambda m: f"{m} months" if pd.notna(m) else "Unknown")

    # Normalize employment length
    if "emp_length" in df.columns:
        emp_clean = df["emp_length"].astype("string").str.strip()
        df["emp_length_years"] = emp_clean.map(EMP_LENGTH_MAP).astype("Float64")
        
        # Categorical tenure bands via pd.cut
        df["emp_length_band"] = pd.cut(
            df["emp_length_years"].astype(float),
            bins=[-0.1, 0.9, 3.1, 6.1, 9.1, 10.1],
            labels=["< 1 year", "1-3 years", "4-6 years", "7-9 years", "10+ years"]
        ).astype("string").fillna("Missing / Unreported")

    # Clean home ownership (standardize rare 'NONE' into 'OTHER')
    if "home_ownership" in df.columns:
        df["home_ownership"] = df["home_ownership"].astype("string").str.strip().str.upper()
        df["home_ownership_clean"] = df["home_ownership"].replace({"NONE": "OTHER"})

    # --- Step 4: Date Parsing & Vintage Attributes ---
    if "issue_d" in df.columns:
        df["issue_date"] = pd.to_datetime(df["issue_d"].astype("string"), format="%b-%y", errors="coerce")
        missing_issue_dates = df["issue_date"].isna()
        if missing_issue_dates.any():
            df.loc[missing_issue_dates, "issue_date"] = pd.to_datetime(
                df.loc[missing_issue_dates, "issue_d"], errors="coerce"
            )
        df["issue_year"] = df["issue_date"].dt.year.astype("Int64")
        df["issue_month"] = df["issue_date"].dt.month.astype("Int64")
        df["issue_year_month"] = df["issue_date"].dt.strftime("%Y-%m")
        df["issue_quarter"] = df["issue_date"].dt.to_period("Q").astype(str)

    # Parse earliest credit line date and calculate borrower credit history length
    if "earliest_cr_line" in df.columns:
        df["earliest_cr_date"] = pd.to_datetime(df["earliest_cr_line"].astype("string"), format="%b-%y", errors="coerce")
        missing_cr_dates = df["earliest_cr_date"].isna()
        if missing_cr_dates.any():
            df.loc[missing_cr_dates, "earliest_cr_date"] = pd.to_datetime(
                df.loc[missing_cr_dates, "earliest_cr_line"], errors="coerce"
            )
        # Handle century cutoff issue if 68 is parsed as 2068
        if "issue_date" in df.columns:
            mask_future = df["earliest_cr_date"] > df["issue_date"]
            df.loc[mask_future, "earliest_cr_date"] = df.loc[mask_future, "earliest_cr_date"] - pd.DateOffset(years=100)
            df["credit_history_years"] = np.round(
                (df["issue_date"] - df["earliest_cr_date"]).dt.days / 365.25, 1
            )

    # --- Step 5: Feature Engineering ---
    # Loan-to-Income Ratio (LTI)
    if "loan_amnt" in df.columns and "annual_inc" in df.columns:
        df["loan_to_income_ratio"] = np.where(
            df["annual_inc"] > 0,
            np.round(df["loan_amnt"] / df["annual_inc"], 4),
            np.nan
        )
        df["lti_band"] = pd.cut(
            df["loan_to_income_ratio"],
            bins=[-0.01, 0.15, 0.25, 0.35, 10.0],
            labels=["Low (< 15%)", "Moderate (15% - 25%)", "Elevated (25% - 35%)", "High (>= 35%)"]
        ).astype("string").fillna("Unknown")

    # Annual Income Bands & Outlier Treatment
    if "annual_inc" in df.columns:
        income_p995 = float(df["annual_inc"].quantile(0.995))
        df["is_high_income_outlier"] = df["annual_inc"] > income_p995
        
        df["income_band"] = pd.cut(
            df["annual_inc"],
            bins=[-0.01, 39999.99, 74999.99, 99999.99, 149999.99, 1e9],
            labels=["< $40,000", "$40,000 - $75,000", "$75,000 - $100,000", "$100,000 - $150,000", ">= $150,000"]
        ).astype("string").fillna("Unknown")

    # Interest Rate Bands
    if "int_rate" in df.columns:
        df["int_rate_band"] = pd.cut(
            df["int_rate"],
            bins=[-0.01, 9.99, 12.99, 15.99, 100.0],
            labels=["Low (< 10%)", "Moderate (10% - 13%)", "High (13% - 16%)", "Very High (>= 16%)"]
        ).astype("string").fillna("Unknown")

    # DTI Bands
    if "dti" in df.columns:
        df["dti_band"] = pd.cut(
            df["dti"],
            bins=[-0.01, 9.99, 19.99, 100.0],
            labels=["Low (< 10%)", "Moderate (10% - 20%)", "High (>= 20%)"]
        ).astype("string").fillna("Unknown")

    # Customer Risk Tier based on Credit Grade
    if "grade" in df.columns:
        grade = df["grade"].astype("string").str.upper().str.strip()
        df["customer_risk_tier"] = "Unknown"
        df.loc[grade.isin(["A", "B"]), "customer_risk_tier"] = "Prime"
        df.loc[grade.isin(["C", "D"]), "customer_risk_tier"] = "Near-Prime"
        df.loc[grade.isin(["E", "F", "G"]), "customer_risk_tier"] = "Subprime"

    # Loan Status, Default Flag & Outcome Cohorts
    if "loan_status" in df.columns:
        status = df["loan_status"].astype("string").str.strip()
        df["loan_status"] = status
        
        # default_flag is defined ONLY for completed loans; Current/Active loans remain NA
        default_map = {"Charged Off": 1, "Fully Paid": 0}
        df["default_flag"] = status.map(default_map).astype("Int64")
        
        df["outcome_group"] = "Other"
        df.loc[status == "Fully Paid", "outcome_group"] = "Completed - Paid"
        df.loc[status == "Charged Off", "outcome_group"] = "Completed - Default"
        df.loc[status == "Current", "outcome_group"] = "Active - In Progress"

    # --- Step 6: Financial Risk & Cashflow Loss Formulations ---
    if {"funded_amnt", "total_rec_prncp", "recoveries", "total_pymnt"}.issubset(df.columns):
        # Principal shortfall prior to recoveries
        shortfall = np.maximum(0.0, df["funded_amnt"] - df["total_rec_prncp"])
        df["principal_shortfall"] = np.where(df["loan_status"] == "Charged Off", shortfall, 0.0)
        
        # Net Credit Loss (post-recovery uncollected principal)
        net_loss = np.maximum(0.0, shortfall - df["recoveries"])
        df["net_credit_loss"] = np.where(df["loan_status"] == "Charged Off", net_loss, 0.0)
        
        # Recovery Rate (%) on defaulted principal
        df["recovery_rate_pct"] = np.where(
            (df["loan_status"] == "Charged Off") & (df["principal_shortfall"] > 0),
            np.clip((df["recoveries"] / df["principal_shortfall"]) * 100, 0.0, 100.0),
            np.nan
        )
        
        # Net Investor Return (Total cash collected minus funded capital)
        df["net_investor_gain_loss"] = df["total_pymnt"] - df["funded_amnt"]

    # --- Step 7: Completed Loans Sub-dataset ---
    completed_df = df[df["loan_status"].isin(["Fully Paid", "Charged Off"])].copy()

    # --- Step 8: Comprehensive Quality & Transformation Audit ---
    report = {
        "source_file": str(input_path),
        "rows_before": int(original_shape[0]),
        "columns_before": int(original_shape[1]),
        "rows_after_exact_deduplication": int(df.shape[0]),
        "exact_duplicate_rows_removed": duplicate_rows,
        "loan_status_counts": df["loan_status"].value_counts().to_dict(),
        "raw_dimensions": {
            "rows": int(original_shape[0]),
            "columns": int(original_shape[1])
        },
        "cleaned_dimensions": {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1])
        },
        "deduplication_audit": {
            "exact_duplicate_rows_removed": duplicate_rows,
            "unique_loan_ids": unique_ids,
            "duplicate_loan_ids": duplicate_ids
        },
        "pruned_uninformative_columns": {
            "count": len(cols_to_drop),
            "columns": cols_to_drop
        },
        "portfolio_composition": {
            "total_loans": int(len(df)),
            "status_counts": df["loan_status"].value_counts().to_dict(),
            "status_percentages": (df["loan_status"].value_counts(normalize=True) * 100).round(3).to_dict()
        },
        "completed_loans_audit": {
            "completed_loans_count": int(len(completed_df)),
            "fully_paid_count": int((completed_df["loan_status"] == "Fully Paid").sum()),
            "charged_off_count": int((completed_df["loan_status"] == "Charged Off").sum()),
            "historical_default_rate_pct": round(float((completed_df["loan_status"] == "Charged Off").mean() * 100), 4)
        },
        "financial_exposure_audit": {
            "total_portfolio_funded_usd": round(float(df["funded_amnt"].sum()), 2),
            "total_payments_collected_usd": round(float(df["total_pymnt"].sum()), 2),
            "total_principal_recovered_usd": round(float(df["total_rec_prncp"].sum()), 2),
            "total_interest_earned_usd": round(float(df["total_rec_int"].sum()), 2),
            "total_recoveries_collected_usd": round(float(df["recoveries"].sum()), 2),
            "total_net_credit_loss_usd": round(float(df["net_credit_loss"].sum()), 2)
        },
        "missing_values_after_cleaning": df.isna().sum()[df.isna().sum() > 0].to_dict()
    }

    return df, report


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean and enrich LendingClub loan dataset.")
    parser.add_argument("--input", default="data/raw/loan.csv", help="Path to input raw CSV.")
    parser.add_argument("--output-dir", default="data/processed", help="Directory for output files.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading and processing dataset from {args.input}...")
    cleaned_df, audit_report = clean_loans(args.input)

    # Save complete cleaned portfolio dataset
    cleaned_path = output_dir / "loans_cleaned.csv"
    cleaned_df.to_csv(cleaned_path, index=False)
    print(f"-> Saved full cleaned dataset: {cleaned_path} ({len(cleaned_df):,} rows, {cleaned_df.shape[1]} cols)")

    # Save historical completed loans dataset for default analysis
    completed_df = cleaned_df[cleaned_df["loan_status"].isin(["Fully Paid", "Charged Off"])]
    completed_path = output_dir / "loans_completed_for_default_analysis.csv"
    completed_df.to_csv(completed_path, index=False)
    print(f"-> Saved completed-loans dataset: {completed_path} ({len(completed_df):,} rows)")

    # Save comprehensive audit report
    report_path = output_dir / "data_quality_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2)
    print(f"-> Saved audit report: {report_path}")

    print("\n" + "=" * 60)
    print("DATA QUALITY & CLEANING AUDIT SUMMARY")
    print(f"Total Rows:                   {audit_report['cleaned_dimensions']['rows']:,}")
    print(f"Total Columns Retained:       {audit_report['cleaned_dimensions']['columns']:,}")
    print(f"Columns Pruned (100% NaN/0-var): {audit_report['pruned_uninformative_columns']['count']:,}")
    print(f"Historical Default Rate:      {audit_report['completed_loans_audit']['historical_default_rate_pct']}%")
    print(f"Total Funded Exposure:        ${audit_report['financial_exposure_audit']['total_portfolio_funded_usd']:,.2f}")
    print(f"Total Payments Received:      ${audit_report['financial_exposure_audit']['total_payments_collected_usd']:,.2f}")
    print(f"Total Net Credit Loss:        ${audit_report['financial_exposure_audit']['total_net_credit_loss_usd']:,.2f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
