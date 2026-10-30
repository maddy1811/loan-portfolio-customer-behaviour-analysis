# Power BI Executive Dashboard Blueprint
## Loan Portfolio & Customer Behaviour Analytics

**Theme:** Institutional Fintech & Capital Markets (Dark Navy `#1E3A8A`, Emerald `#059669`, Crimson `#BE123C`, Teal `#0D9488`).  
**Data Source:** `data/processed/loans_cleaned.csv` (Table Name: `Loans`).

---

## Global Filters & Top Navigation Slicer Bar
Place a horizontal top slicer strip pinned across all three pages:
* **Origination Year (`issue_year`):** Multi-select dropdown (`2007`, `2008`, `2009`, `2010`, `2011`).
* **Credit Grade (`grade`):** Tile / Buttons (`A`, `B`, `C`, `D`, `E`, `F`, `G`).
* **Loan Term (`term_clean`):** Dropdown (`36 months`, `60 months`).
* **Loan Purpose (`purpose`):** Dropdown (Debt Consolidation, Credit Card, Home Improvement, etc.).
* **Employment Tenure (`emp_length_band`):** Dropdown (`< 1 year`, `1-3 years`, `4-6 years`, `7-9 years`, `10+ years`).

---

## Page 1: Executive Portfolio Overview
**Objective:** Deliver C-suite and credit committee summary of capital deployment, portfolio liquidity, and default outcomes.

### Grid Layout & Visual Elements:
1. **Top KPI Ribbon (5 Cards):**
   * **Card 1: Total Funded Exposure** -> Measure: `[Total Funded Amount]` (Formatted: `$434.8M`)
   * **Card 2: Total Loans Originated** -> Measure: `[Total Loans]` (Formatted: `39,717`)
   * **Card 3: Average Loan Size** -> Measure: `[Average Loan Amount]` (Formatted: `$11,219`)
   * **Card 4: Historical Default Rate** -> Measure: `[Historical Default Rate]` (Formatted: `14.59%` with subtitle: *Completed Loans*)
   * **Card 5: Net Economic Return** -> Measure: `[Net Investor Return]` (Formatted: `+$47.89M`)

2. **Visual 1 (Donut Chart - Portfolio Outcome Composition):**
   * **Legend:** `Loans[outcome_group]` (`Completed - Paid`, `Completed - Default`, `Active - In Progress`).
   * **Values:** `[Total Loans]`.
   * **Colors:** Emerald Green (`#059669`), Crimson Red (`#BE123C`), Cool Slate (`#64748B`).
   * **Data Labels:** Category & Percentage (`82.96% Paid`, `14.17% Default`, `2.87% Active`).

3. **Visual 2 (Clustered Column Chart - Completed vs. Active Volume):**
   * **X-Axis:** `Loans[grade]`.
   * **Y-Axis:** `[Fully Paid Count]`, `[Charged Off Count]`, `[Active Loan Count]`.
   * **Title:** "Loan Volume and Settlement Status by Credit Grade".

4. **Visual 3 (Line & Clustered Column Chart - Vintage Issuance & Volume Trend):**
   * **X-Axis:** `Loans[issue_year_month]` or `Loans[issue_quarter]`.
   * **Column Y-Axis:** `[Total Funded Amount]` (Disbursed capital growth).
   * **Line Y-Axis:** `[Total Loans]` (Origination velocity).
   * **Title:** "Monthly Loan Origination Volume & Capital Deployment (2007 - 2011)".

---

## Page 2: Customer & Portfolio Analysis
**Objective:** Profile borrower demographics, capacity to borrow, and portfolio concentration.

### Grid Layout & Visual Elements:
1. **Top Metric Tiles:**
   * **Card 1: Average Borrower Income** -> `[Average Borrower Income]` (`$68,969`)
   * **Card 2: Average Debt-to-Income (DTI)** -> `[Average DTI Ratio]` (`13.32%`)
   * **Card 3: Average Contractual APR** -> `[Average Interest Rate]` (`12.02%`)
   * **Card 4: Average Credit Age** -> `[Average Credit History Years]` (`15.4 Years`)

2. **Visual 1 (Horizontal Bar Chart - Capital Allocation by Loan Purpose):**
   * **Y-Axis:** `Loans[purpose]` (Sorted descending by funded volume).
   * **X-Axis:** `[Total Funded Amount]`.
   * **Data Labels:** Values in Millions ($M).
   * **Insight Highlight:** Debt Consolidation (~$234M) and Credit Cards (~$61M) represent >67% of portfolio volume.

3. **Visual 2 (Column Chart - Customer Income Segmentation):**
   * **X-Axis:** `Loans[income_band]` (`< $40k`, `$40k - $75k`, `$75k - $100k`, `$100k - $150k`, `>= $150k`).
   * **Y-Axis:** `[Total Loans]`.
   * **Tooltip:** `[Average Loan Amount]`, `[Average DTI Ratio]`.

4. **Visual 3 (Treemap / 100% Stacked Bar - Home Ownership & Tenure):**
   * **Category:** `Loans[home_ownership_clean]` (`RENT`, `MORTGAGE`, `OWN`, `OTHER`).
   * **Breakdown / Legend:** `Loans[emp_length_band]`.
   * **Values:** `[Total Loans]`.

5. **Visual 4 (Histogram / Binned Column - Loan Amount Distribution):**
   * **X-Axis:** `Loans[loan_amnt]` (binned in $2,500 increments).
   * **Y-Axis:** `[Total Loans]`.
   * **Highlights:** Common round borrowing limits ($5,000, $10,000, $15,000, $20,000, $25,000).

---

## Page 3: Credit Risk & Performance
**Objective:** In-depth credit risk segmentation, default drivers, recovery efficacy, and loss provisioning.

### Grid Layout & Visual Elements:
1. **Risk KPI Cards:**
   * **Card 1: Gross Principal Shortfall** -> `[Gross Principal Shortfall]` (`$43.81M`)
   * **Card 2: Recoveries Collected** -> `[Total Recoveries Collected]` (`$3.78M`)
   * **Card 3: Net Realized Credit Loss** -> `[Total Net Credit Loss]` (`$40.03M`)
   * **Card 4: Portfolio Recovery Rate** -> `[Portfolio Recovery Rate %]` (`8.63%`)
   * **Card 5: Net Loss Severity** -> `[Loss Severity %]` (`60.53%`)

2. **Visual 1 (Step / Line Chart - Monotonic Default Rate by Credit Grade):**
   * **X-Axis:** `Loans[grade]` (`A`, `B`, `C`, `D`, `E`, `F`, `G`).
   * **Y-Axis:** `[Historical Default Rate]`.
   * **Secondary Y-Axis:** `[Average Interest Rate]`.
   * **Insight:** Grade A defaults at 5.99% (7.33% APR) vs Grade G defaulting at 33.78% (21.31% APR), illustrating risk-based pricing discipline.

3. **Visual 2 (Horizontal Bar Chart - Default Rate by Loan Purpose):**
   * **Y-Axis:** `Loans[purpose]` (Sorted descending by Default Rate).
   * **X-Axis:** `[Historical Default Rate]`.
   * **Reference Line:** Constant line at `14.59%` (Portfolio Average).
   * **Key Finding:** Small business loans default at 27.08%, while major purchase loans default at only 10.33%.

4. **Visual 3 (Matrix Visual - Risk Tier & Term Performance Grid):**
   * **Rows:** `Loans[customer_risk_tier]` (`Prime`, `Near-Prime`, `Subprime`).
   * **Columns:** `Loans[term_clean]` (`36 months`, `60 months`).
   * **Values:** `[Completed Loan Count]`, `[Historical Default Rate]`, `[Total Net Credit Loss]`, `[Portfolio Recovery Rate %]`.

5. **Visual 4 (Waterfall Chart - Credit Loss Resolution):**
   * **Category:** `Funded Defaulted` -> `Principal Repaid` -> `Gross Shortfall` -> `Recoveries` -> `Net Credit Loss`.
   * **Values:** `$66.14M` -> `-$22.32M` -> `$43.81M` -> `-$3.78M` -> `$40.03M`.
   * **Color Coding:** Standard accounting waterfall palette.

---

## Power BI Best Practices & Polish
1. **Tooltips:** Configure customized report page tooltips on default rate visuals explaining: *"Calculated strictly on completed loan outcomes (Fully Paid + Charged Off). Excludes 1,140 actively amortizing loans."*
2. **Formatting:** Ensure all currencies display USD symbols with commas (`$#,##0`). Rates and percentages formatted to two decimals (`0.00%`).
3. **Cross-Filtering:** Set slicers to cross-filter all visuals bi-directionally.
