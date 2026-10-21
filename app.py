from pathlib import Path
import pandas as pd
import streamlit as st

# ---------------- PAGE SETUP ----------------
st.set_page_config(
    page_title="GenP Business Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 GenP Technologies | Business Analytics Dashboard")
st.caption(
    "A cross-functional view of sales, marketing, customer support, "
    "customer health, and financial performance."
)

DATA_DIR = Path(__file__).parent


# ---------------- DATA LOADING ----------------
@st.cache_data
def load_csv(filename):
    path = DATA_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


customers = load_csv("Customers.csv")
marketing = load_csv("Marketing_Campaigns.csv")
financials = load_csv("SaaS_Financials.csv")
sales = load_csv("Sales_Pipeline.csv")
support = load_csv("Support_Tickets.csv")


def money(value):
    return f"${value:,.0f}" if pd.notna(value) else "N/A"


def numeric_sum(df, column):
    if column in df.columns:
        return pd.to_numeric(df[column], errors="coerce").sum()
    return 0


def numeric_mean(df, column):
    if column in df.columns:
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        return series.mean() if not series.empty else None
    return None


def metric_value(value, suffix="", decimals=1):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.{decimals}f}{suffix}"


# ---------------- CHECK DATA ----------------
datasets = {
    "Customers": customers,
    "Marketing campaigns": marketing,
    "Financials": financials,
    "Sales pipeline": sales,
    "Support tickets": support,
}

missing = [name for name, df in datasets.items() if df.empty]

if missing:
    st.error(
        "Some datasets are missing or could not be read: "
        + ", ".join(missing)
    )
    st.info(
        "Upload all five CSV files into the same GitHub repository folder "
        "as app.py. Use the exact filenames listed in the README."
    )
    st.stop()


# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.header("Dashboard filters")

regions = sorted(
    customers["Region"].dropna().astype(str).unique()
) if "Region" in customers.columns else []

tiers = sorted(
    customers["Customer_Tier"].dropna().astype(str).unique()
) if "Customer_Tier" in customers.columns else []

scenarios = sorted(
    financials["Scenario"].dropna().astype(str).unique()
) if "Scenario" in financials.columns else []

selected_regions = st.sidebar.multiselect(
    "Customer region", regions, default=regions
)

selected_tiers = st.sidebar.multiselect(
    "Customer tier", tiers, default=tiers
)

selected_scenarios = st.sidebar.multiselect(
    "Financial scenario", scenarios, default=scenarios
)

c = customers.copy()
m = marketing.copy()
f = financials.copy()
s = sales.copy()
t = support.copy()

if "Region" in c.columns and selected_regions:
    c = c[c["Region"].astype(str).isin(selected_regions)]

if "Customer_Tier" in c.columns and selected_tiers:
    c = c[c["Customer_Tier"].astype(str).isin(selected_tiers)]

if "Scenario" in f.columns and selected_scenarios:
    f = f[f["Scenario"].astype(str).isin(selected_scenarios)]

# Apply customer filters to datasets that share Customer_ID
if "Customer_ID" in c.columns:
    allowed_ids = set(c["Customer_ID"].dropna())

    if "Customer_ID" in s.columns:
        s = s[s["Customer_ID"].isin(allowed_ids)]

    if "Customer_ID" in t.columns:
        t = t[t["Customer_ID"].isin(allowed_ids)]

    if "Customer_ID" in f.columns:
        f = f[f["Customer_ID"].isin(allowed_ids)]


# ---------------- KPI HELPERS ----------------
def show_kpis(items):
    columns = st.columns(len(items))
    for column, (label, value) in zip(columns, items):
        column.metric(label, value)


# ---------------- DASHBOARD TABS ----------------
tabs = st.tabs([
    "Executive overview",
    "Sales",
    "Marketing",
    "Support",
    "Financial health",
    "Customer health",
    "Data quality",
])


# =========================================================
# 1. EXECUTIVE OVERVIEW
# =========================================================
with tabs[0]:
    st.header("Executive overview")
    st.write(
        "Use this page to understand the relationship between acquisition, "
        "customer retention, service quality, and financial performance."
    )

    total_mrr = numeric_sum(c, "MRR_USD")
    total_arr = numeric_sum(f, "ARR_USD")
    total_deals = len(s)
    total_tickets = len(t)

    show_kpis([
        ("Customers", f"{len(c):,}"),
        ("Customer MRR", money(total_mrr)),
        ("Financial ARR records total", money(total_arr)),
        ("Sales pipeline records", f"{total_deals:,}"),
        ("Support tickets", f"{total_tickets:,}"),
    ])

    left, right = st.columns(2)

    with left:
        st.subheader("Customers by renewal status")
        if "Renewal_Status" in c.columns:
            status_counts = c["Renewal_Status"].fillna("Unknown").value_counts()
            st.bar_chart(status_counts)
        else:
            st.info("Renewal status is unavailable.")

    with right:
        st.subheader("Customers by tier")
        if "Customer_Tier" in c.columns:
            tier_counts = c["Customer_Tier"].fillna("Unknown").value_counts()
            st.bar_chart(tier_counts)
        else:
            st.info("Customer tier is unavailable.")

    st.subheader("Key business questions")
    st.markdown("""
    - Are sales activities producing valuable customers?
    - Are marketing campaigns generating activations, not just leads?
    - Are support delays affecting customer satisfaction?
    - Are customer retention and expansion strong enough to support growth?
    - Do acquisition costs and customer lifetime value indicate healthy economics?
    """)


# =========================================================
# 2. SALES
# =========================================================
with tabs[1]:
    st.header("Sales performance")

    show_kpis([
        ("Pipeline records", f"{len(s):,}"),
        ("Total deal value", money(numeric_sum(s, "Deal_Value_USD"))),
        ("Average deal value", money(numeric_mean(s, "Deal_Value_USD"))),
        ("Average discount", metric_value(
            numeric_mean(s, "Discount_Pct"), "%"
        )),
    ])

    left, right = st.columns(2)

    with left:
        st.subheader("Deal value by sales stage")
        if {"Sales_Stage", "Deal_Value_USD"}.issubset(s.columns):
            chart = s.groupby("Sales_Stage")["Deal_Value_USD"].sum()
            st.bar_chart(chart)
        else:
            st.info("Sales stage or deal value is unavailable.")

    with right:
        st.subheader("Deal value by source")
        if {"Deal_Source", "Deal_Value_USD"}.issubset(s.columns):
            chart = s.groupby("Deal_Source")["Deal_Value_USD"].sum()
            st.bar_chart(chart)
        else:
            st.info("Deal source or deal value is unavailable.")

    st.subheader("Sales by region")
    if {"Region", "Deal_Value_USD"}.issubset(s.columns):
        st.bar_chart(s.groupby("Region")["Deal_Value_USD"].sum())

    if "Upsell_Flag" in s.columns:
        st.subheader("Upsell activity")
        st.write(s["Upsell_Flag"].fillna("Unknown").value_counts())

    st.subheader("Sales records")
    st.dataframe(s, use_container_width=True, hide_index=True)


# =========================================================
# 3. MARKETING
# =========================================================
with tabs[2]:
    st.header("Marketing campaign performance")

    show_kpis([
        ("Campaigns", f"{len(m):,}"),
        ("Actual spend", money(numeric_sum(m, "Actual_Spend_USD"))),
        ("Leads generated", f"{numeric_sum(m, 'Leads_Generated'):,.0f}"),
        ("Activations", f"{numeric_sum(m, 'Activations'):,.0f}"),
        ("Average activation rate", metric_value(
            numeric_mean(m, "Activation_Rate_Pct"), "%"
        )),
    ])

    left, right = st.columns(2)

    with left:
        st.subheader("Spend by channel")
        if {"Channel", "Actual_Spend_USD"}.issubset(m.columns):
            st.bar_chart(m.groupby("Channel")["Actual_Spend_USD"].sum())
        else:
            st.info("Channel or actual spend is unavailable.")

    with right:
        st.subheader("Activations by campaign type")
        if {"Campaign_Type", "Activations"}.issubset(m.columns):
            st.bar_chart(m.groupby("Campaign_Type")["Activations"].sum())
        else:
            st.info("Campaign type or activations are unavailable.")

    st.subheader("Campaign comparison")
    wanted = [
        col for col in [
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
        ] if col in m.columns
    ]

    if wanted:
        st.dataframe(m[wanted], use_container_width=True, hide_index=True)


# =========================================================
# 4. SUPPORT
# =========================================================
with tabs[3]:
    st.header("Customer support performance")

    show_kpis([
        ("Tickets", f"{len(t):,}"),
        ("Average resolution hours", metric_value(
            numeric_mean(t, "Resolution_Hours"), " hrs"
        )),
        ("Average CSAT", metric_value(
            numeric_mean(t, "CSAT_Score")
        )),
        ("SLA met rate", metric_value(
            numeric_mean(
                t.assign(
                    _sla=pd.to_numeric(t["SLA_Met"], errors="coerce")
                ),
                "_sla"
            ) * 100 if "SLA_Met" in t.columns else None,
            "%"
        )),
    ])

    left, right = st.columns(2)

    with left:
        st.subheader("Tickets by category")
        if "Category" in t.columns:
            st.bar_chart(t["Category"].fillna("Unknown").value_counts())

    with right:
        st.subheader("Tickets by priority")
        if "Priority" in t.columns:
            st.bar_chart(t["Priority"].fillna("Unknown").value_counts())

    st.subheader("Resolution time by category")
    if {"Category", "Resolution_Hours"}.issubset(t.columns):
        resolution = t.groupby("Category")["Resolution_Hours"].mean()
        st.bar_chart(resolution)

    st.subheader("Support records")
    st.dataframe(t, use_container_width=True, hide_index=True)


# =========================================================
# 5. FINANCIAL HEALTH
# =========================================================
with tabs[4]:
    st.header("Financial health")

    show_kpis([
        ("ARR in selected records", money(numeric_sum(f, "ARR_USD"))),
        ("Average CAC", money(numeric_mean(f, "CAC_USD"))),
        ("Average LTV", money(numeric_mean(f, "LTV_USD"))),
        ("Average LTV/CAC", metric_value(
            numeric_mean(f, "LTV_CAC_Ratio"), "x"
        )),
        ("Average runway", metric_value(
            numeric_mean(f, "Runway_Months"), " months"
        )),
    ])

    left, right = st.columns(2)

    with left:
        st.subheader("LTV/CAC by acquisition channel")
        if {"Acquisition_Channel", "LTV_CAC_Ratio"}.issubset(f.columns):
            st.bar_chart(
                f.groupby("Acquisition_Channel")["LTV_CAC_Ratio"].mean()
            )

    with right:
        st.subheader("Monthly churn by service line")
        if {"Service_Line", "Monthly_Churn_Rate_Pct"}.issubset(f.columns):
            st.bar_chart(
                f.groupby("Service_Line")["Monthly_Churn_Rate_Pct"].mean()
            )

    st.subheader("Cash balance and runway")
    if {"Cash_Balance_USD", "Runway_Months"}.issubset(f.columns):
        st.dataframe(
            f[[
                col for col in [
                    "Cohort", "Service_Line", "Scenario",
                    "Cash_Balance_USD", "Burn_Rate_USD",
                    "Runway_Months", "Gross_Margin_Pct",
                    "Budget_Variance_Pct",
                ] if col in f.columns
            ]],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Financial data may contain repeated records across customers, periods, "
        "or scenarios. Interpret totals according to the dataset's grain."
    )


# =========================================================
# 6. CUSTOMER HEALTH
# =========================================================
with tabs[5]:
    st.header("Customer health and retention")

    show_kpis([
        ("Customers in selection", f"{len(c):,}"),
        ("Average NPS score", metric_value(numeric_mean(c, "NPS_Score"))),
        ("Customers flagged at churn risk", f"{(
            c['Churn_Risk_Flag'].astype(str).str.lower().isin(
                ['yes', 'true', '1', 'high', 'at risk']
            ).sum()
        ) if 'Churn_Risk_Flag' in c.columns else 0:,}"),
        ("Customer MRR", money(numeric_sum(c, "MRR_USD"))),
    ])

    left, right = st.columns(2)

    with left:
        st.subheader("NPS score distribution")
        if "NPS_Score" in c.columns:
            st.bar_chart(c["NPS_Score"].dropna().value_counts().sort_index())

    with right:
        st.subheader("Churn risk flag")
        if "Churn_Risk_Flag" in c.columns:
            st.bar_chart(
                c["Churn_Risk_Flag"].fillna("Unknown").value_counts()
            )

    st.subheader("Customer breakdown by subscription plan")
    if "Subscribed_Plan" in c.columns:
        st.bar_chart(c["Subscribed_Plan"].fillna("Unknown").value_counts())

    st.subheader("Customer records")
    st.dataframe(c, use_container_width=True, hide_index=True)


# =========================================================
# 7. DATA QUALITY
# =========================================================
with tabs[6]:
    st.header("Data quality checks")

    st.write(
        "Review dataset size, missing values, duplicate records, and key fields "
        "before relying on the dashboard's results."
    )

    quality_rows = []

    for name, df in datasets.items():
        quality_rows.append({
            "Dataset": name,
            "Rows": len(df),
            "Columns": len(df.columns),
            "Duplicate rows": int(df.duplicated().sum()),
            "Missing cells": int(df.isna().sum().sum()),
            "Missing cells (%)": round(
                df.isna().sum().sum() / max(df.size, 1) * 100, 2
            ),
        })

    quality_df = pd.DataFrame(quality_rows)
    st.dataframe(quality_df, use_container_width=True, hide_index=True)

    st.subheader("Missing values by field")

    dataset_choice = st.selectbox(
        "Choose dataset",
        list(datasets.keys())
    )
    selected_df = datasets[dataset_choice]

    missing_df = (
        selected_df.isna()
        .sum()
        .rename("Missing values")
        .reset_index()
        .rename(columns={"index": "Column"})
    )
    missing_df["Missing (%)"] = (
        missing_df["Missing values"] / max(len(selected_df), 1) * 100
    ).round(2)

    st.dataframe(
        missing_df.sort_values("Missing values", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Dataset previews")
    st.dataframe(
        selected_df.head(100),
        use_container_width=True,
        hide_index=True,
    )


# ---------------- FOOTER ----------------
st.divider()
st.caption(
    "GenP Technologies fictional capstone dashboard. "
    "Use the results as analytical evidence, not as proof of causation."
)
