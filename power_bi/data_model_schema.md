# Power BI Dimensional Data Model & Star Schema Architecture
## Loan Portfolio & Customer Behaviour Analytics

This document specifies both the **Single-Table Model** (immediate plug-and-play) and the **Star Schema Dimensional Model** (enterprise-grade data warehousing standard).

---

## Architecture 1: Single-Table Production Model (Recommended for Initial PBIX)

For swift validation and zero-loss DAX measure execution, `data/processed/loans_cleaned.csv` serves as the primary denormalized fact table **`Loans`**.

* **Row Count:** 39,717
* **Primary Key:** `id` (100% unique integer)
* **Secondary Key:** `member_id` (100% unique integer)
* **Temporal Key:** `issue_date` (`datetime64[ns]`)
* **Measures Storage:** Create an empty dedicated measures table named `_Measures` to house all portfolio and risk DAX formulas.

---

## Architecture 2: Enterprise Star Schema Specification

For institutional enterprise deployments (e.g. Fabric, Synapse, SQL Server, or Advanced Power BI Models), the denormalized dataset is decoupled into a star schema:

```mermaid
erDiagram
    DimDate ||--o{ FactLoans : "1:N (issue_date)"
    DimGrade ||--o{ FactLoans : "1:N (grade / sub_grade)"
    DimPurpose ||--o{ FactLoans : "1:N (purpose)"
    DimGeography ||--o{ FactLoans : "1:N (addr_state)"
    DimCustomer ||--o{ FactLoans : "1:N (member_id)"

    FactLoans {
        int id PK
        int member_id FK
        date issue_date FK
        string grade FK
        string sub_grade
        string purpose FK
        string addr_state FK
        decimal funded_amnt
        decimal loan_amnt
        decimal installment
        decimal int_rate
        decimal total_pymnt
        decimal total_rec_prncp
        decimal total_rec_int
        decimal recoveries
        decimal net_credit_loss
        decimal principal_shortfall
        int default_flag
        string loan_status
    }

    DimDate {
        date Date PK
        int Year
        int MonthNumber
        string MonthName
        string Quarter
        string YearMonth
    }

    DimGrade {
        string sub_grade PK
        string grade
        string customer_risk_tier
    }

    DimPurpose {
        string purpose PK
        string purpose_category
    }

    DimGeography {
        string addr_state PK
        string state_name
        string us_region
    }

    DimCustomer {
        int member_id PK
        decimal annual_inc
        string income_band
        string home_ownership_clean
        string emp_length_band
        float emp_length_years
        decimal dti
        string dti_band
        float credit_history_years
        int delinq_2yrs
        int inq_last_6mths
    }
```

---

## DAX Date Dimension Table Formula
In Power BI, create a dynamic calendar table linked to `Loans[issue_date]`:

```dax
DimDate = 
VAR MinDate = MIN(Loans[issue_date])
VAR MaxDate = MAX(Loans[issue_date])
RETURN
ADDCOLUMNS(
    CALENDAR(MinDate, MaxDate),
    "Year", YEAR([Date]),
    "Month Number", MONTH([Date]),
    "Month Name", FORMAT([Date], "MMMM"),
    "Month Short", FORMAT([Date], "MMM"),
    "Quarter", "Q" & FORMAT([Date], "Q"),
    "Year Quarter", FORMAT([Date], "YYYY") & "-Q" & FORMAT([Date], "Q"),
    "Year Month", FORMAT([Date], "YYYY-MM"),
    "Month Year Sort", YEAR([Date]) * 100 + MONTH([Date])
)
```

### Relationship Properties:
* **Cardinality:** One-to-Many (`1:*`) from `DimDate[Date]` to `Loans[issue_date]`.
* **Cross-Filter Direction:** Single (Dimension filters Fact).
* **Mark as Date Table:** Yes, select `DimDate[Date]` as the unique date identifier.
* **Sort By Column:** Sort `Month Name` by `Month Number`, and `Year Month` by `Month Year Sort`.
