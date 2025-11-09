"""
Diagnostics: Tagging Validation & Counterparty Profiling + Backfill Checks

Runs a set of SQL queries against `categorized_transfers` to validate tagging,
counterparty activity, Solana volume, duplicates, and latency.

Usage:
    python utils/diagnostics.py

Requires `NEON_DB_URL` in environment or within a .env at project root.
"""

import os
from dotenv import load_dotenv
import psycopg


def get_conn():
    load_dotenv()
    url = os.getenv("NEON_DB_URL")
    if not url:
        raise RuntimeError("NEON_DB_URL is not set in environment or .env")
    return psycopg.connect(url)


def run_query(conn, title: str, sql: str):
    print(f"\n=== {title} ===")
    with conn.cursor() as cur:
        cur.execute(sql)
        try:
            rows = cur.fetchall()
            if not rows:
                print("(no rows)")
                return
            # Print columns
            cols = [d[0] for d in cur.description]
            print(" | ".join(cols))
            for r in rows:
                print(" | ".join(str(x) if x is not None else "NULL" for x in r))
        except psycopg.ProgrammingError:
            # For queries returning a single scalar
            row = cur.fetchone()
            print(row)


def main():
    with get_conn() as conn:
        # 1. Tagging happening at all: count by sender_tag/receiver_tag
        run_query(conn, "1) Transfers by sender_tag and receiver_tag (24h)",
                  """
                  SELECT 
                      COALESCE(label_sender, category_sender) AS sender_tag,
                      COALESCE(label_receiver, category_receiver) AS receiver_tag,
                      COUNT(*) AS count
                  FROM categorized_transfers
                  WHERE timestamp > NOW() - INTERVAL '1 day'
                  GROUP BY 1,2
                  ORDER BY count DESC
                  LIMIT 20;
                  """)

        # 2. Percentage of rows untagged (both sides NULL, 24h)
        run_query(conn, "2) Percentage untagged rows (both sides NULL, 24h)",
                  """
                  SELECT ROUND(100.0 * 
                      SUM(CASE WHEN 
                          COALESCE(label_sender, category_sender) IS NULL AND 
                          COALESCE(label_receiver, category_receiver) IS NULL 
                      THEN 1 ELSE 0 END) 
                      / NULLIF(COUNT(*), 0), 2) AS pct_both_sides_untagged
                  FROM categorized_transfers
                  WHERE timestamp > NOW() - INTERVAL '1 day';
                  """)

        # 2b. Coverage where at least one side is tagged (24h)
        run_query(conn, "2b) Tagged coverage: at least one side tagged (24h)",
                  """
                  SELECT 
                      SUM(CASE WHEN 
                          COALESCE(label_sender, category_sender) IS NOT NULL OR 
                          COALESCE(label_receiver, category_receiver) IS NOT NULL 
                      THEN 1 ELSE 0 END) AS rows_with_any_tag,
                      ROUND(100.0 * 
                          SUM(CASE WHEN 
                              COALESCE(label_sender, category_sender) IS NOT NULL OR 
                              COALESCE(label_receiver, category_receiver) IS NOT NULL 
                          THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 2) AS pct_with_any_tag
                  FROM categorized_transfers
                  WHERE timestamp > NOW() - INTERVAL '1 day';
                  """)

        # 3. Top counterparties by activity (7 days)
        run_query(conn, "3) Top 25 counterparties by volume and count (7d)",
                  """
                  WITH tags AS (
                      SELECT COALESCE(label_sender, category_sender) AS tag, amount
                      FROM categorized_transfers
                      WHERE timestamp > NOW() - INTERVAL '7 days'
                        AND COALESCE(label_sender, category_sender) IS NOT NULL
                      UNION ALL
                      SELECT COALESCE(label_receiver, category_receiver) AS tag, amount
                      FROM categorized_transfers
                      WHERE timestamp > NOW() - INTERVAL '7 days'
                        AND COALESCE(label_receiver, category_receiver) IS NOT NULL
                  )
                  SELECT 
                      tag AS counterparty_tag,
                      COUNT(*) AS transfer_count,
                      SUM(amount) AS total_volume
                  FROM tags
                  GROUP BY tag
                  ORDER BY total_volume DESC
                  LIMIT 25;
                  """)

        # 4. Exchange vs user flow share (7 days)
        run_query(conn, "4) Exchange vs user flow volume (7d)",
                  """
                  SELECT
                      SUM(CASE WHEN category_sender = 'CEX' OR category_receiver = 'CEX' THEN amount ELSE 0 END) AS exchange_volume,
                      SUM(CASE WHEN 
                          COALESCE(label_sender, category_sender) IS NULL AND 
                          COALESCE(label_receiver, category_receiver) IS NULL
                      THEN amount ELSE 0 END) AS user_volume
                  FROM categorized_transfers
                  WHERE timestamp > NOW() - INTERVAL '7 days';
                  """)

        # 5. Bridge or contract flows (7 days)
        run_query(conn, "5) Top 10 bridge/contract tags by transfers and volume (7d)",
                  """
                  WITH bridge_tags AS (
                      SELECT COALESCE(label_sender, category_sender) AS tag, amount
                      FROM categorized_transfers
                      WHERE timestamp > NOW() - INTERVAL '7 days'
                        AND category_sender IN ('BRIDGE', 'CONTRACT')
                      UNION ALL
                      SELECT COALESCE(label_receiver, category_receiver) AS tag, amount
                      FROM categorized_transfers
                      WHERE timestamp > NOW() - INTERVAL '7 days'
                        AND category_receiver IN ('BRIDGE', 'CONTRACT')
                  )
                  SELECT tag, COUNT(*) AS transfers, SUM(amount) AS total_volume
                  FROM bridge_tags
                  WHERE tag IS NOT NULL
                  GROUP BY tag
                  ORDER BY transfers DESC, total_volume DESC
                  LIMIT 10;
                  """)

        # 6. Solana per-hour insert counts (24h)
        run_query(conn, "6) Solana transfers per hour (24h)",
                  """
                  SELECT date_trunc('hour', timestamp) AS hour, COUNT(*) AS count
                  FROM categorized_transfers
                  WHERE chain = 'solana' AND timestamp > NOW() - INTERVAL '1 day'
                  GROUP BY hour
                  ORDER BY hour DESC;
                  """)

        # 7. Transfers per chain (24h)
        run_query(conn, "7) Transfers per chain (24h)",
                  """
                  SELECT chain, COUNT(*) AS count
                  FROM categorized_transfers
                  WHERE timestamp > NOW() - INTERVAL '1 day'
                  GROUP BY chain
                  ORDER BY count DESC;
                  """)

        # 8. Duplicate inserts on Solana (24h)
        run_query(conn, "8) Solana duplicate insert count (24h)",
                  """
                  SELECT COUNT(*) - COUNT(DISTINCT tx_hash) AS duplicate_count
                  FROM categorized_transfers
                  WHERE chain = 'solana' AND timestamp > NOW() - INTERVAL '1 day';
                  """)

        # 9. Volume sanity for USDC & VGBP on Solana (24h)
        run_query(conn, "9) Solana USDC/VGBP volume and count (24h)",
                  """
                  SELECT token_symbol AS token, SUM(amount) AS total_volume, COUNT(*) AS transfers
                  FROM categorized_transfers
                  WHERE chain = 'solana' AND timestamp > NOW() - INTERVAL '1 day'
                    AND token_symbol IN ('USDC', 'VGBP')
                  GROUP BY token_symbol;
                  """)

        # 10. Processing latency estimate (created_at - timestamp) (24h)
        run_query(conn, "10) Avg processing latency (created_at - timestamp) (24h)",
                  """
                  SELECT AVG(created_at - timestamp) AS avg_latency
                  FROM categorized_transfers
                  WHERE timestamp > NOW() - INTERVAL '1 day';
                  """)


if __name__ == "__main__":
    main()