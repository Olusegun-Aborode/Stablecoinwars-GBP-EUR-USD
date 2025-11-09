"""
GBP Activity with Major Addresses

Runs a query on categorized_transfers to show whether GBP tokens
(GBPT, tGBP, BGBP, VGBP) touch any tagged major exchanges/protocols.

Outputs token_symbol, sender_label, receiver_label, transfer_count, total_amount.

Usage:
    python utils/gbp_activity.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg


def main():
    load_dotenv()
    url = os.getenv("NEON_DB_URL")
    if not url:
        raise RuntimeError("NEON_DB_URL is not set")

    sql = """
    SELECT 
        token_symbol,
        COALESCE(label_sender, category_sender) AS sender_label,
        COALESCE(label_receiver, category_receiver) AS receiver_label,
        COUNT(*) AS transfer_count,
        SUM(amount) AS total_amount
    FROM categorized_transfers
    WHERE token_symbol IN ('GBPT', 'tGBP', 'BGBP', 'VGBP')
      AND (
        COALESCE(label_sender, category_sender) IS NOT NULL OR
        COALESCE(label_receiver, category_receiver) IS NOT NULL
      )
    GROUP BY token_symbol, sender_label, receiver_label
    ORDER BY transfer_count DESC;
    """

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            if not rows:
                print("(no tagged GBP activity found)")
                return 0
            print("token_symbol | sender_label | receiver_label | transfer_count | total_amount")
            for r in rows:
                print(" | ".join(str(x) if x is not None else "NULL" for x in r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())