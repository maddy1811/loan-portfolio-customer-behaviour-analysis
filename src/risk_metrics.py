"""Financial Risk and Portfolio Analytics Module.

Calculates key risk indicators, portfolio performance metrics, default rates,
and loss metrics across borrower segments following banking and credit risk standards.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np


def portfolio_kpis(df: pd.DataFrame) -> dict:
    """Calculate comprehensive macro KPIs across the entire loan portfolio."""
    total_loans = len(df)
    if total_loans == 0:
        return {}

    # Status distribution
    status_counts = df["loan_status"].value_counts(dropna=False).to_dict() if "loan_status" in df else {}
    fully_paid_count = status_counts.get("Fully Paid", 0)
    charged_off_count = status_counts.get("Charged Off", 0)
    current_count = status_counts.get("Current", 0)
    completed_loans = fully_paid_count + charged_off_count

    # Historical default rate on completed loans
    historical_default_rate = (charged_off_count / completed_loans) if completed_loans > 0 else np.nan
    # Portfolio-wide default share
    portfolio_default_rate = (charged_off_count / total_loans) if total_loans > 0 else np.nan

    kpis = {
        "total_loan_count": int(total_loans),
        "total_funded_amount": float(df["funded_amnt"].sum()) if "funded_amnt" in df else float(df.get("loan_amnt", pd.Series([0])).sum()),
        "total_loan_amount_requested": float(df["loan_amnt"].sum()) if "loan_amnt" in df else 0.0,
        "average_loan_amount": float(df["loan_amnt"].mean()) if "loan_amnt" in df else 0.0,
        "average_funded_amount": float(df["funded_amnt"].mean()) if "funded_amnt" in df else 0.0,
        "average_interest_rate_pct": float(df["int_rate"].mean()) if "int_rate" in df else 0.0,
        "average_dti": float(df["dti"].mean()) if "dti" in df else 0.0,
        "fully_paid_count": int(fully_paid_count),
        "fully_paid_pct": float(fully_paid_count / total_loans * 100),
        "charged_off_count": int(charged_off_count),
        "charged_off_pct": float(charged_off_count / total_loans * 100),
        "active_current_count": int(current_count),
        "active_current_pct": float(current_count / total_loans * 100),
        "completed_loan_count": int(completed_loans),
        "historical_default_rate_pct": float(historical_default_rate * 100) if pd.notna(historical_default_rate) else 0.0,
        "total_payments_received": float(df["total_pymnt"].sum()) if "total_pymnt" in df else 0.0,
        "total_principal_received": float(df["total_rec_prncp"].sum()) if "total_rec_prncp" in df else 0.0,
        "total_interest_received": float(df["total_rec_int"].sum()) if "total_rec_int" in df else 0.0,
        "total_recoveries_collected": float(df["recoveries"].sum()) if "recoveries" in df else 0.0,
        "total_net_credit_loss": float(df["net_credit_loss"].sum()) if "net_credit_loss" in df else 0.0,
        "overall_net_investor_gain": float(df["total_pymnt"].sum() - df["funded_amnt"].sum()) if {"total_pymnt", "funded_amnt"}.issubset(df.columns) else 0.0,
    }
    return kpis


def completed_loan_default_rate(df: pd.DataFrame) -> float:
    """Return historical default rate: Charged Off / (Charged Off + Fully Paid)."""
    if "loan_status" not in df:
        raise KeyError("loan_status column is missing from DataFrame")
    completed = df[df["loan_status"].isin(["Fully Paid", "Charged Off"])]
    if completed.empty:
        return float("nan")
    return float((completed["loan_status"] == "Charged Off").mean())


def default_rate_by_segment(df: pd.DataFrame, segment_col: str) -> pd.DataFrame:
    """Calculate completed-loan default rates, funded volume, and loss by segment."""
    if segment_col not in df.columns or "loan_status" not in df.columns:
        raise KeyError(f"Required columns missing: {segment_col}, loan_status")

    completed = df[df["loan_status"].isin(["Fully Paid", "Charged Off"])].copy()
    if completed.empty:
        return pd.DataFrame()

    completed["is_default"] = (completed["loan_status"] == "Charged Off").astype(int)

    agg_dict = {
        "loan_count": ("is_default", "count"),
        "charged_off_count": ("is_default", "sum"),
        "default_rate_pct": ("is_default", lambda s: round(s.mean() * 100, 2)),
    }
    if "funded_amnt" in completed.columns:
        agg_dict["total_funded_amount"] = ("funded_amnt", "sum")
        agg_dict["avg_funded_amount"] = ("funded_amnt", lambda s: round(s.mean(), 2))
    if "int_rate" in completed.columns:
        agg_dict["avg_interest_rate_pct"] = ("int_rate", lambda s: round(s.mean(), 2))
    if "net_credit_loss" in completed.columns:
        agg_dict["total_net_credit_loss"] = ("net_credit_loss", "sum")

    summary = completed.groupby(segment_col, dropna=False).agg(**agg_dict).reset_index()
    return summary.sort_values(by="default_rate_pct", ascending=False)


def loss_and_recovery_summary(df: pd.DataFrame) -> dict:
    """Analyze loss severity and recovery performance on defaulted loans."""
    charged_off = df[df["loan_status"] == "Charged Off"].copy()
    if charged_off.empty:
        return {}

    funded_co = charged_off["funded_amnt"].sum()
    prncp_co = charged_off["total_rec_prncp"].sum()
    shortfall = funded_co - prncp_co
    recoveries = charged_off["recoveries"].sum()
    net_loss = np.maximum(0.0, shortfall - recoveries)

    return {
        "charged_off_loans": len(charged_off),
        "defaulted_principal_funded": float(funded_co),
        "principal_repaid_prior_to_default": float(prncp_co),
        "gross_principal_shortfall": float(shortfall),
        "post_chargeoff_recoveries": float(recoveries),
        "net_unrecovered_credit_loss": float(net_loss),
        "portfolio_recovery_rate_pct": float((recoveries / shortfall * 100) if shortfall > 0 else 0.0),
        "loss_severity_pct": float((net_loss / funded_co * 100) if funded_co > 0 else 0.0),
    }


if __name__ == "__main__":
    import json
    cleaned_path = Path("data/processed/loans_cleaned.csv")
    if cleaned_path.exists():
        df_clean = pd.read_csv(cleaned_path, low_memory=False)
        print("=== MACRO PORTFOLIO KPIS ===")
        kpis = portfolio_kpis(df_clean)
        for k, v in kpis.items():
            if isinstance(v, float):
                print(f"  {k:<30}: {v:,.2f}")
            else:
                print(f"  {k:<30}: {v}")

        print("\n=== LOSS & RECOVERY PERFORMANCE ===")
        loss_perf = loss_and_recovery_summary(df_clean)
        for k, v in loss_perf.items():
            if isinstance(v, float):
                print(f"  {k:<32}: {v:,.2f}")
            else:
                print(f"  {k:<32}: {v}")

        print("\n=== DEFAULT RATE BY CREDIT GRADE ===")
        print(default_rate_by_segment(df_clean, "grade").to_string(index=False))
