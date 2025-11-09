-- Query: Daily Supply by Currency
-- Description: Shows the total supply of stablecoins grouped by currency (GBP, EUR, USD)
-- Parameters: date_range (date range picker)

WITH daily_totals AS (
    SELECT
        currency,
        DATE(timestamp) as day,
        SUM(supply) as total_supply
    FROM stablecoin_metrics
    WHERE timestamp >= {{date_range_start}}
      AND timestamp <= {{date_range_end}}
    GROUP BY currency, DATE(timestamp)
)

SELECT
    day,
    currency,
    total_supply,
    total_supply - LAG(total_supply) OVER (PARTITION BY currency ORDER BY day) as daily_change,
    (total_supply - LAG(total_supply) OVER (PARTITION BY currency ORDER BY day)) 
        / NULLIF(LAG(total_supply) OVER (PARTITION BY currency ORDER BY day), 0) * 100 as pct_change
FROM daily_totals
ORDER BY day DESC, currency;
