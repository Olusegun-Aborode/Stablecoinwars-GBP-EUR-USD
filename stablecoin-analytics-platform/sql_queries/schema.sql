CREATE TABLE IF NOT EXISTS stablecoin_metrics (
    id SERIAL PRIMARY KEY,
    coin VARCHAR(10) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    chain VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    supply DECIMAL(38,18),
    transfers_count INTEGER,
    transfers_volume DECIMAL(38,18),
    tvl DECIMAL(38,18),
    peg_deviation DECIMAL(8,6),
    usd_equivalent_volume DECIMAL(38,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_currency_coin_time
    ON stablecoin_metrics(currency, coin, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_chain_time
    ON stablecoin_metrics(chain, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_timestamp
    ON stablecoin_metrics(timestamp DESC);

CREATE MATERIALIZED VIEW IF NOT EXISTS daily_metrics AS
SELECT
    coin,
    currency,
    chain,
    DATE(timestamp) as day,
    AVG(supply) as avg_supply,
    MAX(supply) as max_supply,
    MIN(supply) as min_supply,
    SUM(transfers_count) as total_transfers,
    SUM(transfers_volume) as total_volume,
    AVG(tvl) as avg_tvl,
    AVG(peg_deviation) as avg_peg_deviation
FROM stablecoin_metrics
GROUP BY coin, currency, chain, DATE(timestamp);

CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_metrics_unique
    ON daily_metrics(coin, chain, day);