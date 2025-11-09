-- Query: Chain Distribution by Token
-- Description: Shows how each stablecoin's supply is distributed across chains
-- Parameters: token_symbol (text dropdown), snapshot_date (date)

WITH latest_snapshot AS (
    SELECT
        coin,
        chain,
        supply,
        ROW_NUMBER() OVER (PARTITION BY coin, chain ORDER BY timestamp DESC) as rn
    FROM stablecoin_metrics
    WHERE DATE(timestamp) = {{snapshot_date}}
      AND coin = {{token_symbol}}
)

SELECT
    chain,
    supply,
    supply / SUM(supply) OVER () * 100 as percentage
FROM latest_snapshot
WHERE rn = 1
  AND supply > 0
ORDER BY supply DESC;
