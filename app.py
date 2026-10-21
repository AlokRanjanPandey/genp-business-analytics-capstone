
from pathlib import Path

import pandas as pd
import streamlit as st

# =====================================================
# 1. PAGE SETUP
# =====================================================

st.set_page_config(
    page_title="GenP Business Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 GenP Technologies")
st.subheader("Business Analytics Dashboard")

st.write(
    "Analyze sales, marketing, customer support, "
    "financial performance, and customer retention."
)

# =====================================================
# 2. LOAD THE FIVE CSV DATASETS
# =====================================================

DATA_DIR = Path(__file__).parent

REQUIRED_FILES = {
    "Customers": "Customers.csv",
    "Marketing": "Marketing_Campaigns.csv",
    "Financials": "SaaS_Financials.csv",
    "Sales": "Sales_Pipeline.csv",
    "Support": "Support_Tickets.csv",
}


@st.cache_data
def load_csv(file_path, modified_time):
    return pd.read_csv(file_path)


datasets = {}
errors = []

for dataset_name, filename in REQUIRED_FILES.items():
    file_path = DATA_DIR / filename

    if not file_path.is_file():
        errors.append(
            f"{filename} was not found beside app.py."
        )
        datasets[dataset_name] = pd.DataFrame()
        continue

    try:
        datasets[dataset_name] = load_csv(
            str(file_path),
            file_path.stat().st_mtime
        )
    except Exception as error:
        errors.append(
            f"{filename}: {type(error).__name__}: {error}"
        )
        datasets[dataset_name] = pd.DataFrame()

if errors:
    st.error("Some datasets could not be loaded.")

    for error in errors:
        st.write(f"- {error}")

    st.write("Files currently found in the app folder:")

    try:
        for file_path in sorted(DATA_DIR.iterdir()):
            st.write(f"- {file_path.name}")
    except Exception:
        st.write("Unable to list the app folder.")

    st.info(
        "Check that all five CSV files are committed to the "
        "same GitHub folder as app.py, and that their names "
        "match the filenames listed in the code."
    )

    st.stop()

customers = datasets["Customers"]
marketing = datasets["Marketing"]
financials = datasets["Financials"]
sales = datasets["Sales"]
support = datasets["Support"]

st.success("All five datasets loaded successfully.")

with st.expander("Dataset loading details"):
    for name, df in datasets.items():
        st.write(
            f"**{name}:** {len(df):,} rows and "
            f"{len(df.columns):,} columns"
        )

# =====================================================
# 3. HELPER FUNCTIONS
# =====================================================

def number_sum(df, column):
    if column not in df.columns:
        return 0.0

    return pd.to_numeric(
        df[column], errors="coerce"
    ).sum()


def number_mean(df, column):
    if column not in df.columns:
        return None

    values = pd.to_numeric(
        df[column], errors="coerce"
    ).dropna()

    if values.empty:
        return None

    return values.mean()


def money(value):
    if value is None or pd.isna(value):
        return "N/A"

    return f"${value:,.0f}"


def display_number(value, suffix="", decimals=1):
    if value is None or pd.isna(value):
        return "N/A"

    return f"{value:,.{decimals}f}{suffix}"


def show_kpis(items):
    columns = st.columns(len(items))

    for column, (label, value) in zip(columns, items):
        column.metric(label, value)


def yes_no_percentage(series):
    """Convert common Yes/No or True/False values to a percentage."""
    normalized = series.astype(str).str.strip().str.lower()

    mapping = {
        "yes": 1,
        "true": 1,
        "1": 1,
        "met": 1,
        "no": 0,
        "false": 0,
        "0": 0,
        "not met": 0,
    }

    converted = normalized.map(mapping).dropna()

    if converted.empty:
        numeric = pd.to_numeric(series, errors="coerce").dropna()

        if numeric.empty:
            return None

        if numeric.isin([0, 1]).all():
            return numeric.mean() * 100

        return None

    return converted.mean() * 100


# =====================================================
# 4. SIDEBAR FILTERS
# =====================================================

st.sidebar.title("Dashboard filters")
st.sidebar.caption("Use these filters to explore the data.")

regions = (
    sorted(customers["Region"].dropna().astype(str).unique())
    if "Region" in customers.columns else []
)

tiers = (
    sorted(
        customers["Customer_Tier"]
        .dropna().astype(str).unique()
    )
    if "Customer_Tier" in customers.columns else []
)

scenarios = (
    sorted(
        financials["Scenario"]
        .dropna().astype(str).unique()
    )
    if "Scenario" in financials.columns else []
)

selected_regions = st.sidebar.multiselect(
    "Customer region",
    regions,
    default=regions
)

selected_tiers = st.sidebar.multiselect(
    "Customer tier",
    tiers,
    default=tiers
)

selected_scenarios = st.sidebar.multiselect(
    "Financial scenario",
    scenarios,
    default=scenarios
)

# Create filtered copies of the datasets.
c = customers.copy()
m = marketing.copy()
f = financials.copy()
s = sales.copy()
t = support.copy()

if "Region" in c.columns:
    c = c[c["Region"].astype(str).isin(selected_regions)]

if "Customer_Tier" in c.columns:
    c = c[
        c["Customer_Tier"].astype(str).isin(selected_tiers)
    ]

if "Scenario" in f.columns:
    f = f[
        f["Scenario"].astype(str).isin(selected_scenarios)
    ]

# Apply selected customer filters to related datasets.
if "Customer_ID" in customers.columns:
    allowed_ids = set(c["Customer_ID"].dropna())

    if "Customer_ID" in s.columns:
        s = s[s["Customer_ID"].isin(allowed_ids)]

    if "Customer_ID" in t.columns:
        t = t[t["Customer_ID"].isin(allowed_ids)]

    if "Customer_ID" in f.columns:
        f = f[f["Customer_ID"].isin(allowed_ids)]

if "Region" in s.columns and selected_regions:
    s = s[s["Region"].astype(str).isin(selected_regions)]

# =====================================================
# 5. DASHBOARD TABS
# =====================================================

tabs = st.tabs([
    "Executive Overview",
    "Sales",
    "Marketing",
    "Support",
    "Financial Health",
    "Customer Health",
    "Data Quality",
])

# =====================================================
# TAB 1: EXECUTIVE OVERVIEW
# =====================================================

with tabs[0]:
    st.header("Executive Overview")

    st.write(
        "A high-level view of customer activity, revenue, "
        "sales pipeline, and support demand."
    )

    show_kpis([
        ("Customers", f"{len(c):,}"),
        ("Customer MRR", money(number_sum(c, "MRR_USD"))),
        ("Sales records", f"{len(s):,}"),
        ("Support tickets", f"{len(t):,}"),
        ("Marketing campaigns", f"{len(m):,}"),
    ])

    left, right = st.columns(2)

    with left:
        st.subheader("Customers by renewal status")

        if "Renewal_Status" in c.columns:
            counts = (
                c["Renewal_Status"]
                .fillna("Unknown")
                .value_counts()
            )
            st.bar_chart(counts)
        else:
            st.info("Renewal status is unavailable.")

    with right:
        st.subheader("Customers by tier")

        if "Customer_Tier" in c.columns:
            counts = (
                c["Customer_Tier"]
                .fillna("Unknown")
                .value_counts()
            )
            st.bar_chart(counts)
        else:
            st.info("Customer tier is unavailable.")

    st.subheader("Business questions")

    st.markdown("""
    - Are sales activities generating valuable customers?
    - Are marketing campaigns turning leads into activations?
    - Is customer support meeting service expectations?
    - Are customers renewing or showing signs of churn risk?
    - Are customer acquisition costs justified by lifetime value?
    """)

# =====================================================
# TAB 2: SALES
# =====================================================

with tabs[1]:
    st.header("Sales Performance")

    show_kpis([
        ("Pipeline records", f"{len(s):,}"),
        ("Total deal value", money(number_sum(s, "Deal_Value_USD"))),
        ("Average deal value", money(number_mean(s, "Deal_Value_USD"))),
        (
            "Average discount",
            display_number(number_mean(s, "Discount_Pct"), "%")
        ),
    ])

    left, right = st.columns(2)

    with left:
        st.subheader("Deal value by sales stage")

        if {"Sales_Stage", "Deal_Value_USD"}.issubset(s.columns):
            chart_data = s.copy()
            chart_data["Deal_Value_USD"] = pd.to_numeric(
                chart_data["Deal_Value_USD"],
                errors="coerce"
            )

            st.bar_chart(
                chart_data.groupby("Sales_Stage")[
                    "Deal_Value_USD"
                ].sum()
            )
        else:
            st.info("Sales stage or deal value is unavailable.")

    with right:
        st.subheader("Deal value by source")

        if {"Deal_Source", "Deal_Value_USD"}.issubset(s.columns):
            chart_data = s.copy()
            chart_data["Deal_Value_USD"] = pd.to_numeric(
                chart_data["Deal_Value_USD"],
                errors="coerce"
            )

            st.bar_chart(
                chart_data.groupby("Deal_Source")[
                    "Deal_Value_USD"
                ].sum()
            )
        else:
            st.info("Deal source or deal value is unavailable.")

    st.subheader("Deal value by region")

    if {"Region", "Deal_Value_USD"}.issubset(s.columns):
        chart_data = s.copy()
        chart_data["Deal_Value_USD"] = pd.to_numeric(
            chart_data["Deal_Value_USD"],
            errors="coerce"
        )

        st.bar_chart(
            chart_data.groupby("Region")["Deal_Value_USD"].sum()
        )

    if "Upsell_Flag" in s.columns:
        st.subheader("Upsell activity")
        st.bar_chart(
            s["Upsell_Flag"].fillna("Unknown").value_counts()
        )

    st.subheader("Sales records")
    st.dataframe(s, use_container_width=True, hide_index=True)

# =====================================================
# TAB 3: MARKETING
# =====================================================

with tabs[2]:
    st.header("Marketing Campaign Performance")

    show_kpis([
        ("Campaigns", f"{len(m):,}"),
        ("Actual spend", money(number_sum(m, "Actual_Spend_USD"))),
        ("Leads generated", f"{number_sum(m, 'Leads_Generated'):,.0f}"),
        ("Activations", f"{number_sum(m, 'Activations'):,.0f}"),
        (
            "Average activation rate",
            display_number(
                number_mean(m, "Activation_Rate_Pct"), "%"
            ),
        ),
    ])

    left, right = st.columns(2)

    with left:
        st.subheader("Marketing spend by channel")

        if {"Channel", "Actual_Spend_USD"}.issubset(m.columns):
            chart_data = m.copy()
            chart_data["Actual_Spend_USD"] = pd.to_numeric(
                chart_data["Actual_Spend_USD"],
                errors="coerce"
            )

            st.bar_chart(
                chart_data.groupby("Channel")[
                    "Actual_Spend_USD"
                ].sum()
            )
        else:
            st.info("Channel or actual spend is unavailable.")

    with right:
        st.subheader("Activations by campaign type")

        if {"Campaign_Type", "Activations"}.issubset(m.columns):
            chart_data = m.copy()
            chart_data["Activations"] = pd.to_numeric(
                chart_data["Activations"],
                errors="coerce"
            )

            st.bar_chart(
                chart_data.groupby("Campaign_Type")[
                    "Activations"
                ].sum()
            )
        else:
            st.info("Campaign type or activations is unavailable.")

    st.subheader("Campaign comparison")

    columns_to_show = [
        "Campaign_Name",
        "Campaign_Type",
        "Channel",
        "Budget_USD",
        "Actual_Spend_USD",
        "Leads_Generated",
        "Qualified_Leads",
        "Activations",
        "Activation_Rate_Pct",
        "Retention_7Day_Pct",
    ]

    available_columns = [
        col for col in columns_to_show if col in m.columns
    ]

    if available_columns:
        st.dataframe(
            m[available_columns],
            use_container_width=True,
            hide_index=True
        )

# =====================================================
# TAB 4: CUSTOMER SUPPORT
# =====================================================

with tabs[3]:
    st.header("Customer Support Performance")

    sla_rate = (
        yes_no_percentage(t["SLA_Met"])
        if "SLA_Met" in t.columns else None
    )

    show_kpis([
        ("Tickets", f"{len(t):,}"),
        (
            "Average resolution time",
            display_number(number_mean(t, "Resolution_Hours"), " hrs")
        ),
        ("Average CSAT", display_number(number_mean(t, "CSAT_Score"))),
        ("SLA met rate", display_number(sla_rate, "%")),
    ])

    left, right = st.columns(2)

    with left:
        st.subheader("Tickets by category")

        if "Category" in t.columns:
            st.bar_chart(
                t["Category"].fillna("Unknown").value_counts()
            )

    with right:
        st.subheader("Tickets by priority")

        if "Priority" in t.columns:
            st.bar_chart(
                t["Priority"].fillna("Unknown").value_counts()
            )

    st.subheader("Average resolution time by category")

    if {"Category", "Resolution_Hours"}.issubset(t.columns):
        chart_data = t.copy()
        chart_data["Resolution_Hours"] = pd.to_numeric(
            chart_data["Resolution_Hours"],
            errors="coerce"
        )

        st.bar_chart(
            chart_data.groupby("Category")[
                "Resolution_Hours"
            ].mean()
        )

    st.subheader("Support records")
    st.dataframe(t, use_container_width=True, hide_index=True)

# =====================================================
# TAB 5: FINANCIAL HEALTH
# =====================================================

with tabs[4]:
    st.header("Financial Health")

    show_kpis([
        (
            "ARR in selected records",
            money(number_sum(f, "ARR_USD"))
        ),
        ("Average CAC", money(number_mean(f, "CAC_USD"))),
        ("Average LTV", money(number_mean(f, "LTV_USD"))),
        (
            "Average LTV/CAC",
            display_number(number_mean(f, "LTV_CAC_Ratio"), "x")
        ),
        (
            "Average runway",
            display_number(number_mean(f, "Runway_Months"), " months")
        ),
    ])

    left, right = st.columns(2)

    with left:
        st.subheader("LTV/CAC by acquisition channel")

        if {"Acquisition_Channel", "LTV_CAC_Ratio"}.issubset(f.columns):
            chart_data = f.copy()
            chart_data["LTV_CAC_Ratio"] = pd.to_numeric(
                chart_data["LTV_CAC_Ratio"],
                errors="coerce"
            )

            st.bar_chart(
                chart_data.groupby("Acquisition_Channel")[
                    "LTV_CAC_Ratio"
                ].mean()
            )

    with right:
        st.subheader("Monthly churn by service line")

        if {"Service_Line", "Monthly_Churn_Rate_Pct"}.issubset(f.columns):
            chart_data = f.copy()
            chart_data["Monthly_Churn_Rate_Pct"] = pd.to_numeric(
                chart_data["Monthly_Churn_Rate_Pct"],
                errors="coerce"
            )

            st.bar_chart(
                chart_data.groupby("Service_Line")[
                    "Monthly_Churn_Rate_Pct"
                ].mean()
            )

    st.subheader("Cash balance and runway")

    financial_columns = [
        "Cohort",
        "Service_Line",
        "Scenario",
        "Cash_Balance_USD",
        "Burn_Rate_USD",
        "Runway_Months",
        "Gross_Margin_Pct",
        "Budget_Variance_Pct",
    ]

    available_columns = [
        col for col in financial_columns if col in f.columns
    ]

    if available_columns:
        st.dataframe(
            f[available_columns],
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        "Financial data may contain repeated records across customers, "
        "periods, or scenarios. Totals are not necessarily unique "
        "company-wide figures."
    )

# =====================================================
# TAB 6: CUSTOMER HEALTH
# =====================================================

with tabs[5]:
    st.header("Customer Health and Retention")

    if "Churn_Risk_Flag" in c.columns:
        risk_values = (
            c["Churn_Risk_Flag"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        risk_count = risk_values.isin(
            ["yes", "true", "1", "high", "at risk"]
        ).sum()
    else:
        risk_count = 0

    show_kpis([
        ("Customers in selection", f"{len(c):,}"),
        ("Average NPS score", display_number(number_mean(c, "NPS_Score"))),
        ("Customers flagged at churn risk", f"{risk_count:,}"),
        ("Customer MRR", money(number_sum(c, "MRR_USD"))),
    ])

    left, right = st.columns(2)

    with left:
        st.subheader("NPS score distribution")

        if "NPS_Score" in c.columns:
            scores = pd.to_numeric(
                c["NPS_Score"], errors="coerce"
            ).dropna()

            st.bar_chart(scores.value_counts().sort_index())

    with right:
        st.subheader("Customers by churn-risk flag")

        if "Churn_Risk_Flag" in c.columns:
            st.bar_chart(
                c["Churn_Risk_Flag"]
                .fillna("Unknown")
                .value_counts()
            )

    st.subheader("Customers by subscription plan")

    if "Subscribed_Plan" in c.columns:
        st.bar_chart(
            c["Subscribed_Plan"].fillna("Unknown").value_counts()
        )

    st.subheader("Customer records")
    st.dataframe(c, use_container_width=True, hide_index=True)

# =====================================================
# TAB 7: DATA QUALITY
# =====================================================

with tabs[6]:
    st.header("Data Quality Checks")

    st.write(
        "Review dataset sizes, missing values, and duplicate records "
        "before drawing business conclusions."
    )

    quality_rows = []

    for name, df in datasets.items():
        total_cells = df.size
        missing_cells = int(df.isna().sum().sum())

        quality_rows.append({
            "Dataset": name,
            "Rows": len(df),
            "Columns": len(df.columns),
            "Duplicate rows": int(df.duplicated().sum()),
            "Missing cells": missing_cells,
            "Missing cells (%)": round(
                missing_cells / max(total_cells, 1) * 100,
                2
            ),
        })

    quality_df = pd.DataFrame(quality_rows)

    st.dataframe(
        quality_df,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Missing values by field")

    dataset_choice = st.selectbox(
        "Choose a dataset",
        list(datasets.keys())
    )

    selected_df = datasets[dataset_choice]

    if not selected_df.empty:
        missing_df = (
            selected_df.isna()
            .sum()
            .rename("Missing values")
            .reset_index()
        )

        missing_df.columns = ["Column", "Missing values"]

        missing_df["Missing (%)"] = (
            missing_df["Missing values"]
            / max(len(selected_df), 1)
            * 100
        ).round(2)

        st.dataframe(
            missing_df.sort_values(
                "Missing values",
                ascending=False
            ),
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Dataset preview")
        st.dataframe(
            selected_df.head(100),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("This dataset has no rows to preview.")

# =====================================================
# 6. FOOTER
# =====================================================

st.divider()

st.caption(
    "GenP Technologies is a fictional business case. "
    "Use dashboard results as analytical evidence, not as proof "
    "of causation. Interpret financial totals according to the "
    "underlying dataset structure."
)
