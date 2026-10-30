"""Automated High-Resolution Financial Visualization Generator.

Generates institutional-quality visualizations for Loan Portfolio & Customer Behaviour
Analysis and saves them to the figures/ directory.
"""
from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Set global financial fintech styling
sns.set_theme(style="whitegrid", font="sans-serif")
plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 11,
    "figure.titlesize": 16,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight"
})

# Fintech Color Palette
PRIMARY = "#1E3A8A"      # Deep Navy
SECONDARY = "#0D9488"    # Teal Accent
DANGER = "#BE123C"       # Crimson / Default Red
SUCCESS = "#059669"      # Emerald / Paid Green
WARNING = "#D97706"      # Amber
NEUTRAL = "#4B5563"      # Cool Grey


def generate_all_figures(cleaned_data_path: str | Path, output_dir: str | Path) -> list[Path]:
    data_path = Path(cleaned_data_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path, low_memory=False)
    completed = df[df["loan_status"].isin(["Fully Paid", "Charged Off"])].copy()

    saved_paths = []

    # 1. Loan Amount Distribution
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(df["loan_amnt"], bins=35, kde=True, color=PRIMARY, ax=ax, edgecolor="white", alpha=0.7)
    mean_val = df["loan_amnt"].mean()
    median_val = df["loan_amnt"].median()
    ax.axvline(mean_val, color=DANGER, linestyle="--", linewidth=1.8, label=f"Mean: ${mean_val:,.0f}")
    ax.axvline(median_val, color=SECONDARY, linestyle="-", linewidth=1.8, label=f"Median: ${median_val:,.0f}")
    ax.set_title("Portfolio Loan Amount Distribution (Requested Capital)")
    ax.set_xlabel("Loan Amount (USD)")
    ax.set_ylabel("Number of Loans")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${int(x):,}"))
    ax.legend(frameon=True)
    p = out_dir / "01_loan_amount_distribution.png"
    plt.savefig(p)
    plt.close()
    saved_paths.append(p)

    # 2. Loan Purpose Distribution
    fig, ax = plt.subplots(figsize=(11, 6))
    purpose_summary = df.groupby("purpose")["funded_amnt"].agg(["count", "sum"]).sort_values("sum", ascending=True)
    bars = ax.barh(purpose_summary.index, purpose_summary["sum"] / 1e6, color=PRIMARY, alpha=0.85, edgecolor="none")
    ax.set_title("Total Funded Capital by Loan Purpose (in $ Millions)")
    ax.set_xlabel("Funded Amount ($ Millions)")
    ax.set_ylabel("Loan Purpose")
    for bar in bars:
        w = bar.get_width()
        ax.annotate(f"${w:.1f}M", xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points", ha="left", va="center", fontsize=9, weight="bold")
    ax.set_xlim(0, (purpose_summary["sum"].max() / 1e6) * 1.15)
    p = out_dir / "02_loan_purpose_distribution.png"
    plt.savefig(p)
    plt.close()
    saved_paths.append(p)

    # 3. Interest Rate Distribution by Credit Grade
    fig, ax = plt.subplots(figsize=(10, 5))
    grades = sorted(df["grade"].dropna().unique())
    sns.boxplot(data=df, x="grade", y="int_rate", order=grades, hue="grade", palette="mako", legend=False, ax=ax, width=0.6, fliersize=2)
    ax.set_title("Interest Rate Distribution Across Credit Grades (Risk-Based Pricing)")
    ax.set_xlabel("Credit Grade (Prime to Subprime)")
    ax.set_ylabel("Interest Rate (%)")
    p = out_dir / "03_interest_rate_distribution.png"
    plt.savefig(p)
    plt.close()
    saved_paths.append(p)

    # 4. Customer Income Distribution
    fig, ax = plt.subplots(figsize=(10, 5))
    # Cap display at 99th percentile for clean visualization while reporting true stats
    p99 = df["annual_inc"].quantile(0.99)
    inc_disp = df[df["annual_inc"] <= p99]["annual_inc"]
    sns.histplot(inc_disp, bins=40, kde=True, color=SECONDARY, ax=ax, edgecolor="white", alpha=0.7)
    mean_inc = df["annual_inc"].mean()
    median_inc = df["annual_inc"].median()
    ax.axvline(median_inc, color=PRIMARY, linestyle="-", linewidth=2, label=f"Median Income: ${median_inc:,.0f}")
    ax.axvline(mean_inc, color=DANGER, linestyle="--", linewidth=1.8, label=f"Mean Income: ${mean_inc:,.0f}")
    ax.set_title("Borrower Annual Income Distribution (Display Truncated at 99th Percentile)")
    ax.set_xlabel("Annual Income (USD)")
    ax.set_ylabel("Number of Borrowers")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${int(x):,}"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend()
    p = out_dir / "04_customer_income_segments.png"
    plt.savefig(p)
    plt.close()
    saved_paths.append(p)

    # 5. Employment Tenure Distribution
    fig, ax = plt.subplots(figsize=(10, 5))
    emp_order = ["< 1 year", "1-3 years", "4-6 years", "7-9 years", "10+ years", "Missing / Unreported"]
    emp_counts = df["emp_length_band"].value_counts().reindex(emp_order).fillna(0)
    bars = ax.bar(emp_counts.index, emp_counts.values, color=PRIMARY, alpha=0.85, edgecolor="none", width=0.55)
    ax.set_title("Borrower Employment Tenure Distribution")
    ax.set_xlabel("Employment Length Band")
    ax.set_ylabel("Number of Borrowers")
    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"{int(h):,}\n({h/len(df)*100:.1f}%)", xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, emp_counts.max() * 1.18)
    p = out_dir / "05_employment_tenure.png"
    plt.savefig(p)
    plt.close()
    saved_paths.append(p)

    # 6. Home Ownership Distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    home_counts = df["home_ownership_clean"].value_counts()
    bars = ax.bar(home_counts.index, home_counts.values, color=[PRIMARY, SECONDARY, WARNING, NEUTRAL], width=0.5)
    ax.set_title("Borrower Home Ownership Structure")
    ax.set_xlabel("Home Ownership Status")
    ax.set_ylabel("Number of Loans")
    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"{int(h):,} ({h/len(df)*100:.1f}%)", xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=10)
    ax.set_ylim(0, home_counts.max() * 1.15)
    p = out_dir / "06_home_ownership.png"
    plt.savefig(p)
    plt.close()
    saved_paths.append(p)

    # 7. Credit Grades & Subgrades
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), gridspec_kw={"width_ratios": [1, 2]})
    grade_counts = df["grade"].value_counts().reindex(grades).fillna(0)
    ax1.bar(grade_counts.index, grade_counts.values, color=PRIMARY, width=0.6)
    ax1.set_title("Loan Volume by Credit Grade")
    ax1.set_xlabel("Credit Grade")
    ax1.set_ylabel("Number of Loans")
    for x, y in enumerate(grade_counts.values):
        ax1.annotate(f"{int(y):,}", (x, y), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=9)

    subgrade_order = sorted(df["sub_grade"].dropna().unique())
    subgrade_counts = df["sub_grade"].value_counts().reindex(subgrade_order).fillna(0)
    ax2.bar(subgrade_counts.index, subgrade_counts.values, color=SECONDARY, width=0.7)
    ax2.set_title("Granular Subgrade Distribution (A1 - G5)")
    ax2.set_xlabel("Sub-Grade")
    ax2.set_xticks(range(len(subgrade_order)))
    ax2.set_xticklabels(subgrade_order, rotation=90, fontsize=8)
    p = out_dir / "07_credit_grades_subgrades.png"
    plt.savefig(p)
    plt.close()
    saved_paths.append(p)

    # 8. Debt-to-Income (DTI) Distribution
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(df["dti"], bins=30, kde=True, color="#4338CA", ax=ax, edgecolor="white", alpha=0.7)
    ax.axvline(20.0, color=DANGER, linestyle="--", linewidth=1.8, label="DTI Threshold Guideline (20%)")
    mean_dti = df["dti"].mean()
    ax.axvline(mean_dti, color=WARNING, linestyle="-", linewidth=1.8, label=f"Mean DTI: {mean_dti:.1f}%")
    ax.set_title("Borrower Debt-to-Income (DTI) Ratio Distribution")
    ax.set_xlabel("Debt-to-Income Ratio (%)")
    ax.set_ylabel("Number of Borrowers")
    ax.legend()
    p = out_dir / "08_debt_to_income_ratio.png"
    plt.savefig(p)
    plt.close()
    saved_paths.append(p)

    # 9. Default Rates by Loan Grade (Monotonic Risk Curve)
    fig, ax = plt.subplots(figsize=(10, 5))
    grade_risk = completed.groupby("grade").agg(
        total=("default_flag", "count"),
        defaults=("default_flag", "sum")
    ).reindex(grades)
    grade_risk["default_rate"] = (grade_risk["defaults"] / grade_risk["total"]) * 100

    bars = ax.bar(grade_risk.index, grade_risk["default_rate"], color=DANGER, alpha=0.85, width=0.55)
    ax.set_title("Historical Completed-Loan Default Rate by Credit Grade")
    ax.set_xlabel("Credit Grade (Prime -> Subprime)")
    ax.set_ylabel("Default Rate (%)")
    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"{h:.2f}%", xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=10, weight="bold")
    ax.set_ylim(0, grade_risk["default_rate"].max() * 1.2)
    p = out_dir / "09_default_rate_by_grade.png"
    plt.savefig(p)
    plt.close()
    saved_paths.append(p)

    # 10. Default Rates by Loan Purpose
    fig, ax = plt.subplots(figsize=(11, 6))
    purpose_risk = completed.groupby("purpose").agg(
        total=("default_flag", "count"),
        defaults=("default_flag", "sum")
    )
    purpose_risk["default_rate"] = (purpose_risk["defaults"] / purpose_risk["total"]) * 100
    purpose_risk = purpose_risk.sort_values("default_rate", ascending=True)

    bars = ax.barh(purpose_risk.index, purpose_risk["default_rate"], color=PRIMARY, alpha=0.85)
    overall_avg = (completed["default_flag"].mean()) * 100
    ax.axvline(overall_avg, color=DANGER, linestyle="--", linewidth=1.5, label=f"Portfolio Average: {overall_avg:.2f}%")
    ax.set_title("Historical Default Rate by Loan Purpose")
    ax.set_xlabel("Default Rate (%)")
    ax.set_ylabel("Loan Purpose")
    for bar in bars:
        w = bar.get_width()
        ax.annotate(f"{w:.2f}%", xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points", ha="left", va="center", fontsize=9, weight="bold")
    ax.set_xlim(0, purpose_risk["default_rate"].max() * 1.18)
    ax.legend(loc="lower right")
    p = out_dir / "10_default_rate_by_purpose.png"
    plt.savefig(p)
    plt.close()
    saved_paths.append(p)

    # 11. Default Rates by Employment Tenure
    fig, ax = plt.subplots(figsize=(10, 5))
    emp_risk = completed.groupby("emp_length_band").agg(
        total=("default_flag", "count"),
        defaults=("default_flag", "sum")
    ).reindex(emp_order).fillna(0)
    emp_risk["default_rate"] = (emp_risk["defaults"] / emp_risk["total"]) * 100

    bars = ax.bar(emp_risk.index, emp_risk["default_rate"], color="#0284C7", width=0.55)
    ax.axvline(overall_avg, color=DANGER, linestyle="--", linewidth=1.5)
    ax.set_title("Default Rate Across Employment Tenure Categories")
    ax.set_xlabel("Employment Tenure Band")
    ax.set_ylabel("Default Rate (%)")
    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"{h:.2f}%", xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=10, weight="bold")
    ax.set_ylim(0, emp_risk["default_rate"].max() * 1.25)
    p = out_dir / "11_default_rate_by_employment_length.png"
    plt.savefig(p)
    plt.close()
    saved_paths.append(p)

    # 12. Loan Issuance Trends (Vintages)
    fig, ax = plt.subplots(figsize=(11, 5))
    vintage = df.groupby(["issue_year", "issue_quarter"]).agg(
        loan_count=("loan_amnt", "count"),
        volume_m=("funded_amnt", lambda s: s.sum() / 1e6)
    ).reset_index()
    vintage["quarter_label"] = vintage["issue_quarter"]
    ax.plot(vintage["quarter_label"], vintage["volume_m"], marker="o", color=PRIMARY, linewidth=2.5, label="Funded Volume ($M)")
    ax.set_title("Origination Volume Vintage Trend (2007 - 2011)")
    ax.set_xlabel("Origination Quarter")
    ax.set_ylabel("Quarterly Funded Volume ($ Millions)")
    ax.set_xticks(range(len(vintage)))
    ax.set_xticklabels(vintage["quarter_label"], rotation=45, ha="right", fontsize=9)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${int(x)}M"))
    ax.legend(loc="upper left")
    p = out_dir / "12_loan_issuance_trends.png"
    plt.savefig(p)
    plt.close()
    saved_paths.append(p)

    # 13. Loan Performance by Term (36 vs 60 Months)
    fig, ax = plt.subplots(figsize=(8, 5))
    term_perf = completed.groupby("term_clean").agg(
        total=("default_flag", "count"),
        defaults=("default_flag", "sum"),
        funded=("funded_amnt", "sum")
    ).reset_index()
    term_perf["default_rate"] = (term_perf["defaults"] / term_perf["total"]) * 100
    bars = ax.bar(term_perf["term_clean"], term_perf["default_rate"], color=[SUCCESS, DANGER], width=0.45)
    ax.set_title("Loan Default Rate Comparison by Contract Term")
    ax.set_xlabel("Contract Term")
    ax.set_ylabel("Historical Default Rate (%)")
    for idx, bar in enumerate(bars):
        h = bar.get_height()
        total_loans = term_perf["total"].iloc[idx]
        ax.annotate(f"{h:.2f}%\n({int(total_loans):,} loans)",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=10, weight="bold")
    ax.set_ylim(0, term_perf["default_rate"].max() * 1.3)
    p = out_dir / "13_loan_performance_by_term.png"
    plt.savefig(p)
    plt.close()
    saved_paths.append(p)

    # 14. Correlation Heatmap of Risk Numerics
    fig, ax = plt.subplots(figsize=(10, 8))
    corr_cols = ["loan_amnt", "int_rate", "annual_inc", "dti", "loan_to_income_ratio", "revol_util", "delinq_2yrs", "inq_last_6mths"]
    existing_corr = [c for c in corr_cols if c in df.columns]
    corr_mat = df[existing_corr].corr()
    sns.heatmap(corr_mat, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax, cbar_kws={"label": "Pearson Correlation"})
    ax.set_title("Credit & Behavioral Numeric Correlation Matrix")
    p = out_dir / "14_numeric_correlation_heatmap.png"
    plt.savefig(p)
    plt.close()
    saved_paths.append(p)

    # 15. Loss Severity and Recovery Waterfall (Defaulted Loans)
    fig, ax = plt.subplots(figsize=(10, 5))
    charged_off = df[df["loan_status"] == "Charged Off"]
    funded_co = charged_off["funded_amnt"].sum() / 1e6
    repaid_co = charged_off["total_rec_prncp"].sum() / 1e6
    shortfall_co = (funded_co - repaid_co)
    recov_co = charged_off["recoveries"].sum() / 1e6
    net_loss_co = (shortfall_co - recov_co)

    categories = ["Funded Defaulted", "Principal Repaid", "Gross Shortfall", "Recoveries", "Net Credit Loss"]
    values = [funded_co, repaid_co, shortfall_co, recov_co, net_loss_co]
    colors = [NEUTRAL, SUCCESS, WARNING, SECONDARY, DANGER]
    bars = ax.bar(categories, values, color=colors, width=0.55)
    ax.set_title("Credit Loss Resolution & Recovery Waterfall ($ Millions)")
    ax.set_ylabel("$ Millions")
    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"${h:.2f}M", xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=10, weight="bold")
    ax.set_ylim(0, max(values) * 1.15)
    p = out_dir / "15_loss_recovery_waterfall.png"
    plt.savefig(p)
    plt.close()
    saved_paths.append(p)

    return saved_paths


if __name__ == "__main__":
    cleaned_file = Path("data/processed/loans_cleaned.csv")
    fig_dir = Path("figures")
    print(f"Generating professional visualizations from {cleaned_file} into {fig_dir}...")
    saved = generate_all_figures(cleaned_file, fig_dir)
    print(f"Successfully generated {len(saved)} high-resolution financial charts:")
    for f in saved:
        print(f"  - {f.name}")
