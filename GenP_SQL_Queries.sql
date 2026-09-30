-- TASK 4
-- ==================================================================
-- QUESTION 1: MARKETING ANALYSIS
-- ==================================================================
-- Calculate win rate, average closed-won deal value, and total closed-won
-- sales value by Campaign Type.
-- Sales_Pipeline does not contain ARR_USD, so total closed-won deal value
-- is used as the available sales-value proxy.
-- Identify which Campaign Types generate the highest-quality pipeline.
USE genp_task4;

SELECT
    mc.Campaign_Type,

    COUNT(DISTINCT CASE
        WHEN sp.Sales_Stage IN ('Closed Won', 'Closed Lost')
        THEN sp.Deal_ID
    END) AS closed_deals,

    COUNT(DISTINCT CASE
        WHEN sp.Sales_Stage = 'Closed Won'
        THEN sp.Deal_ID
    END) AS closed_won,

    COUNT(DISTINCT CASE
        WHEN sp.Sales_Stage = 'Closed Lost'
        THEN sp.Deal_ID
    END) AS closed_lost,

    ROUND(
        100.0 * COUNT(DISTINCT CASE
            WHEN sp.Sales_Stage = 'Closed Won'
            THEN sp.Deal_ID
        END)
        /
        NULLIF(
            COUNT(DISTINCT CASE
                WHEN sp.Sales_Stage IN ('Closed Won', 'Closed Lost')
                THEN sp.Deal_ID
            END), 0
        ), 2
    ) AS win_rate_pct,

    ROUND(
        AVG(CASE
            WHEN sp.Sales_Stage = 'Closed Won'
            THEN sp.Deal_Value_USD_Clean
        END), 2
    ) AS avg_closed_won_deal_value_usd,

    ROUND(
        SUM(CASE
            WHEN sp.Sales_Stage = 'Closed Won'
            THEN sp.Deal_Value_USD_Clean
            ELSE 0
        END), 2
    ) AS total_closed_won_deal_value_usd

FROM vw_marketing_campaigns_clean mc

LEFT JOIN vw_sales_pipeline_clean sp
    ON sp.Campaign_ID = mc.Campaign_ID

GROUP BY mc.Campaign_Type

ORDER BY win_rate_pct DESC;

-- Query Output:
-- Highest win rate: Email Nurture - 62.50%
-- Second highest: Paid Search - 62.20%
-- Highest total closed-won deal value: Paid Search - approximately $3.47M

# 4. Business Answer -
-- Email Nurture generated the highest-quality pipeline based on win rate at
-- 62.50%, closely followed by Paid Search at 62.20%. Paid Search generated
-- the highest total closed-won deal value at approximately $3.47 million.
-- Therefore, Email Nurture had the highest pipeline quality by win rate,
-- while Paid Search had the strongest monetary contribution.

-- =====================================================
-- QUESTION 2: MARKETING ANALYSIS
-- =====================================================
-- Compare Activation_Rate_Pct across Campaign_Type and Target_Audience.
-- Determine whether In-App Nudge campaigns produce meaningfully higher
-- activation rates than paid acquisition campaigns.



-- PART A: Activation Rate by Campaign Type and Target Audience

SELECT
    Campaign_Type,
    Target_Audience,

    COUNT(*) AS campaign_count,

    SUM(Leads_Generated) AS total_leads,

    SUM(Activations) AS total_activations,

    ROUND(
        100.0 * SUM(Activations)
        / NULLIF(SUM(Leads_Generated), 0),
        2
    ) AS weighted_activation_rate_pct

FROM vw_marketing_campaigns_clean

GROUP BY
    Campaign_Type,
    Target_Audience

ORDER BY
    weighted_activation_rate_pct DESC;


-- Query Output:
-- In-App Nudge had the highest activation rate across all four target audiences.
-- All Segments: 25.79%
-- Enterprise: 25.11%
-- SMB: 24.58%
-- Mid-Market: 23.61%

# 4. Business Answer -
# In-App Nudge achieved the highest activation rates across all four
# target audiences. The highest result was 25.79% for All Segments,
# followed by Enterprise at 25.11%, SMB at 24.58%, and Mid-Market at
# 23.61%. The next highest result was Paid Search targeting SMB at
# 21.68%. In contrast, the lowest activation rate was Paid Search
# targeting Enterprise at 6.47%. Overall, the results show that
# In-App Nudge consistently performed strongly across different target
# audiences and was the best-performing campaign type for user activation.


-- PART B: In-App Nudge vs Paid Acquisition

SELECT
    CASE
        WHEN Campaign_Type = 'In-App Nudge'
            THEN 'In-App Nudge'

        WHEN Campaign_Type IN ('Paid Search', 'LinkedIn Ads')
            THEN 'Paid Acquisition'
    END AS comparison_group,

    SUM(Leads_Generated) AS total_leads,

    SUM(Activations) AS total_activations,

    ROUND(
        100.0 * SUM(Activations)
        / NULLIF(SUM(Leads_Generated), 0),
        2
    ) AS weighted_activation_rate_pct

FROM vw_marketing_campaigns_clean

WHERE Campaign_Type IN (
    'In-App Nudge',
    'Paid Search',
    'LinkedIn Ads'
)

GROUP BY comparison_group

ORDER BY weighted_activation_rate_pct DESC;

# 3. Query Output
# In-App Nudge: 22,371 total leads, 5,471 total activations, 24.46% activation rate.
# Paid Acquisition: 49,362 total leads, 7,393 total activations, 14.98% activation rate.

# 4. Business Answer -
-- In-App Nudge campaigns achieved a 24.46% activation rate compared with
-- 14.98% for Paid Acquisition campaigns, a difference of 9.48 percentage
-- points. This indicates substantially higher activation for In-App Nudge
-- campaigns. Statistical significance will be assessed separately in Task 5.

-- =====================================================
-- QUESTION 3: MARKETING ANALYSIS
-- =====================================================
-- Calculate cost per acquired customer by Channel.
-- Compare marketing spend with Closed Won deals attributed
-- to each channel.

-- PART A: Cost per Acquired Customer by Channel
-- Campaign spend is aggregated at campaign level before joining
-- to sales results to prevent duplicated marketing spend.

USE genp_task4;

WITH campaign_spend AS (
    SELECT
        Campaign_ID,
        Channel,
        Actual_Spend_USD
    FROM vw_marketing_campaigns_clean
),

campaign_wins AS (
    SELECT
        Campaign_ID,
        COUNT(DISTINCT Deal_ID) AS closed_won_deals
    FROM vw_sales_pipeline_clean
    WHERE Sales_Stage = 'Closed Won'
      AND Campaign_ID IS NOT NULL
    GROUP BY Campaign_ID
)

SELECT
    cs.Channel,

    ROUND(
        SUM(cs.Actual_Spend_USD),
        2
    ) AS total_actual_spend_usd,

    SUM(
        COALESCE(cw.closed_won_deals, 0)
    ) AS closed_won_deals,

    ROUND(
        SUM(cs.Actual_Spend_USD)
        /
        NULLIF(
            SUM(COALESCE(cw.closed_won_deals, 0)),
            0
        ),
        2
    ) AS cost_per_acquired_customer_usd

FROM campaign_spend cs

LEFT JOIN campaign_wins cw
    ON cw.Campaign_ID = cs.Campaign_ID

GROUP BY
    cs.Channel

ORDER BY
    cost_per_acquired_customer_usd;


-- Query Output:
-- Lowest cost: LinkedIn - $39,676.90
-- Highest cost: In-App - $87,744.61

-- Business Answer:
-- LinkedIn is the most cost-efficient channel, while In-App is the least
-- cost-efficient based on cost per acquired customer.
CREATE OR REPLACE VIEW vw_saas_financials_clean AS
SELECT
    Record_ID,
    Customer_ID,
    Cohort,
    Service_Line,
    Acquisition_Channel,
    Scenario,
    MRR_USD,
    ARR_USD,
    CAC_USD,
    LTV_USD,
    LTV_CAC_Ratio,
    Monthly_Churn_Rate_Pct,
    Expansion_MRR_USD,
    Contraction_MRR_USD,
    Burn_Rate_USD,
    Cash_Balance_USD,
    Runway_Months,
    Gross_Margin_Pct,
    Budget_Variance_Pct,
    Period_Start_Date,
    Period_End_Date
FROM (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY Record_ID
               ORDER BY Record_ID
           ) AS rn
    FROM saas_financials_raw
) x
WHERE rn = 1;
-- PART B: Compare LTV with CAC by Acquisition Channel.
-- The SaaS Financials acquisition taxonomy is analyzed separately
-- because its channel names do not match Marketing_Campaigns.Channel.

SELECT
    Acquisition_Channel,

    COUNT(DISTINCT Customer_ID) AS customers,

    ROUND(
        AVG(CAC_USD),
        2
    ) AS avg_cac_usd,

    ROUND(
        AVG(LTV_USD),
        2
    ) AS avg_ltv_usd,

    ROUND(
        AVG(LTV_CAC_Ratio),
        2
    ) AS avg_ltv_cac_ratio,

    CASE
        WHEN AVG(LTV_CAC_Ratio) >= 3
            THEN 'Viable'
        ELSE 'Not Viable'
    END AS ltv_cac_assessment
    
FROM vw_saas_financials_clean

WHERE CAC_USD IS NOT NULL
  AND LTV_USD IS NOT NULL
  AND LTV_CAC_Ratio IS NOT NULL
  AND LTV_CAC_Ratio >= 0

GROUP BY
    Acquisition_Channel

ORDER BY
    avg_ltv_cac_ratio DESC;

-- Query Output:
-- Highest LTV/CAC: Product-Led Signup - 1,762.07
-- Lowest LTV/CAC: LinkedIn Ads - 204.83
-- All listed acquisition channels are above the 3x analytical benchmark.

-- Business Answer:
-- Product-Led Signup has the strongest LTV/CAC at 1,762.07,
-- while LinkedIn Ads has the lowest at 204.83.
-- Using 3x as an analytical benchmark, all listed acquisition
-- channels have viable LTV/CAC ratios.

-- ---------------------------------------------------------------------
-- PART C: Channel Taxonomy Reconciliation
-- The Marketing_Campaigns.Channel and SaaS_Financials.Acquisition_Channel
-- use different naming taxonomies and therefore cannot be directly joined
-- without a documented business mapping.
-- This query documents the available values for transparent reconciliation.

SELECT DISTINCT
    Channel AS marketing_channel
FROM vw_marketing_campaigns_clean
ORDER BY Channel;

SELECT DISTINCT
    Acquisition_Channel AS saas_acquisition_channel
FROM vw_saas_financials_clean
ORDER BY Acquisition_Channel;

-- Business Answer:
-- Marketing and SaaS use different channel taxonomies.
-- Therefore, a direct exact-name join would be invalid.
-- The two channel analyses are reported separately rather than
-- creating an unsupported join assumption.
-- =====================================================
-- QUESTION 4: OPERATIONS ANALYSIS
-- =====================================================
CREATE OR REPLACE VIEW vw_support_tickets_clean AS
SELECT
    Ticket_ID,
    Customer_ID,
    Deal_ID,
    Category,
    Priority,
    Status,
    CASE
    WHEN Created_Date LIKE '%/%/%'
        THEN STR_TO_DATE(Created_Date, '%d/%m/%Y')
    ELSE STR_TO_DATE(Created_Date, '%Y-%m-%d')
END AS Created_Date_Clean,

CASE
    WHEN Resolved_Date LIKE '%/%/%'
        THEN STR_TO_DATE(Resolved_Date, '%d/%m/%Y')
    ELSE STR_TO_DATE(Resolved_Date, '%Y-%m-%d')
END AS Resolved_Date_Clean,
    CASE
        WHEN Resolution_Hours >= 0 THEN Resolution_Hours
        ELSE NULL
    END AS Resolution_Hours_Clean,
    SLA_Target_Hours,
    SLA_Met,
    Assigned_Agent,
    Contact_Channel,
    CSAT_Score,
    CASE
        WHEN LOWER(TRIM(Automation_Flag)) IN ('1','true','yes')
            THEN 'Automated'
        ELSE 'Human'
    END AS Automation_Type
FROM (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY Ticket_ID
               ORDER BY Ticket_ID
           ) AS rn
    FROM support_tickets_raw
) x
WHERE rn = 1;
-- PART A: SLA Breach Rate by Priority and Category
-- Calculate the percentage of valid resolved tickets that
-- breached their SLA target.

USE genp_task4;

SELECT
    Priority,
    Category,

    COUNT(*) AS valid_resolved_tickets,

    SUM(
        CASE
            WHEN Resolution_Hours_Clean > SLA_Target_Hours
            THEN 1
            ELSE 0
        END
    ) AS sla_breaches,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN Resolution_Hours_Clean > SLA_Target_Hours
                THEN 1
                ELSE 0
            END
        )
        /
        NULLIF(COUNT(*), 0),
        2
    ) AS sla_breach_rate_pct

FROM vw_support_tickets_clean

WHERE Status = 'Resolved'
  AND Resolution_Hours_Clean IS NOT NULL
  AND SLA_Target_Hours IS NOT NULL

GROUP BY
    Priority,
    Category

ORDER BY
    sla_breach_rate_pct DESC;


-- Query Output:
-- Highest SLA breach: Critical - Data Discrepancy (71.79%)
-- Next highest: Critical - Feature Request (71.43%)
-- Lowest SLA breach: Critical - Access & Permissions (50.00%)

-- Business Answer:
-- Critical Data Discrepancy and Critical Feature Request have the highest
-- SLA breach rates, while Critical Access & Permissions has the lowest.

-- PART B: Automation vs Human Handling and CSAT
-- Query 1 measures the proportion of automated vs human handling
-- across all valid tickets.
-- Query 2 measures average CSAT only for tickets with a CSAT score.

USE genp_task4;

-- ---------------------------------------------------------------------
-- Query 1: Automation vs Human handling proportion

SELECT
    Automation_Type,
    COUNT(*) AS total_tickets,

    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS proportion_pct

FROM vw_support_tickets_clean

WHERE Automation_Type IN ('Automated', 'Human')

GROUP BY Automation_Type

ORDER BY proportion_pct DESC;

-- Query Output:
-- Human: 66.39%
-- Automated: 33.61%

-- Business Answer:
-- Most tickets are handled by humans (66.39%), while 33.61% are handled automatically.
-- ---------------------------------------------------------------------
-- Query 2: Average CSAT by handling type

SELECT
    Automation_Type,

    ROUND(
        AVG(CSAT_Score),
        2
    ) AS avg_csat

FROM vw_support_tickets_clean

WHERE Automation_Type IN ('Automated', 'Human')
  AND CSAT_Score IS NOT NULL

GROUP BY
    Automation_Type

ORDER BY
    avg_csat DESC;

-- Query Output:
-- Automated average CSAT: 1.27
-- Human average CSAT: 1.23

-- Business Answer:
-- Automated tickets had a slightly higher average CSAT score of 1.27
-- compared with 1.23 for human-handled tickets. The small difference
-- indicates only a slight difference in average CSAT and does not establish
-- that automation causes higher customer satisfaction.
CREATE OR REPLACE VIEW vw_customers_clean AS
SELECT
    Customer_ID,
    Company_Name,
    Industry,
    Company_Size,
    Customer_Tier,
    Region,
    Onboarding_Date,
    Renewal_Status,
    MRR_USD,
    NPS_Score,
    Subscribed_Plan,
    CSM_Name,
    Contract_Months,
    Churn_Risk_Flag
FROM (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY Customer_ID
               ORDER BY Customer_ID
           ) AS rn
    FROM customers_raw
) x
WHERE rn = 1;

-- PART C: Customers with >5 High-Priority or Critical Tickets
-- Identify customers with more than 5 High/Critical tickets
-- within any rolling 6-month window.

USE genp_task4;

WITH high_priority_tickets AS (
    SELECT
        Customer_ID,
        Created_Date_Clean
    FROM vw_support_tickets_clean
    WHERE Priority IN ('High', 'Critical')
      AND Customer_ID IS NOT NULL
      AND Created_Date_Clean IS NOT NULL
),

rolling_ticket_counts AS (
    SELECT
        t1.Customer_ID,
        t1.Created_Date_Clean AS window_start_date,
        COUNT(*) AS high_critical_ticket_count
    FROM high_priority_tickets t1
    JOIN high_priority_tickets t2
        ON t1.Customer_ID = t2.Customer_ID
       AND t2.Created_Date_Clean BETWEEN
           t1.Created_Date_Clean
           AND DATE_ADD(t1.Created_Date_Clean, INTERVAL 6 MONTH)
    GROUP BY
        t1.Customer_ID,
        t1.Created_Date_Clean
    HAVING COUNT(*) > 5
),

flagged_customers AS (
    SELECT DISTINCT
        Customer_ID
    FROM rolling_ticket_counts
),

flagged_status AS (
    SELECT
        c.Renewal_Status,
        COUNT(DISTINCT c.Customer_ID) AS flagged_customers
    FROM flagged_customers f
    JOIN vw_customers_clean c
        ON f.Customer_ID = c.Customer_ID
    GROUP BY c.Renewal_Status
),

overall_status AS (
    SELECT
        Renewal_Status,
        COUNT(DISTINCT Customer_ID) AS total_customers
    FROM vw_customers_clean
    GROUP BY Renewal_Status
)

SELECT
    o.Renewal_Status,
    COALESCE(f.flagged_customers, 0) AS flagged_customers,
    o.total_customers,

    ROUND(
        100.0 * COALESCE(f.flagged_customers, 0)
        /
        NULLIF(
            (SELECT COUNT(*) FROM flagged_customers),
            0
        ),
        2
    ) AS flagged_percentage,

    ROUND(
        100.0 * o.total_customers
        /
        NULLIF(
            (SELECT COUNT(*) FROM vw_customers_clean),
            0
        ),
        2
    ) AS overall_percentage

FROM overall_status o

LEFT JOIN flagged_status f
    ON f.Renewal_Status = o.Renewal_Status

ORDER BY
    o.Renewal_Status;

-- Query Output:
-- Active: 1 flagged customer / 812 overall customers / 100.00% of flagged group / 54.13% of all customers
-- At Risk: 0 flagged customers / 212 overall customers / 0.00% of flagged group / 14.13% of all customers
-- Churned: 0 flagged customers / 280 overall customers / 0.00% of flagged group / 18.67% of all customers
-- Renewed: 0 flagged customers / 196 overall customers / 0.00% of flagged group / 13.07% of all customers

-- Business Answer:
-- One customer exceeded the threshold of more than 5 High/Critical tickets
-- within a rolling 6-month window, and the flagged customer is Active.
-- No At Risk or Churned customers appeared in the flagged group.
-- Therefore, the flagged group does not show concentration among
-- At Risk or Churned customers.

-- =====================================================
-- QUESTION 5: CROSS-FUNCTIONAL ANALYSIS
-- =====================================================
-- PART A: NPS Score vs Monthly Churn Rate
USE genp_task4;

WITH customer_financials AS (
    SELECT
        s.Customer_ID,
        AVG(c.NPS_Score) AS avg_nps,
        AVG(s.Monthly_Churn_Rate_Pct) AS avg_monthly_churn
    FROM vw_saas_financials_clean s
    JOIN vw_customers_clean c
        ON s.Customer_ID = c.Customer_ID
    WHERE c.NPS_Score IS NOT NULL
      AND s.Monthly_Churn_Rate_Pct IS NOT NULL
    GROUP BY s.Customer_ID
)

SELECT
    c.Customer_Tier,
    COUNT(*) AS customers,
    ROUND(AVG(cf.avg_nps), 2) AS avg_nps,
    ROUND(AVG(cf.avg_monthly_churn), 2) AS avg_monthly_churn_pct

FROM customer_financials cf

JOIN vw_customers_clean c
    ON cf.Customer_ID = c.Customer_ID

GROUP BY c.Customer_Tier

ORDER BY avg_monthly_churn_pct DESC;

-- Query Output:
-- Highest churn: Enterprise - 6.80%
-- Lowest churn: Mid-Market - 6.41%

-- Business Answer:
-- Enterprise customers have the highest average monthly churn and the
-- lowest average NPS, while Mid-Market customers have the lowest churn.
-- This provides some evidence of a possible relationship between lower
-- NPS and higher churn, but the tier-level comparison alone is not
-- sufficient to confirm a strong relationship.

-- PART B: NPS vs Churn by Customer Tier
-- Compare customer-level average NPS with customer-level
-- average monthly churn by Customer Tier.

USE genp_task4;

WITH customer_financials AS (
    SELECT
        Customer_ID,

        AVG(Monthly_Churn_Rate_Pct)
            AS avg_monthly_churn_rate_pct

    FROM vw_saas_financials_clean

    WHERE Monthly_Churn_Rate_Pct IS NOT NULL

    GROUP BY
        Customer_ID
)

SELECT
    c.Customer_Tier,

    COUNT(DISTINCT c.Customer_ID) AS customers,

    ROUND(
        AVG(c.NPS_Score),
        2
    ) AS average_nps_score,

    ROUND(
        AVG(cf.avg_monthly_churn_rate_pct),
        2
    ) AS average_monthly_churn_rate_pct

FROM vw_customers_clean c

JOIN customer_financials cf
    ON c.Customer_ID = cf.Customer_ID

WHERE c.NPS_Score IS NOT NULL

GROUP BY
    c.Customer_Tier

ORDER BY
    average_monthly_churn_rate_pct DESC;

-- Query Output:
-- Enterprise: Avg NPS 32.27, Avg Monthly Churn 6.80%
-- SMB: Avg NPS 41.28, Avg Monthly Churn 6.58%
-- Mid-Market: Avg NPS 37.59, Avg Monthly Churn 6.41%
--
-- Business Answer:
-- Enterprise has the lowest NPS and highest churn, while Mid-Market has the
-- lowest churn. This suggests a possible relationship between lower NPS and
-- higher churn, but the pattern is not strong enough to confirm a clear trend.

-- ---------------------------------------------------------------------
-- PART B2: Customer-Level Pearson Correlation
-- Measures the relationship between customer NPS and monthly churn.
-- Negative correlation indicates higher NPS is associated with lower churn.

USE genp_task4;

WITH customer_financials AS (
    SELECT
        s.Customer_ID,
        AVG(c.NPS_Score) AS avg_nps,
        AVG(s.Monthly_Churn_Rate_Pct) AS avg_monthly_churn
    FROM vw_saas_financials_clean s
    JOIN vw_customers_clean c
        ON s.Customer_ID = c.Customer_ID
    WHERE c.NPS_Score IS NOT NULL
      AND s.Monthly_Churn_Rate_Pct IS NOT NULL
    GROUP BY s.Customer_ID
),

stats AS (
    SELECT
        COUNT(*) AS n,
        SUM(avg_nps) AS sum_x,
        SUM(avg_monthly_churn) AS sum_y,
        SUM(avg_nps * avg_nps) AS sum_x2,
        SUM(avg_monthly_churn * avg_monthly_churn) AS sum_y2,
        SUM(avg_nps * avg_monthly_churn) AS sum_xy
    FROM customer_financials
)

SELECT
    ROUND(
        (
            n * sum_xy - sum_x * sum_y
        )
        /
        NULLIF(
            SQRT(
                (n * sum_x2 - sum_x * sum_x)
                *
                (n * sum_y2 - sum_y * sum_y)
            ),
            0
        ),
        3
    ) AS pearson_nps_churn_correlation
FROM stats;

-- Query Output:
-- Pearson correlation between customer NPS and monthly churn: 0.013

-- Business Answer:
-- The Pearson correlation is 0.013, indicating an almost zero positive
-- relationship between NPS and monthly churn. Therefore, the data does
-- not provide evidence of a meaningful linear relationship between
-- customer NPS and monthly churn.
-- =====================================================================
-- PART C: REGION-LEVEL BUSINESS HEALTH SCORECARD
--
-- Customers.Region is the authoritative regional dimension for
-- customer-linked Sales, Support, and Financial metrics.
--
-- IMPORTANT:
-- Sales_Pipeline contains Deal_Value_USD, not ARR_USD.
-- Therefore the sales metric is reported as:
-- Total Closed-Won Deal Value.
--
-- Marketing Target_Region is analyzed separately because it represents
-- campaign targeting and is different from Customers.Region.
-- =====================================================================

USE genp_task4;

WITH sales_region AS (
    SELECT
        c.Region,

        ROUND(
            SUM(
                CASE
                    WHEN sp.Sales_Stage = 'Closed Won'
                    THEN sp.Deal_Value_USD_Clean
                    ELSE 0
                END
            ),
            2
        ) AS total_closed_won_deal_value_usd

    FROM vw_sales_pipeline_clean sp

    JOIN vw_customers_clean c
        ON c.Customer_ID = sp.Customer_ID

    GROUP BY c.Region
),

support_region AS (
    SELECT
        c.Region,

        ROUND(
            100.0 *
            SUM(
                CASE
                    WHEN st.Resolution_Hours_Clean > st.SLA_Target_Hours
                    THEN 1
                    ELSE 0
                END
            )
            / NULLIF(COUNT(*), 0),
            2
        ) AS sla_breach_rate_pct

    FROM vw_support_tickets_clean st

    JOIN vw_customers_clean c
        ON st.Customer_ID = c.Customer_ID

    WHERE st.Status = 'Resolved'
      AND st.Resolution_Hours_Clean IS NOT NULL
      AND st.SLA_Target_Hours IS NOT NULL

    GROUP BY c.Region
),

financial_region AS (
    SELECT
        c.Region,

        ROUND(
            AVG(f.LTV_CAC_Ratio),
            2
        ) AS avg_ltv_cac_ratio

    FROM vw_saas_financials_clean f

    JOIN vw_customers_clean c
        ON f.Customer_ID = c.Customer_ID

    WHERE f.LTV_CAC_Ratio IS NOT NULL
      AND f.LTV_CAC_Ratio >= 0

    GROUP BY c.Region
),

marketing_region AS (
    SELECT
        Target_Region AS Region,

        ROUND(
            AVG(Activation_Rate_Pct),
            2
        ) AS avg_activation_rate_pct

    FROM vw_marketing_campaigns_clean

WHERE Leads_Generated IS NOT NULL
  AND Activations IS NOT NULL
  AND Activation_Rate_Pct IS NOT NULL
  AND Target_Region <> 'Global'

    GROUP BY Target_Region
)

SELECT
    sr.Region,
    sr.total_closed_won_deal_value_usd,
    mr.avg_activation_rate_pct,
    spr.sla_breach_rate_pct,
    fr.avg_ltv_cac_ratio

FROM sales_region sr

LEFT JOIN marketing_region mr
    ON mr.Region = sr.Region

LEFT JOIN support_region spr
    ON spr.Region = sr.Region

LEFT JOIN financial_region fr
    ON fr.Region = sr.Region

ORDER BY
    sr.total_closed_won_deal_value_usd DESC;

-- Query Output:
-- ANZ: Highest closed-won deal value - $6.43M
-- Middle East: Highest average activation - 18.87%
-- Middle East: Lowest SLA breach rate - 58.66%
-- Southeast Asia: Highest LTV/CAC - 701.48

-- Business Answer:
-- No single region necessarily leads across all four metrics.
-- Regional performance should therefore be evaluated using the
-- complete scorecard rather than one metric alone.


-- ---------------------------------------------------------------------
-- MARKETING ACTIVATION BY TARGET REGION
--
-- Marketing Target_Region is kept separate from Customers.Region.
-- ---------------------------------------------------------------------

SELECT
    Target_Region,

    COUNT(*) AS campaign_count,

  ROUND(
    AVG(Activation_Rate_Pct),
    2
) AS avg_activation_rate_pct

FROM vw_marketing_campaigns_clean

WHERE Leads_Generated IS NOT NULL
  AND Activations IS NOT NULL

GROUP BY
    Target_Region

ORDER BY
    avg_activation_rate_pct DESC;

-- Query Output:
-- Middle East: 18.87%
-- East Africa: 17.82%
-- Global: 17.23%
-- ANZ: 16.36%
-- Southeast Asia: 15.89%
-- South Asia: 14.97%

-- Business Answer:
-- Middle East has the highest average marketing activation rate at 18.87%,
-- while South Asia has the lowest at 14.97%. Marketing Target_Region
-- represents campaign targeting and is therefore kept separate from
-- Customers.Region.