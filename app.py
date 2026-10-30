"""Loan Portfolio & Customer Behaviour Analytics - Web Application.

A production-grade, interactive financial dashboard built with Streamlit and Plotly,
replicating institutional banking analytics and credit risk underwriting standards.
"""
from __future__ import annotations
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.dashboard_helpers import (
    set_custom_css, render_kpi, style_plot,
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_DANGER,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_MUTED, COLOR_LIGHT_BG
)

# Page configuration
st.set_page_config(
    page_title="Loan Portfolio & Risk Analytics | LendingClub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom fintech styling
set_custom_css()

DATA_PATH = Path("data/processed/loans_cleaned.csv")


@st.cache_data(show_spinner="Loading portfolio dataset...")
def load_data(filepath: Path) -> pd.DataFrame:
    """Load and cache the cleaned loans dataset."""
    if not filepath.exists():
        st.error(f"Processed dataset not found at {filepath}. Please run `python src/data_cleaning.py` first.")
        st.stop()
    df = pd.read_csv(filepath, low_memory=False)
    # Ensure date parsing
    if "issue_date" in df.columns:
        df["issue_date"] = pd.to_datetime(df["issue_date"], errors="coerce")
    return df


# Load dataset
df_raw = load_data(DATA_PATH)

# ==========================================
# SIDEBAR NAVIGATION & INTERACTIVE FILTERS
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0 20px 0;">
        <h2 style="color: #FFFFFF; margin: 0; font-size: 20px; font-weight: 700;">🏦 FinRisk Analytics</h2>
        <p style="color: #94A3B8; margin: 4px 0 0 0; font-size: 12px;">LendingClub Portfolio Intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        [
            "Executive Overview",
            "Loan Portfolio Analysis",
            "Customer Behaviour",
            "Credit Risk Analysis",
            "Recovery & Loss Analysis"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("<h4 style='color: #F8FAFC; font-size: 14px;'>Global Portfolio Filters</h4>", unsafe_allow_html=True)

    # 1. Grade Filter
    all_grades = sorted(df_raw["grade"].dropna().unique().tolist())
    selected_grades = st.multiselect("Credit Grade", all_grades, default=all_grades)

    # 2. Term Filter
    all_terms = sorted(df_raw["term_clean"].dropna().unique().tolist())
    selected_terms = st.multiselect("Loan Term", all_terms, default=all_terms)

    # 3. Purpose Filter
    all_purposes = sorted(df_raw["purpose"].dropna().unique().tolist())
    selected_purposes = st.multiselect("Loan Purpose", all_purposes, default=all_purposes)

    # 4. Employment Tenure Filter
    all_emp = ["< 1 year", "1-3 years", "4-6 years", "7-9 years", "10+ years", "Missing / Unreported"]
    existing_emp = [e for e in all_emp if e in df_raw["emp_length_band"].unique()]
    selected_emp = st.multiselect("Employment Tenure", existing_emp, default=existing_emp)

    # 5. Home Ownership Filter
    all_home = sorted(df_raw["home_ownership_clean"].dropna().unique().tolist())
    selected_home = st.multiselect("Home Ownership", all_home, default=all_home)

    # 6. Issue Year Filter
    min_year = int(df_raw["issue_year"].min()) if "issue_year" in df_raw else 2007
    max_year = int(df_raw["issue_year"].max()) if "issue_year" in df_raw else 2011
    selected_years = st.slider("Origination Years", min_value=min_year, max_value=max_year, value=(min_year, max_year))

    st.markdown("---")
    st.caption("Active Amortizing Loans (Current) are included in portfolio totals and excluded from default denominators.")


# Filter Application
mask = (
    df_raw["grade"].isin(selected_grades) &
    df_raw["term_clean"].isin(selected_terms) &
    df_raw["purpose"].isin(selected_purposes) &
    df_raw["emp_length_band"].isin(selected_emp) &
    df_raw["home_ownership_clean"].isin(selected_home) &
    df_raw["issue_year"].between(selected_years[0], selected_years[1])
)
df = df_raw[mask].copy()

if df.empty:
    st.warning("No loans match the current filter selection. Please broaden your filters in the sidebar.")
    st.stop()

# Segment definitions
completed_df = df[df["loan_status"].isin(["Fully Paid", "Charged Off"])].copy()
charged_off_df = df[df["loan_status"] == "Charged Off"].copy()
fully_paid_df = df[df["loan_status"] == "Fully Paid"].copy()
current_df = df[df["loan_status"] == "Current"].copy()

# ==========================================
# PAGE 1: EXECUTIVE OVERVIEW
# ==========================================
if page == "Executive Overview":
    st.markdown("""
    <div class="top-header-banner">
        <h1 class="top-header-title">Executive Portfolio Overview</h1>
        <p class="top-header-subtitle">Comprehensive C-Suite monitoring of capital deployment, portfolio liquidity, and default outcomes.</p>
    </div>
    """, unsafe_allow_html=True)

    # Primary KPI Row
    c1, c2, c3, c4 = st.columns(4)
    total_funded = df["funded_amnt"].sum()
    total_loans = len(df)
    avg_loan = df["loan_amnt"].mean()
    hist_default_rate = (len(charged_off_df) / len(completed_df) * 100) if len(completed_df) > 0 else 0.0

    with c1:
        render_kpi("Total Funded Capital", f"${total_funded/1e6:,.2f}M", f"{total_loans:,} Active & Closed Loans", "neutral")
    with c2:
        render_kpi("Average Loan Size", f"${avg_loan:,.0f}", f"Disbursed Avg: ${df['funded_amnt'].mean():,.0f}", "neutral")
    with c3:
        render_kpi("Historical Default Rate", f"{hist_default_rate:.2f}%", f"{len(charged_off_df):,} Defaults / {len(completed_df):,} Closed", "danger" if hist_default_rate > 15 else "warning")
    with c4:
        net_return = df["total_pymnt"].sum() - total_funded
        badge = "success" if net_return > 0 else "danger"
        render_kpi("Net Investor Return", f"${net_return/1e6:+,.2f}M", "Cash Collected vs Funded Capital", badge)

    # Secondary KPI Row
    c5, c6, c7, c8 = st.columns(4)
    fp_pct = (len(fully_paid_df) / total_loans * 100)
    co_pct = (len(charged_off_df) / total_loans * 100)
    total_recov = df["recoveries"].sum()
    net_credit_loss = df["net_credit_loss"].sum()

    with c5:
        render_kpi("Fully Paid Rate", f"{fp_pct:.2f}%", f"{len(fully_paid_df):,} Loans Settled", "success")
    with c6:
        render_kpi("Portfolio Default Share", f"{co_pct:.2f}%", f"{len(charged_off_df):,} Total Defaults", "danger")
    with c7:
        render_kpi("Post-Chargeoff Recoveries", f"${total_recov/1e6:,.2f}M", "Collections on Defaulted Debt", "neutral")
    with c8:
        render_kpi("Net Realized Loss", f"${net_credit_loss/1e6:,.2f}M", "Unrecovered Defaulted Capital", "danger")

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row 1
    col_left, col_right = st.columns([1, 2])

    with col_left:
        status_counts = df["loan_status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        color_map = {
            "Fully Paid": COLOR_SUCCESS,
            "Charged Off": COLOR_DANGER,
            "Current": COLOR_MUTED
        }
        fig_donut = px.pie(
            status_counts,
            names="Status",
            values="Count",
            hole=0.55,
            color="Status",
            color_discrete_map=color_map
        )
        fig_donut.update_traces(textposition="outside", textinfo="percent+label", pull=[0.05 if s == "Charged Off" else 0 for s in status_counts["Status"]])
        fig_donut = style_plot(fig_donut, "Portfolio Outcome Composition", height=380)
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_right:
        if "issue_year_month" in df.columns:
            monthly = df.groupby("issue_year_month").agg(
                funded_m=("funded_amnt", lambda s: s.sum() / 1e6),
                loan_count=("loan_amnt", "count")
            ).reset_index()
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(
                x=monthly["issue_year_month"],
                y=monthly["funded_m"],
                name="Funded Volume ($M)",
                marker_color=COLOR_PRIMARY,
                opacity=0.85
            ))
            fig_trend.add_trace(go.Scatter(
                x=monthly["issue_year_month"],
                y=monthly["loan_count"],
                name="Loan Count",
                yaxis="y2",
                line=dict(color=COLOR_SECONDARY, width=3),
                mode="lines+markers"
            ))
            fig_trend.update_layout(
                yaxis=dict(title="Funded Volume ($ Millions)"),
                yaxis2=dict(title="Loan Applications", overlaying="y", side="right", showgrid=False)
            )
            fig_trend = style_plot(fig_trend, "Monthly Origination Velocity & Capital Deployment", height=380)
            st.plotly_chart(fig_trend, use_container_width=True)

    # Charts Row 2
    grade_summary = df.groupby("grade").agg(
        funded_m=("funded_amnt", lambda s: s.sum() / 1e6),
        avg_rate=("int_rate", "mean")
    ).reset_index().sort_values("grade")

    fig_grade = px.bar(
        grade_summary,
        x="grade",
        y="funded_m",
        color="avg_rate",
        color_continuous_scale="Blues",
        labels={"grade": "Credit Grade", "funded_m": "Funded Capital ($M)", "avg_rate": "Avg APR (%)"},
        text=grade_summary["funded_m"].apply(lambda v: f"${v:.1f}M")
    )
    fig_grade.update_traces(textposition="outside")
    fig_grade = style_plot(fig_grade, "Funded Capital by Credit Grade & Risk-Based Pricing (APR)", height=380)
    st.plotly_chart(fig_grade, use_container_width=True)


# ==========================================
# PAGE 2: LOAN PORTFOLIO ANALYSIS
# ==========================================
elif page == "Loan Portfolio Analysis":
    st.markdown("""
    <div class="top-header-banner">
        <h1 class="top-header-title">Loan Portfolio Analysis</h1>
        <p class="top-header-subtitle">Detailed breakdown of capital allocation, borrowing purposes, interest rates, and loan structures.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        purpose_sum = df.groupby("purpose")["funded_amnt"].agg(["sum", "count"]).reset_index()
        purpose_sum["funded_m"] = purpose_sum["sum"] / 1e6
        purpose_sum = purpose_sum.sort_values("funded_m", ascending=True)

        fig_purp = px.bar(
            purpose_sum,
            y="purpose",
            x="funded_m",
            orientation="h",
            labels={"purpose": "Loan Purpose", "funded_m": "Total Funded ($ Millions)"},
            color_discrete_sequence=[COLOR_PRIMARY]
        )
        fig_purp.update_traces(text=purpose_sum["funded_m"].apply(lambda v: f"${v:.1f}M"), textposition="outside")
        fig_purp = style_plot(fig_purp, "Funded Capital Allocation by Loan Purpose", height=420)
        st.plotly_chart(fig_purp, use_container_width=True)

    with col2:
        fig_hist = px.histogram(
            df,
            x="loan_amnt",
            nbins=35,
            color_discrete_sequence=[COLOR_SECONDARY],
            labels={"loan_amnt": "Loan Amount (USD)"}
        )
        fig_hist.add_vline(x=df["loan_amnt"].median(), line_dash="dash", line_color=COLOR_DANGER, annotation_text=f"Median: ${df['loan_amnt'].median():,.0f}")
        fig_hist = style_plot(fig_hist, "Borrowing Size Distribution (Requested Capital)", height=420)
        st.plotly_chart(fig_hist, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        fig_box = px.box(
            df,
            x="grade",
            y="int_rate",
            category_orders={"grade": sorted(df["grade"].unique())},
            color="grade",
            color_discrete_sequence=px.colors.sequential.Blues_r,
            labels={"grade": "Credit Grade", "int_rate": "Contractual Interest Rate (%)"}
        )
        fig_box = style_plot(fig_box, "Interest Rate Distribution Across Credit Grades", height=400)
        st.plotly_chart(fig_box, use_container_width=True)

    with col4:
        term_counts = df["term_clean"].value_counts().reset_index()
        term_counts.columns = ["Term", "Count"]
        fig_term = px.pie(
            term_counts,
            names="Term",
            values="Count",
            hole=0.5,
            color="Term",
            color_discrete_map={"36 months": COLOR_PRIMARY, "60 months": COLOR_WARNING}
        )
        fig_term.update_traces(textposition="outside", textinfo="percent+label")
        fig_term = style_plot(fig_term, "Contract Term Structure (36 vs 60 Months)", height=400)
        st.plotly_chart(fig_term, use_container_width=True)

    col5, col6 = st.columns(2)

    with col5:
        home_counts = df["home_ownership_clean"].value_counts().reset_index()
        home_counts.columns = ["Home Ownership", "Count"]
        fig_home = px.bar(
            home_counts,
            x="Home Ownership",
            y="Count",
            color="Home Ownership",
            color_discrete_sequence=[COLOR_PRIMARY, COLOR_SECONDARY, COLOR_WARNING, COLOR_MUTED],
            text="Count"
        )
        fig_home.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_home = style_plot(fig_home, "Borrower Home Ownership Structure", height=380)
        st.plotly_chart(fig_home, use_container_width=True)

    with col6:
        inc_order = ["< $40,000", "$40,000 - $75,000", "$75,000 - $100,000", "$100,000 - $150,000", ">= $150,000"]
        inc_counts = df["income_band"].value_counts().reindex(inc_order).fillna(0).reset_index()
        inc_counts.columns = ["Income Tier", "Borrowers"]
        fig_inc = px.bar(
            inc_counts,
            x="Income Tier",
            y="Borrowers",
            color_discrete_sequence=[COLOR_PRIMARY],
            text="Borrowers"
        )
        fig_inc.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_inc = style_plot(fig_inc, "Customer Annual Income Segmentation", height=380)
        st.plotly_chart(fig_inc, use_container_width=True)


# ==========================================
# PAGE 3: CUSTOMER BEHAVIOUR
# ==========================================
elif page == "Customer Behaviour":
    st.markdown("""
    <div class="top-header-banner">
        <h1 class="top-header-title">Customer Behaviour & Demographics</h1>
        <p class="top-header-subtitle">Analysis of borrower employment stability, debt burden, revolving line utilization, and risk segmentation.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        emp_order = ["< 1 year", "1-3 years", "4-6 years", "7-9 years", "10+ years", "Missing / Unreported"]
        emp_counts = df["emp_length_band"].value_counts().reindex(emp_order).fillna(0).reset_index()
        emp_counts.columns = ["Tenure Band", "Borrowers"]
        fig_emp = px.bar(
            emp_counts,
            x="Tenure Band",
            y="Borrowers",
            color_discrete_sequence=[COLOR_PRIMARY],
            text="Borrowers"
        )
        fig_emp.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_emp = style_plot(fig_emp, "Borrower Employment Tenure Distribution", height=400)
        st.plotly_chart(fig_emp, use_container_width=True)

    with col2:
        # Sample for smooth responsive scatter visualization
        scatter_sample = df.sample(min(3000, len(df)), random_state=42)
        fig_scatter = px.scatter(
            scatter_sample,
            x="annual_inc",
            y="loan_amnt",
            color="customer_risk_tier",
            color_discrete_map={"Prime": COLOR_SUCCESS, "Near-Prime": COLOR_WARNING, "Subprime": COLOR_DANGER},
            labels={"annual_inc": "Annual Income ($)", "loan_amnt": "Loan Amount ($)", "customer_risk_tier": "Risk Tier"},
            opacity=0.6
        )
        fig_scatter.update_xaxes(range=[0, min(300000, df["annual_inc"].quantile(0.995))])
        fig_scatter = style_plot(fig_scatter, "Customer Capacity: Income vs. Loan Size (Truncated Display)", height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        fig_dti = px.histogram(
            df,
            x="dti",
            nbins=30,
            color_discrete_sequence=["#4338CA"],
            labels={"dti": "Debt-to-Income Ratio (%)"}
        )
        fig_dti.add_vline(x=20.0, line_dash="dash", line_color=COLOR_DANGER, annotation_text="DTI Risk Benchmark (20%)")
        fig_dti = style_plot(fig_dti, "Borrower Debt-to-Income (DTI) Ratio Distribution", height=400)
        st.plotly_chart(fig_dti, use_container_width=True)

    with col4:
        fig_util = px.histogram(
            df.dropna(subset=["revol_util"]),
            x="revol_util",
            nbins=35,
            color_discrete_sequence=[COLOR_SECONDARY],
            labels={"revol_util": "Revolving Credit Utilization (%)"}
        )
        fig_util.add_vline(x=80.0, line_dash="dash", line_color=COLOR_DANGER, annotation_text="High Utilization (80%)")
        fig_util = style_plot(fig_util, "Revolving Credit Line Utilization Rate (%)", height=400)
        st.plotly_chart(fig_util, use_container_width=True)

    # Customer Risk Tier Summary Table
    st.markdown("<h4 style='color: #0F172A; font-weight: 700;'>Customer Risk Tier Strategic Matrix</h4>", unsafe_allow_html=True)
    tier_summary = completed_df.groupby("customer_risk_tier").agg(
        Total_Loans=("id", "count"),
        Defaults=("default_flag", "sum"),
        Default_Rate=("default_flag", lambda s: f"{s.mean()*100:.2f}%"),
        Funded_Volume=("funded_amnt", lambda s: f"${s.sum()/1e6:,.2f}M"),
        Avg_Loan_Size=("loan_amnt", lambda s: f"${s.mean():,.0f}"),
        Avg_Interest_Rate=("int_rate", lambda s: f"{s.mean():.2f}%"),
        Net_Credit_Loss=("net_credit_loss", lambda s: f"${s.sum()/1e6:,.2f}M")
    ).reset_index()
    st.dataframe(tier_summary, use_container_width=True)


# ==========================================
# PAGE 4: CREDIT RISK ANALYSIS
# ==========================================
elif page == "Credit Risk Analysis":
    st.markdown("""
    <div class="top-header-banner">
        <h1 class="top-header-title">Credit Risk & Default Assessment</h1>
        <p class="top-header-subtitle">Empirical default probabilities, credit rating monotonic curves, risk tier benchmarking, and vintage performance.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        grade_risk = completed_df.groupby("grade").agg(
            total=("default_flag", "count"),
            defaults=("default_flag", "sum")
        ).reset_index()
        grade_risk["default_rate"] = (grade_risk["defaults"] / grade_risk["total"]) * 100
        grade_risk = grade_risk.sort_values("grade")

        fig_gr_risk = px.bar(
            grade_risk,
            x="grade",
            y="default_rate",
            color="default_rate",
            color_continuous_scale="Reds",
            labels={"grade": "Credit Grade", "default_rate": "Historical Default Rate (%)"},
            text=grade_risk["default_rate"].apply(lambda v: f"{v:.2f}%")
        )
        fig_gr_risk.update_traces(textposition="outside")
        fig_gr_risk = style_plot(fig_gr_risk, "Monotonic Default Rate by Credit Grade (A to G)", height=420)
        st.plotly_chart(fig_gr_risk, use_container_width=True)

    with col2:
        purp_risk = completed_df.groupby("purpose").agg(
            total=("default_flag", "count"),
            defaults=("default_flag", "sum")
        ).reset_index()
        purp_risk["default_rate"] = (purp_risk["defaults"] / purp_risk["total"]) * 100
        purp_risk = purp_risk.sort_values("default_rate", ascending=True)

        fig_p_risk = px.bar(
            purp_risk,
            y="purpose",
            x="default_rate",
            orientation="h",
            color="default_rate",
            color_continuous_scale="Reds",
            labels={"purpose": "Loan Purpose", "default_rate": "Default Rate (%)"}
        )
        fig_p_risk.update_traces(text=purp_risk["default_rate"].apply(lambda v: f"{v:.2f}%"), textposition="outside")
        fig_p_risk.add_vline(x=completed_df["default_flag"].mean() * 100, line_dash="dash", line_color=COLOR_PRIMARY, annotation_text="Portfolio Avg")
        fig_p_risk = style_plot(fig_p_risk, "Historical Default Rate by Loan Purpose", height=420)
        st.plotly_chart(fig_p_risk, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        term_risk = completed_df.groupby("term_clean").agg(
            total=("default_flag", "count"),
            defaults=("default_flag", "sum")
        ).reset_index()
        term_risk["default_rate"] = (term_risk["defaults"] / term_risk["total"]) * 100

        fig_t_risk = px.bar(
            term_risk,
            x="term_clean",
            y="default_rate",
            color="term_clean",
            color_discrete_map={"36 months": COLOR_SUCCESS, "60 months": COLOR_DANGER},
            labels={"term_clean": "Contract Term", "default_rate": "Default Rate (%)"},
            text=term_risk["default_rate"].apply(lambda v: f"{v:.2f}%")
        )
        fig_t_risk.update_traces(textposition="outside")
        fig_t_risk = style_plot(fig_t_risk, "Default Rate by Loan Term Duration (36 vs 60 Months)", height=380)
        st.plotly_chart(fig_t_risk, use_container_width=True)

    with col4:
        emp_risk = completed_df.groupby("emp_length_band").agg(
            total=("default_flag", "count"),
            defaults=("default_flag", "sum")
        ).reindex(emp_order).dropna().reset_index()
        emp_risk["default_rate"] = (emp_risk["defaults"] / emp_risk["total"]) * 100

        fig_e_risk = px.bar(
            emp_risk,
            x="emp_length_band",
            y="default_rate",
            color_discrete_sequence=["#0284C7"],
            labels={"emp_length_band": "Employment Tenure", "default_rate": "Default Rate (%)"},
            text=emp_risk["default_rate"].apply(lambda v: f"{v:.2f}%")
        )
        fig_e_risk.update_traces(textposition="outside")
        fig_e_risk = style_plot(fig_e_risk, "Default Rate Across Employment Tenure Categories", height=380)
        st.plotly_chart(fig_e_risk, use_container_width=True)


# ==========================================
# PAGE 5: RECOVERY & LOSS ANALYSIS
# ==========================================
elif page == "Recovery & Loss Analysis":
    st.markdown("""
    <div class="top-header-banner">
        <h1 class="top-header-title">Recovery & Loss Severity Analytics</h1>
        <p class="top-header-subtitle">Accounting shortfall, collections efficiency, recovery rates, and net credit loss provisioning.</p>
    </div>
    """, unsafe_allow_html=True)

    # Recovery KPIs
    funded_co = charged_off_df["funded_amnt"].sum()
    repaid_co = charged_off_df["total_rec_prncp"].sum()
    shortfall = funded_co - repaid_co
    recov = charged_off_df["recoveries"].sum()
    net_loss = np.maximum(0.0, shortfall - recov)
    recov_rate = (recov / shortfall * 100) if shortfall > 0 else 0.0
    loss_severity = (net_loss / funded_co * 100) if funded_co > 0 else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_kpi("Defaulted Capital", f"${funded_co/1e6:,.2f}M", f"{len(charged_off_df):,} Defaulted Loans", "neutral")
    with c2:
        render_kpi("Gross Shortfall", f"${shortfall/1e6:,.2f}M", "Unrepaid Principal", "warning")
    with c3:
        render_kpi("Recoveries Collected", f"${recov/1e6:,.2f}M", "Post-Chargeoff Recovery", "success")
    with c4:
        render_kpi("Net Realized Loss", f"${net_loss/1e6:,.2f}M", "True Economic Loss", "danger")
    with c5:
        render_kpi("Recovery Rate", f"{recov_rate:.2f}%", f"Severity: {loss_severity:.1f}%", "neutral")

    st.markdown("<br>", unsafe_allow_html=True)

    # Waterfall Chart
    fig_waterfall = go.Figure(go.Waterfall(
        name="Credit Loss",
        orientation="v",
        measure=["relative", "relative", "total", "relative", "total"],
        x=["Funded Defaulted", "Principal Repaid Pre-Default", "Gross Principal Shortfall", "Recoveries Collected", "Net Realized Loss"],
        textposition="outside",
        text=[f"${funded_co/1e6:,.2f}M", f"-${repaid_co/1e6:,.2f}M", f"${shortfall/1e6:,.2f}M", f"-${recov/1e6:,.2f}M", f"${net_loss/1e6:,.2f}M"],
        y=[funded_co/1e6, -repaid_co/1e6, 0, -recov/1e6, 0],
        connector={"line": {"color": "#94A3B8"}},
        decreasing={"marker": {"color": COLOR_SUCCESS}},
        increasing={"marker": {"color": COLOR_WARNING}},
        totals={"marker": {"color": COLOR_DANGER}}
    ))
    fig_waterfall = style_plot(fig_waterfall, "Credit Loss Resolution & Recovery Waterfall ($ Millions)", height=450)
    st.plotly_chart(fig_waterfall, use_container_width=True)

    # Recovery by Grade Breakdown
    col_a, col_b = st.columns(2)
    with col_a:
        rec_by_grade = charged_off_df.groupby("grade").agg(
            funded_co=("funded_amnt", "sum"),
            shortfall=("principal_shortfall", "sum"),
            recoveries=("recoveries", "sum")
        ).reset_index()
        rec_by_grade["recovery_rate"] = (rec_by_grade["recoveries"] / rec_by_grade["shortfall"]) * 100
        fig_rec_gr = px.bar(
            rec_by_grade,
            x="grade",
            y="recovery_rate",
            color="recovery_rate",
            color_continuous_scale="Blues",
            labels={"grade": "Credit Grade", "recovery_rate": "Recovery Rate (%)"},
            text=rec_by_grade["recovery_rate"].apply(lambda v: f"{v:.2f}%")
        )
        fig_rec_gr.update_traces(textposition="outside")
        fig_rec_gr = style_plot(fig_rec_gr, "Capital Recovery Rate on Shortfall by Credit Grade (%)", height=380)
        st.plotly_chart(fig_rec_gr, use_container_width=True)

    with col_b:
        fig_net_gain = px.box(
            df,
            x="grade",
            y="net_investor_gain_loss",
            color="grade",
            color_discrete_sequence=px.colors.sequential.Blues_r,
            labels={"grade": "Credit Grade", "net_investor_gain_loss": "Net Cashflow Return ($)"}
        )
        fig_net_gain.add_hline(y=0, line_dash="dash", line_color=COLOR_DANGER)
        fig_net_gain = style_plot(fig_net_gain, "Net Investor Cashflow Gain/Loss Distribution by Grade", height=380)
        st.plotly_chart(fig_net_gain, use_container_width=True)
