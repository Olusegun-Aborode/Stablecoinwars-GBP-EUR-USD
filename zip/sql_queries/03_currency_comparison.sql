-- Query: Multi-Currency Comparison
-- Description: Compare key metrics across GBP, EUR, and USD stablecoins
-- Parameters: comparison_date (date)

WITH latest_metrics AS (
    SELECT
        currency,
        coin,
        chain,
        supply,
        transfers_count,
        transfers_volume,
        tvl,
        peg_deviation,
        ROW_NUMBER() OVER (PARTITION BY currency, coin, chain ORDER BY timestamp DESC) as rn
    FROM stablecoin_metrics
    WHERE DATE(timestamp) = {{comparison_date}}
)

SELECT
    currency,
    COUNT(DISTINCT coin) as num_tokens,
    COUNT(DISTINCT chain) as num_chains,
    SUM(supply) as total_supply,
    SUM(transfers_count) as total_transfers,
    SUM(transfers_volume) as total_volume,
    SUM(tvl) as total_tvl,
    AVG(peg_deviation) as avg_peg_deviation,
    SUM(transfers_volume) / NULLIF(SUM(tvl), 0) as utilization_ratio
FROM latest_metrics
WHERE rn = 1
GROUP BY currency
ORDER BY total_supply DESC;
