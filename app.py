
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
st.caption(
    "Analyzing customer growth, sales performance, marketing efficiency, "
    "support operations, and financial health."
)

# =====================================================
# 2. DATASET FILES
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
        errors.append(f"{filename} was not found in the GitHub repository.")
        continue

    try:
        datasets[dataset_name] = load_csv(
            str(file_path),
            file_path.stat().st_mtime
        )
    except Exception as error:
        errors.append(f"{filename}: {error}")


# Show dataset loading status
with st.expander("Dataset loading status", expanded=bool(errors)):
    for name, filename in REQUIRED_FILES.items():
        if name in datasets:
            st.success(
                f"{filename}: loaded successfully "
                f"({len(datasets[name]):,} rows)"
            )
        else:
            st.error(f"{filename}: not loaded")

    if errors:
        st.markdown("**Details**")
        for error in errors:
            st.write(f"- {error}")

        st.write("Files currently found in the app folder:")
        try:
            for file_path in sorted(DATA_DIR.iterdir()):
                if file_path.is_file():
                    st.write(f"- {file_path.name}")
        except Exception as error:
            st.write(f"Could not list files: {error}")


if not datasets:
    st.error(
        "No datasets could be loaded. Check that your CSV files "
        "are uploaded to the same GitHub folder as app.py."
    )
    st.stop()


# =====================================================
# 3. HELPER FUNCTIONS
# =====================================================

def get_df(name):
    return datasets.get(name, pd.DataFrame())


def has_columns(df, columns):
    return not df.empty and all(col in df.columns for col in columns)


def numeric_series(df, column):
    if column not in df.columns:
        return pd.Series(dtype="float64")

    return pd.to_numeric(df[column], errors="coerce")


def money(value):
    if pd.isna(value):
        return "N/A"

    return f"${value:,.0f}"


def percentage(value):
    if pd.isna(value):
        return "N/A"

    return f"{value:.1f}%"


def show_empty(message="No data available for this section."):
    st.info(message)


def show_bar_chart(df, category, value, title, top_n=10):
    if not has_columns(df, [category, value]):
        show_empty(f"Required columns for {title} are unavailable.")
        return

    chart_df = df[[category, value]].copy()
    chart_df[value] = pd.to_numeric(chart_df[value], errors="coerce")
    chart_df = chart_df.dropna(subset=[category, value])

    if chart_df.empty:
        show_empty(f"No usable data for {title}.")
        return

    chart_df = (
        chart_df.groupby(category, as_index=False)[value]
        .sum()
        .sort_values(value, ascending=False)
        .head(top_n)
        .set_index(category)
    )

    st.subheader(title)
    st.bar_chart(chart_df)


def show_metric(label, value):
    st.metric(label, value)


# =====================================================
# 4. DATA REFERENCES
# =====================================================

customers = get_df("Customers")
marketing = get_df("Marketing")
financials = get_df("Financials")
sales = get_df("Sales")
support = get_df("Support")


# =====================================================
# 5. SIDEBAR FILTERS
# =====================================================

st.sidebar.header("Dashboard Filters")

selected_region = "All"

region_sources = []

if "Region" in customers.columns:
    region_sources.append(customers["Region"])

if "Region" in sales.columns:
    region_sources.append(sales["Region"])

if "Target_Region" in marketing.columns:
    region_sources.append(marketing["Target_Region"])

if region_sources:
    regions = pd.concat(region_sources).dropna().astype(str).unique().tolist()
    regions = sorted(regions)

    selected_region = st.sidebar.selectbox(
        "Region",
        ["All"] + regions
    )

selected_tier = "All"

if "Customer_Tier" in customers.columns:
    tiers = sorted(
        customers["Customer_Tier"].dropna().astype(str).unique().tolist()
    )

    selected_tier = st.sidebar.selectbox(
        "Customer Tier",
        ["All"] + tiers
    )

selected_scenario = "All"

if "Scenario" in financials.columns:
    scenarios = sorted(
        financials["Scenario"].dropna().astype(str).unique().tolist()
    )

    selected_scenario = st.sidebar.selectbox(
        "Financial Scenario",
        ["All"] + scenarios
    )


# Apply filters where relevant
filtered_customers = customers.copy()
filtered_sales = sales.copy()
filtered_marketing = marketing.copy()
filtered_financials = financials.copy()
filtered_support = support.copy()

if selected_region != "All":
    if "Region" in filtered_customers.columns:
        filtered_customers = filtered_customers[
            filtered_customers["Region"].astype(str) == selected_region
        ]

    if "Region" in filtered_sales.columns:
        filtered_sales = filtered_sales[
            filtered_sales["Region"].astype(str) == selected_region
        ]

    if "Target_Region" in filtered_marketing.columns:
        filtered_marketing = filtered_marketing[
            filtered_marketing["Target_Region"].astype(str) == selected_region
        ]

    # Financial and support tables do not necessarily have a Region column.
    # Filter them through matching customer IDs when possible.
    if (
        "Customer_ID" in filtered_financials.columns
        and "Customer_ID" in filtered_customers.columns
    ):
        valid_ids = filtered_customers["Customer_ID"].dropna().unique()
        filtered_financials = filtered_financials[
            filtered_financials["Customer_ID"].isin(valid_ids)
        ]

    if (
        "Customer_ID" in filtered_support.columns
        and "Customer_ID" in filtered_customers.columns
    ):
        valid_ids = filtered_customers["Customer_ID"].dropna().unique()
        filtered_support = filtered_support[
            filtered_support["Customer_ID"].isin(valid_ids)
        ]

if selected_tier != "All" and "Customer_Tier" in filtered_customers.columns:
    filtered_customers = filtered_customers[
        filtered_customers["Customer_Tier"].astype(str) == selected_tier
    ]

    if (
        "Customer_ID" in filtered_financials.columns
        and "Customer_ID" in filtered_customers.columns
    ):
        valid_ids = filtered_customers["Customer_ID"].dropna().unique()
        filtered_financials = filtered_financials[
            filtered_financials["Customer_ID"].isin(valid_ids)
        ]

    if (
        "Customer_ID" in filtered_sales.columns
        and "Customer_ID" in filtered_customers.columns
    ):
        valid_ids = filtered_customers["Customer_ID"].dropna().unique()
        filtered_sales = filtered_sales[
            filtered_sales["Customer_ID"].isin(valid_ids)
        ]

    if (
        "Customer_ID" in filtered_support.columns
        and "Customer_ID" in filtered_customers.columns
    ):
        valid_ids = filtered_customers["Customer_ID"].dropna().unique()
        filtered_support = filtered_support[
            filtered_support["Customer_ID"].isin(valid_ids)
        ]

if selected_scenario != "All" and "Scenario" in filtered_financials.columns:
    filtered_financials = filtered_financials[
        filtered_financials["Scenario"].astype(str) == selected_scenario
    ]


# =====================================================
# 6. DASHBOARD TABS
# =====================================================

tabs = st.tabs([
    "Executive Overview",
    "Sales",
    "Marketing",
    "Support",
    "Financial Health",
    "Customer Health",
    "Data Quality"
])


# =====================================================
# TAB 1: EXECUTIVE OVERVIEW
# =====================================================

with tabs[0]:
    st.header("Executive Overview")

    col1, col2, col3, col4 = st.columns(4)

    # Customer metrics
    with col1:
        if not filtered_customers.empty:
            if "Customer_ID" in filtered_customers.columns:
                total_customers = filtered_customers["Customer_ID"].nunique()
            else:
                total_customers = len(filtered_customers)

            show_metric("Customers", f"{total_customers:,}")
        else:
            show_metric("Customers", "N/A")

    # Monthly recurring revenue
    with col2:
        if "MRR_USD" in filtered_customers.columns:
            mrr = numeric_series(filtered_customers, "MRR_USD").sum()
            show_metric("Customer MRR", money(mrr))
        else:
            show_metric("Customer MRR", "N/A")

    # Sales pipeline value
    with col3:
        if "Deal_Value_USD" in filtered_sales.columns:
            pipeline_value = numeric_series(
                filtered_sales, "Deal_Value_USD"
            ).sum()
            show_metric("Sales Deal Value", money(pipeline_value))
        else:
            show_metric("Sales Deal Value", "N/A")

    # Support tickets
    with col4:
        if not filtered_support.empty:
            show_metric("Support Tickets", f"{len(filtered_support):,}")
        else:
            show_metric("Support Tickets", "N/A")

    st.divider()

    left, right = st.columns(2)

    with left:
        show_bar_chart(
            filtered_sales,
            "Sales_Stage",
            "Deal_Value_USD",
            "Sales Deal Value by Stage"
        )

    with right:
        show_bar_chart(
            filtered_customers,
            "Industry",
            "MRR_USD",
            "Customer MRR by Industry"
        )

    st.subheader("Key Business Indicators")

    indicator_col1, indicator_col2, indicator_col3 = st.columns(3)

    with indicator_col1:
        if "NPS_Score" in filtered_customers.columns:
            nps = numeric_series(filtered_customers, "NPS_Score").mean()
            show_metric("Average NPS Score", f"{nps:.1f}" if pd.notna(nps) else "N/A")
        else:
            show_metric("Average NPS Score", "N/A")

    with indicator_col2:
        if "Activation_Rate_Pct" in filtered_marketing.columns:
            activation = numeric_series(
                filtered_marketing, "Activation_Rate_Pct"
            ).mean()
            show_metric(
                "Average Activation Rate",
                percentage(activation) if pd.notna(activation) else "N/A"
            )
        else:
            show_metric("Average Activation Rate", "N/A")

    with indicator_col3:
        if "SLA_Met" in filtered_support.columns:
            sla = filtered_support["SLA_Met"].astype(str).str.lower().isin(
                ["true", "1", "yes", "y"]
            ).mean() * 100
            show_metric("Tickets Meeting SLA", percentage(sla))
        else:
            show_metric("Tickets Meeting SLA", "N/A")


# =====================================================
# TAB 2: SALES
# =====================================================

with tabs[1]:
    st.header("Sales Performance")

    col1, col2, col3 = st.columns(3)

    with col1:
        if "Deal_ID" in filtered_sales.columns:
            show_metric(
                "Total Deals",
                f"{filtered_sales['Deal_ID'].nunique():,}"
            )
        else:
            show_metric("Total Deals", f"{len(filtered_sales):,}")

    with col2:
        if "Deal_Value_USD" in filtered_sales.columns:
            total_value = numeric_series(
                filtered_sales, "Deal_Value_USD"
            ).sum()
            show_metric("Total Deal Value", money(total_value))
        else:
            show_metric("Total Deal Value", "N/A")

    with col3:
        if "Days_to_Close" in filtered_sales.columns:
            avg_days = numeric_series(
                filtered_sales, "Days_to_Close"
            ).mean()
            show_metric(
                "Average Days to Close",
                f"{avg_days:.1f}" if pd.notna(avg_days) else "N/A"
            )
        else:
            show_metric("Average Days to Close", "N/A")

    left, right = st.columns(2)

    with left:
        show_bar_chart(
            filtered_sales,
            "Sales_Stage",
            "Deal_Value_USD",
            "Deal Value by Sales Stage"
        )

    with right:
        show_bar_chart(
            filtered_sales,
            "Deal_Source",
            "Deal_Value_USD",
            "Deal Value by Source"
        )

    show_bar_chart(
        filtered_sales,
        "Sales_Rep_Name",
        "Deal_Value_USD",
        "Deal Value by Sales Representative"
    )

    if not filtered_sales.empty:
        display_columns = [
            "Deal_ID", "Service_Line", "Sales_Stage",
            "Deal_Value_USD", "Deal_Source", "Region"
        ]
        available_columns = [
            col for col in display_columns if col in filtered_sales.columns
        ]

        if available_columns:
            st.subheader("Sales Pipeline Records")
            st.dataframe(
                filtered_sales[available_columns],
                use_container_width=True,
                hide_index=True
            )


# =====================================================
# TAB 3: MARKETING
# =====================================================

with tabs[2]:
    st.header("Marketing Performance")

    col1, col2, col3 = st.columns(3)

    with col1:
        if "Actual_Spend_USD" in filtered_marketing.columns:
            spend = numeric_series(
                filtered_marketing, "Actual_Spend_USD"
            ).sum()
            show_metric("Actual Marketing Spend", money(spend))
        else:
            show_metric("Actual Marketing Spend", "N/A")

    with col2:
        if "Leads_Generated" in filtered_marketing.columns:
            leads = numeric_series(
                filtered_marketing, "Leads_Generated"
            ).sum()
            show_metric(
                "Leads Generated",
                f"{leads:,.0f}" if pd.notna(leads) else "N/A"
            )
        else:
            show_metric("Leads Generated", "N/A")

    with col3:
        if "Activations" in filtered_marketing.columns:
            activations = numeric_series(
                filtered_marketing, "Activations"
            ).sum()
            show_metric(
                "Activations",
                f"{activations:,.0f}" if pd.notna(activations) else "N/A"
            )
        else:
            show_metric("Activations", "N/A")

    left, right = st.columns(2)

    with left:
        show_bar_chart(
            filtered_marketing,
            "Campaign_Type",
            "Actual_Spend_USD",
            "Marketing Spend by Campaign Type"
        )

    with right:
        show_bar_chart(
            filtered_marketing,
            "Channel",
            "Leads_Generated",
            "Leads Generated by Channel"
        )

    if (
        "Actual_Spend_USD" in filtered_marketing.columns
        and "Leads_Generated" in filtered_marketing.columns
    ):
        spend = numeric_series(filtered_marketing, "Actual_Spend_USD")
        leads = numeric_series(filtered_marketing, "Leads_Generated")

        total_spend = spend.sum()
        total_leads = leads.sum()

        if total_leads > 0:
            st.metric(
                "Average Cost per Lead",
                money(total_spend / total_leads)
            )
        else:
            st.metric("Average Cost per Lead", "N/A")

    if not filtered_marketing.empty:
        display_columns = [
            "Campaign_Name", "Campaign_Type", "Channel",
            "Actual_Spend_USD", "Leads_Generated",
            "Qualified_Leads", "Activations", "Activation_Rate_Pct"
        ]
        available_columns = [
            col for col in display_columns if col in filtered_marketing.columns
        ]

        if available_columns:
            st.subheader("Campaign Details")
            st.dataframe(
                filtered_marketing[available_columns],
                use_container_width=True,
                hide_index=True
            )


# =====================================================
# TAB 4: SUPPORT
# =====================================================

with tabs[3]:
    st.header("Customer Support Performance")

    col1, col2, col3 = st.columns(3)

    with col1:
        show_metric("Total Tickets", f"{len(filtered_support):,}")

    with col2:
        if "Resolution_Hours" in filtered_support.columns:
            avg_resolution = numeric_series(
                filtered_support, "Resolution_Hours"
            ).mean()
            show_metric(
                "Average Resolution Hours",
                f"{avg_resolution:.1f}"
                if pd.notna(avg_resolution) else "N/A"
            )
        else:
            show_metric("Average Resolution Hours", "N/A")

    with col3:
        if "CSAT_Score" in filtered_support.columns:
            csat = numeric_series(filtered_support, "CSAT_Score").mean()
            show_metric(
                "Average CSAT Score",
                f"{csat:.2f}" if pd.notna(csat) else "N/A"
            )
        else:
            show_metric("Average CSAT Score", "N/A")

    left, right = st.columns(2)

    with left:
        if "Category" in filtered_support.columns:
            st.subheader("Tickets by Category")
            category_counts = filtered_support["Category"].value_counts()
            st.bar_chart(category_counts)

        elif "Priority" in filtered_support.columns:
            st.subheader("Tickets by Priority")
            st.bar_chart(filtered_support["Priority"].value_counts())
        else:
            show_empty("Ticket category data is unavailable.")

    with right:
        if "Priority" in filtered_support.columns:
            st.subheader("Tickets by Priority")
            st.bar_chart(filtered_support["Priority"].value_counts())
        else:
            show_empty("Ticket priority data is unavailable.")

    if "SLA_Met" in filtered_support.columns:
        st.subheader("Service Level Agreement Performance")

        sla_values = filtered_support["SLA_Met"].astype(str).str.lower()
        sla_counts = sla_values.map(
            lambda value: (
                "Met" if value in ["true", "1", "yes", "y"]
                else "Not Met" if value in ["false", "0", "no", "n"]
                else "Unknown"
            )
        ).value_counts()

        st.bar_chart(sla_counts)

    if not filtered_support.empty:
        display_columns = [
            "Ticket_ID", "Category", "Priority", "Status",
            "Resolution_Hours", "SLA_Met", "CSAT_Score",
            "Contact_Channel", "Automation_Flag"
        ]
        available_columns = [
            col for col in display_columns if col in filtered_support.columns
        ]

        if available_columns:
            st.subheader("Support Ticket Details")
            st.dataframe(
                filtered_support[available_columns],
                use_container_width=True,
                hide_index=True
            )


# =====================================================
# TAB 5: FINANCIAL HEALTH
# =====================================================

with tabs[4]:
    st.header("Financial Health")

    col1, col2, col3 = st.columns(3)

    with col1:
        if "MRR_USD" in filtered_financials.columns:
            mrr = numeric_series(filtered_financials, "MRR_USD").sum()
            show_metric("Total MRR in Records", money(mrr))
        else:
            show_metric("Total MRR in Records", "N/A")

    with col2:
        if "ARR_USD" in filtered_financials.columns:
            arr = numeric_series(filtered_financials, "ARR_USD").sum()
            show_metric("Total ARR in Records", money(arr))
        else:
            show_metric("Total ARR in Records", "N/A")

    with col3:
        if "Burn_Rate_USD" in filtered_financials.columns:
            burn = numeric_series(
                filtered_financials, "Burn_Rate_USD"
            ).mean()
            show_metric(
                "Average Burn Rate",
                money(burn) if pd.notna(burn) else "N/A"
            )
        else:
            show_metric("Average Burn Rate", "N/A")

    col4, col5, col6 = st.columns(3)

    with col4:
        if "Cash_Balance_USD" in filtered_financials.columns:
            cash = numeric_series(
                filtered_financials, "Cash_Balance_USD"
            ).mean()
            show_metric(
                "Average Cash Balance",
                money(cash) if pd.notna(cash) else "N/A"
            )
        else:
            show_metric("Average Cash Balance", "N/A")

    with col5:
        if "Runway_Months" in filtered_financials.columns:
            runway = numeric_series(
                filtered_financials, "Runway_Months"
            ).mean()
            show_metric(
                "Average Runway (Months)",
                f"{runway:.1f}" if pd.notna(runway) else "N/A"
            )
        else:
            show_metric("Average Runway (Months)", "N/A")

    with col6:
        if "LTV_CAC_Ratio" in filtered_financials.columns:
            ratio = numeric_series(
                filtered_financials, "LTV_CAC_Ratio"
            ).mean()
            show_metric(
                "Average LTV:CAC Ratio",
                f"{ratio:.2f}" if pd.notna(ratio) else "N/A"
            )
        else:
            show_metric("Average LTV:CAC Ratio", "N/A")

    left, right = st.columns(2)

    with left:
        show_bar_chart(
            filtered_financials,
            "Service_Line",
            "MRR_USD",
            "MRR by Service Line"
        )

    with right:
        show_bar_chart(
            filtered_financials,
            "Acquisition_Channel",
            "CAC_USD",
            "Customer Acquisition Cost by Channel"
        )

    show_bar_chart(
        filtered_financials,
        "Cohort",
        "LTV_CAC_Ratio",
        "LTV:CAC Ratio by Cohort"
    )

    if not filtered_financials.empty:
        display_columns = [
            "Cohort", "Service_Line", "Acquisition_Channel",
            "Scenario", "MRR_USD", "ARR_USD", "CAC_USD",
            "LTV_USD", "LTV_CAC_Ratio", "Gross_Margin_Pct",
            "Monthly_Churn_Rate_Pct", "Runway_Months"
        ]
        available_columns = [
            col for col in display_columns
            if col in filtered_financials.columns
        ]

        if available_columns:
            st.subheader("Financial Records")
            st.dataframe(
                filtered_financials[available_columns],
                use_container_width=True,
                hide_index=True
            )


# =====================================================
# TAB 6: CUSTOMER HEALTH
# =====================================================

with tabs[5]:
    st.header("Customer Health and Retention")

    col1, col2, col3 = st.columns(3)

    with col1:
        if "Churn_Risk_Flag" in filtered_customers.columns:
            risk = filtered_customers["Churn_Risk_Flag"].astype(str).str.lower()
            high_risk = risk.isin(["true", "1", "yes", "y"]).sum()
            show_metric("Customers Flagged for Churn Risk", f"{high_risk:,}")
        else:
            show_metric("Customers Flagged for Churn Risk", "N/A")

    with col2:
        if "NPS_Score" in filtered_customers.columns:
            nps = numeric_series(filtered_customers, "NPS_Score").mean()
            show_metric(
                "Average NPS",
                f"{nps:.1f}" if pd.notna(nps) else "N/A"
            )
        else:
            show_metric("Average NPS", "N/A")

    with col3:
        if "Renewal_Status" in filtered_customers.columns:
            renewed = filtered_customers["Renewal_Status"].astype(str).str.lower()
            renewed_count = renewed.isin(
                ["renewed", "active", "yes"]
            ).sum()
            show_metric("Renewed / Active Customers", f"{renewed_count:,}")
        else:
            show_metric("Renewed / Active Customers", "N/A")

    left, right = st.columns(2)

    with left:
        if "Customer_Tier" in filtered_customers.columns:
            st.subheader("Customers by Tier")
            st.bar_chart(filtered_customers["Customer_Tier"].value_counts())
        else:
            show_empty("Customer tier information is unavailable.")

    with right:
        if "Renewal_Status" in filtered_customers.columns:
            st.subheader("Customers by Renewal Status")
            st.bar_chart(
                filtered_customers["Renewal_Status"].value_counts()
            )
        else:
            show_empty("Renewal status information is unavailable.")

    show_bar_chart(
        filtered_customers,
        "Industry",
        "MRR_USD",
        "Monthly Recurring Revenue by Industry"
    )

    if not filtered_customers.empty:
        display_columns = [
            "Company_Name", "Industry", "Company_Size",
            "Customer_Tier", "Region", "Renewal_Status",
            "MRR_USD", "NPS_Score", "Subscribed_Plan",
            "Churn_Risk_Flag"
        ]
        available_columns = [
            col for col in display_columns if col in filtered_customers.columns
        ]

        if available_columns:
            st.subheader("Customer Records")
            st.dataframe(
                filtered_customers[available_columns],
                use_container_width=True,
                hide_index=True
            )


# =====================================================
# TAB 7: DATA QUALITY
# =====================================================

with tabs[6]:
    st.header("Data Quality Overview")

    quality_rows = []

    for name, df in datasets.items():
        quality_rows.append({
            "Dataset": name,
            "Rows": len(df),
            "Columns": len(df.columns),
            "Missing Cells": int(df.isna().sum().sum()),
            "Duplicate Rows": int(df.duplicated().sum()),
            "Memory Usage (KB)": round(
                df.memory_usage(deep=True).sum() / 1024, 1
            )
        })

    quality_df = pd.DataFrame(quality_rows)

    st.dataframe(
        quality_df,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Missing Values by Dataset")

    for name, df in datasets.items():
        missing = df.isna().sum()
        missing = missing[missing > 0].sort_values(ascending=False)

        with st.expander(f"{name}: missing-value details"):
            if missing.empty:
                st.success("No missing values found.")
            else:
                missing_df = missing.rename("Missing Cells").reset_index()
                missing_df.columns = ["Column", "Missing Cells"]
                st.dataframe(
                    missing_df,
                    use_container_width=True,
                    hide_index=True
                )

    st.subheader("Dataset Preview")

    selected_dataset = st.selectbox(
        "Choose a dataset to inspect",
        list(datasets.keys())
    )

    st.dataframe(
        datasets[selected_dataset].head(20),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Data quality indicators describe the loaded CSV files. "
        "They do not automatically correct missing or duplicate records."
    )


# =====================================================
# 7. FOOTER
# =====================================================

st.divider()
st.caption(
    "GenP Technologies | Business Analytics Capstone Project"
)
