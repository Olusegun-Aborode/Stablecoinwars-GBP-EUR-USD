"""
Show tagged addresses in the database.

Outputs:
- Preview (top 50) with label, category, address preview, and full address
- Full list of all tagged addresses

Usage:
    python utils/show_tags.py
"""

import os
from dotenv import load_dotenv
import psycopg


def get_conn():
    load_dotenv()
    url = os.getenv("NEON_DB_URL")
    if not url:
        raise RuntimeError("NEON_DB_URL is not set")
    return psycopg.connect(url)


def print_rows(title: str, cur):
    print(f"\n=== {title} ===")
    cols = [d[0] for d in cur.description]
    print(" | ".join(cols))
    for row in cur.fetchall():
        print(" | ".join(str(x) if x is not None else "NULL" for x in row))


def main():
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Preview: top 50
            cur.execute(
                """
                SELECT 
                    label, 
                    category, 
                    LEFT(address, 10) || '...' || RIGHT(address, 8) AS address_preview, 
                    address,
                    chain,
                    COALESCE(source, 'unknown') AS source
                FROM tagged_addresses 
                ORDER BY category, label 
                LIMIT 50;
                """
            )
            print_rows("Tagged addresses (preview, top 50)", cur)

            # Full list
            cur.execute(
                """
                SELECT 
                    label, 
                    category, 
                    LEFT(address, 10) || '...' || RIGHT(address, 8) AS address_preview, 
                    address,
                    chain,
                    COALESCE(source, 'unknown') AS source
                FROM tagged_addresses 
                ORDER BY category, label;
                """
            )
            print_rows("Tagged addresses (full)", cur)


if __name__ == "__main__":
    main()