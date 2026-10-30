"""Comprehensive Unit and Financial Validation Test Suite.

Validates data integrity, accounting formulas, mathematical consistency,
and credit risk rules across LendingClub portfolio analytics.
"""
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

PROCESSED_DATA_PATH = Path("data/processed/loans_cleaned.csv")
COMPLETED_DATA_PATH = Path("data/processed/loans_completed_for_default_analysis.csv")


@pytest.fixture(scope="session")
def cleaned_df() -> pd.DataFrame:
    assert PROCESSED_DATA_PATH.exists(), f"Processed data missing at {PROCESSED_DATA_PATH}"
    return pd.read_csv(PROCESSED_DATA_PATH, low_memory=False)


@pytest.fixture(scope="session")
def completed_df() -> pd.DataFrame:
    assert COMPLETED_DATA_PATH.exists(), f"Completed data missing at {COMPLETED_DATA_PATH}"
    return pd.read_csv(COMPLETED_DATA_PATH, low_memory=False)


class TestDataIntegrity:
    def test_row_count_and_keys(self, cleaned_df):
        """Ensure full portfolio volume matches audited benchmark and primary keys are unique."""
        assert len(cleaned_df) == 39717, f"Expected 39,717 rows, got {len(cleaned_df)}"
        assert cleaned_df["id"].nunique() == 39717, "Duplicate loan IDs detected!"
        assert cleaned_df["member_id"].nunique() == 39717, "Duplicate member IDs detected!"

    def test_status_distribution(self, cleaned_df):
        """Verify exact ground-truth loan status counts."""
        status_counts = cleaned_df["loan_status"].value_counts().to_dict()
        assert status_counts["Fully Paid"] == 32950
        assert status_counts["Charged Off"] == 5627
        assert status_counts["Current"] == 1140

    def test_no_nulls_in_critical_metrics(self, cleaned_df):
        """Core financial attributes must not contain missing values."""
        critical_cols = [
            "loan_amnt", "funded_amnt", "term_months", "int_rate",
            "installment", "grade", "annual_inc", "loan_status",
            "total_pymnt", "total_rec_prncp", "total_rec_int", "recoveries"
        ]
        for col in critical_cols:
            assert cleaned_df[col].isna().sum() == 0, f"Unexpected null values found in {col}"


class TestFinancialMathAndAccounting:
    def test_cashflow_balance(self, cleaned_df):
        """Total payments must closely equal the sum of principal, interest, late fees, and recoveries."""
        component_sum = (
            cleaned_df["total_rec_prncp"] +
            cleaned_df["total_rec_int"] +
            cleaned_df["total_rec_late_fee"] +
            cleaned_df["recoveries"]
        )
        diff = (cleaned_df["total_pymnt"] - component_sum).abs()
        # LendingClub total_pymnt aligns within minor floating point rounding
        assert (diff > 0.05).mean() < 0.001, "Significant discrepancy between total payments and cash components!"

    def test_net_credit_loss_accounting(self, cleaned_df):
        """Net credit loss must be exactly 0 for Fully Paid loans, and <= funded amount for defaults."""
        paid_loans = cleaned_df[cleaned_df["loan_status"] == "Fully Paid"]
        assert (paid_loans["net_credit_loss"] == 0).all(), "Non-zero net credit loss found in Fully Paid cohort!"

        default_loans = cleaned_df[cleaned_df["loan_status"] == "Charged Off"]
        assert (default_loans["net_credit_loss"] >= 0).all(), "Negative net credit loss found!"
        assert (default_loans["net_credit_loss"] <= default_loans["funded_amnt"]).all(), "Net loss exceeds funded amount!"

    def test_investor_gain_loss(self, cleaned_df):
        """Net investor gain/loss must equal total payments minus funded amount."""
        expected_gain = cleaned_df["total_pymnt"] - cleaned_df["funded_amnt"]
        diff = (cleaned_df["net_investor_gain_loss"] - expected_gain).abs()
        assert (diff > 1e-4).sum() == 0, "Discrepancy in net investor gain/loss calculation!"


class TestCreditRiskAndDefaultRules:
    def test_default_flag_exclusion_of_current_loans(self, cleaned_df):
        """Crucial risk rule: default_flag must be NaN for active/Current loans."""
        current_loans = cleaned_df[cleaned_df["loan_status"] == "Current"]
        assert current_loans["default_flag"].isna().all(), "Active/Current loans must NOT have default_flag 0 or 1!"

        completed = cleaned_df[cleaned_df["loan_status"].isin(["Fully Paid", "Charged Off"])]
        assert completed["default_flag"].isna().sum() == 0, "Completed loans must have non-null default_flag!"

    def test_historical_default_rate_calculation(self, completed_df):
        """Completed loans cohort must have default rate strictly equal to 14.5864%."""
        assert len(completed_df) == 38577
        rate = (completed_df["loan_status"] == "Charged Off").mean() * 100
        assert round(rate, 4) == 14.5864

    def test_monotonic_credit_risk_by_grade(self, completed_df):
        """Credit default rates must increase monotonically across credit grades A -> B -> C -> D -> E -> F/G."""
        rates = completed_df.groupby("grade")["default_flag"].mean()
        assert rates["A"] < rates["B"], "Grade B default rate must exceed Grade A"
        assert rates["B"] < rates["C"], "Grade C default rate must exceed Grade B"
        assert rates["C"] < rates["D"], "Grade D default rate must exceed Grade C"
        assert rates["D"] < rates["E"], "Grade E default rate must exceed Grade D"
        assert rates["E"] < rates["F"], "Grade F default rate must exceed Grade E"


class TestFeatureEngineeringIntegrity:
    def test_loan_to_income_safety(self, cleaned_df):
        """No infinite or negative loan-to-income values."""
        valid_lti = cleaned_df["loan_to_income_ratio"].dropna()
        assert (valid_lti < 0).sum() == 0, "Negative LTI found"
        assert not np.isinf(valid_lti).any(), "Infinite LTI found (division by zero)"

    def test_tenure_and_term_cleaning(self, cleaned_df):
        """Terms must be either 36 or 60 months."""
        assert set(cleaned_df["term_months"].dropna().unique()) == {36, 60}
        assert set(cleaned_df["term_clean"].unique()) == {"36 months", "60 months"}
