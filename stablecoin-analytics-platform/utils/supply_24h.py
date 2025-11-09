"""
24-hour Supply Metrics Preview

Shows per-coin, per-chain data points, earliest and latest timestamps
from the last 24 hours in `stablecoin_metrics`.

Usage:
    python utils/supply_24h.py
"""

import os
from dotenv import load_dotenv
import psycopg


def main():
    load_dotenv()
    url = os.getenv("NEON_DB_URL")
    if not url:
        raise RuntimeError("NEON_DB_URL is not set")

    sql = """
    SELECT 
        coin, 
        chain, 
        COUNT(*) AS data_points, 
        MIN(timestamp) AS earliest, 
        MAX(timestamp) AS latest 
    FROM stablecoin_metrics 
    WHERE timestamp >= NOW() - INTERVAL '24 hours' 
    GROUP BY coin, chain 
    ORDER BY coin, chain;
    """

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            if not rows:
                print("(no supply metrics found in last 24 hours)")
                return 0
            print("coin | chain | data_points | earliest | latest")
            for r in rows:
                print(" | ".join(str(x) for x in r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())