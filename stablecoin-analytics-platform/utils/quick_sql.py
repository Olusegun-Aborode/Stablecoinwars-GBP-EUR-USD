"""
Quick SQL runner for two checks:
1) Per-chain transfer counts and distinct tokens
2) GBP token breakdown by chain

Usage:
    python utils/quick_sql.py
"""

import os
from dotenv import load_dotenv
import psycopg


def main():
    load_dotenv()
    url = os.getenv("NEON_DB_URL")
    if not url:
        raise RuntimeError("NEON_DB_URL is not set")

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            # Query 1: chain counts
            print("\n=== Per-chain counts ===")
            cur.execute(
                """
                SELECT 
                    chain, 
                    COUNT(*) AS transfers, 
                    COUNT(DISTINCT token_symbol) AS tokens 
                FROM categorized_transfers 
                GROUP BY chain 
                ORDER BY transfers DESC;
                """
            )
            rows = cur.fetchall()
            print("chain | transfers | tokens")
            for r in rows:
                print(f"{r[0]} | {r[1]} | {r[2]}")

            # Query 2: GBP breakdown
            print("\n=== GBP breakdown by token ===")
            cur.execute(
                """
                SELECT 
                    token_symbol, 
                    chain, 
                    COUNT(*) AS transfers 
                FROM categorized_transfers 
                WHERE token_symbol IN ('GBPT', 'tGBP', 'BGBP', 'VGBP') 
                GROUP BY token_symbol, chain 
                ORDER BY transfers DESC;
                """
            )
            rows = cur.fetchall()
            print("token_symbol | chain | transfers")
            for r in rows:
                print(f"{r[0]} | {r[1]} | {r[2]}")


if __name__ == "__main__":
    main()