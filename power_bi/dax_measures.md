# Power BI DAX Measures Dictionary
## Loan Portfolio & Customer Behaviour Analytics

All DAX measures are written assuming the primary fact table is named **`Loans`** (imported from `data/processed/loans_cleaned.csv`).

> [!IMPORTANT]
> **Analytical Principle:**  
> `Historical Default Rate` measures outcomes strictly across **completed loans** (`Fully Paid` and `Charged Off`). Ongoing `Current` loans (1,140 loans) are actively amortizing and must not be treated as non-defaults.

---

### 1. Portfolio Volume & Status Measures

#### Total Loans
```dax
Total Loans = COUNTROWS(Loans)
```
*Description:* Total number of loan applications in the portfolio (39,717).  
*Format:* Whole Number (`#,##0`).

#### Active Loan Count
```dax
Active Loan Count = 
CALCULATE(
    [Total Loans],
    Loans[loan_status] = "Current"
)
```
*Description:* Number of loans currently active and amortizing (1,140).  
*Format:* Whole Number (`#,##0`).

#### Completed Loan Count
```dax
Completed Loan Count = 
CALCULATE(
    [Total Loans],
    Loans[loan_status] IN {"Fully Paid", "Charged Off"}
)
```
*Description:* Completed loan cohort with definitive repayment or loss outcomes (38,577).  
*Format:* Whole Number (`#,##0`).

#### Fully Paid Count
```dax
Fully Paid Count = 
CALCULATE(
    [Total Loans],
    Loans[loan_status] = "Fully Paid"
)
```
*Description:* Total loans settled in full without loss (32,950).  
*Format:* Whole Number (`#,##0`).

#### Charged Off Count
```dax
Charged Off Count = 
CALCULATE(
    [Total Loans],
    Loans[loan_status] = "Charged Off"
)
```
*Description:* Total defaulted loans written off as uncollectible (5,627).  
*Format:* Whole Number (`#,##0`).

#### Fully Paid %
```dax
Fully Paid % = 
DIVIDE([Fully Paid Count], [Total Loans], 0)
```
*Description:* Percentage of total portfolio fully settled (82.96%).  
*Format:* Percentage (`0.0%`).

#### Charged Off % (Portfolio Share)
```dax
Charged Off % = 
DIVIDE([Charged Off Count], [Total Loans], 0)
```
*Description:* Proportion of total portfolio defaulted (14.17%).  
*Format:* Percentage (`0.0%`).

---

### 2. Credit Risk & Default Rate Measures

#### Historical Default Rate (Completed Loans)
```dax
Historical Default Rate = 
DIVIDE(
    [Charged Off Count],
    [Completed Loan Count],
    BLANK()
)
```
*Description:* Standard banking metric: Default rate across completed loan commitments (14.59%). Excludes active loans from denominator to avoid survivor bias.  
*Format:* Percentage (`0.00%`).

#### Prime Cohort Default Rate
```dax
Prime Default Rate = 
CALCULATE(
    [Historical Default Rate],
    Loans[customer_risk_tier] = "Prime"
)
```
*Description:* Benchmark default rate for Grade A and B borrowers (9.33%).  
*Format:* Percentage (`0.00%`).

#### Subprime Cohort Default Rate
```dax
Subprime Default Rate = 
CALCULATE(
    [Historical Default Rate],
    Loans[customer_risk_tier] = "Subprime"
)
```
*Description:* Benchmark default rate for Grade E, F, and G borrowers (29.07%).  
*Format:* Percentage (`0.00%`).

---

### 3. Financial Exposure & Capital Measures

#### Total Funded Amount
```dax
Total Funded Amount = 
SUM(Loans[funded_amnt])
```
*Description:* Total principal capital committed and disbursed by LendingClub ($434.81M).  
*Format:* Currency (`$#,##0`).

#### Total Loan Amount Requested
```dax
Total Loan Amount Requested = 
SUM(Loans[loan_amnt])
```
*Description:* Gross borrowing volume requested by applicants ($445.60M).  
*Format:* Currency (`$#,##0`).

#### Average Loan Amount
```dax
Average Loan Amount = 
AVERAGE(Loans[loan_amnt])
```
*Description:* Average loan size requested across applicants ($11,219).  
*Format:* Currency (`$#,##0`).

#### Average Funded Amount
```dax
Average Funded Amount = 
AVERAGE(Loans[funded_amnt])
```
*Description:* Average disbursed principal per loan ($10,948).  
*Format:* Currency (`$#,##0`).

---

### 4. Cash Flow, Loss & Recovery Measures

#### Total Payments Received
```dax
Total Payments Received = 
SUM(Loans[total_pymnt])
```
*Description:* Cumulative cash collected across all loans ($482.70M).  
*Format:* Currency (`$#,##0`).

#### Total Principal Recovered
```dax
Total Principal Recovered = 
SUM(Loans[total_rec_prncp])
```
*Description:* Total loan principal returned ($388.96M).  
*Format:* Currency (`$#,##0`).

#### Total Interest Earned
```dax
Total Interest Earned = 
SUM(Loans[total_rec_int])
```
*Description:* Cumulative interest collected from borrowers ($89.91M).  
*Format:* Currency (`$#,##0`).

#### Total Recoveries Collected
```dax
Total Recoveries Collected = 
SUM(Loans[recoveries])
```
*Description:* Gross post-chargeoff recovery collections ($3.78M).  
*Format:* Currency (`$#,##0`).

#### Gross Principal Shortfall
```dax
Gross Principal Shortfall = 
CALCULATE(
    SUM(Loans[principal_shortfall]),
    Loans[loan_status] = "Charged Off"
)
```
*Description:* Uncollected principal prior to recovery collections ($43.81M).  
*Format:* Currency (`$#,##0`).

#### Total Net Credit Loss
```dax
Total Net Credit Loss = 
SUM(Loans[net_credit_loss])
```
*Description:* Actual unrecovered principal capital post-recoveries across defaulted loans ($40.03M).  
*Format:* Currency (`$#,##0`).

#### Net Investor Return (Gain / Loss)
```dax
Net Investor Return = 
[Total Payments Received] - [Total Funded Amount]
```
*Description:* Net economic cash return generated by the portfolio (+$47.89M).  
*Format:* Currency (`$#,##0`).

#### Portfolio Recovery Rate %
```dax
Portfolio Recovery Rate % = 
DIVIDE(
    [Total Recoveries Collected],
    [Gross Principal Shortfall],
    0
)
```
*Description:* Capital recovery efficiency on defaulted principal shortfall (8.63%).  
*Format:* Percentage (`0.00%`).

#### Loss Severity %
```dax
Loss Severity % = 
VAR DefaultedFunded = 
    CALCULATE(
        [Total Funded Amount],
        Loans[loan_status] = "Charged Off"
    )
RETURN
    DIVIDE([Total Net Credit Loss], DefaultedFunded, 0)
```
*Description:* Proportion of defaulted principal ultimately written off after recoveries (60.53%).  
*Format:* Percentage (`0.00%`).

---

### 5. Borrower Behavior & Pricing Measures

#### Average Interest Rate
```dax
Average Interest Rate = 
AVERAGE(Loans[int_rate])
```
*Description:* Average contractual interest rate (12.02%).  
*Format:* Percentage (`0.00%`).

#### Average DTI Ratio
```dax
Average DTI Ratio = 
AVERAGE(Loans[dti])
```
*Description:* Average borrower Debt-to-Income ratio (13.32%).  
*Format:* Decimal (`0.00`).

#### Average Borrower Income
```dax
Average Borrower Income = 
AVERAGE(Loans[annual_inc])
```
*Description:* Average self-reported annual income ($68,969).  
*Format:* Currency (`$#,##0`).

#### Average Credit History Years
```dax
Average Credit History Years = 
AVERAGE(Loans[credit_history_years])
```
*Description:* Average credit line age at loan origination (15.4 years).  
*Format:* Decimal (`0.0`).
