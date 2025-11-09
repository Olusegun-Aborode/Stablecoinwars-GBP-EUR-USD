"""
Enrich categorized_transfers with tags from tagged_addresses.

Updates sender and receiver category/label fields by matching addresses per chain.

Usage:
    python utils/enrich_tags.py
"""

import os
from dotenv import load_dotenv
import psycopg


def main():
    load_dotenv()
    url = os.getenv("NEON_DB_URL") or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("NEON_DB_URL or DATABASE_URL must be set")

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            # Update sender tags
            cur.execute(
                """
                UPDATE categorized_transfers ct
                SET category_sender = ta.category,
                    label_sender = ta.label
                FROM tagged_addresses ta
                WHERE LOWER(ct.from_address) = LOWER(ta.address)
                  AND ct.chain = ta.chain
                  AND (ct.category_sender IS NULL OR ct.label_sender IS NULL);
                """
            )
            sender_updates = cur.rowcount

            # Update receiver tags
            cur.execute(
                """
                UPDATE categorized_transfers ct
                SET category_receiver = ta.category,
                    label_receiver = ta.label
                FROM tagged_addresses ta
                WHERE LOWER(ct.to_address) = LOWER(ta.address)
                  AND ct.chain = ta.chain
                  AND (ct.category_receiver IS NULL OR ct.label_receiver IS NULL);
                """
            )
            receiver_updates = cur.rowcount

            conn.commit()

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    SUM(CASE WHEN category_sender IS NOT NULL OR label_sender IS NOT NULL THEN 1 ELSE 0 END) AS tagged_sender_rows,
                    SUM(CASE WHEN category_receiver IS NOT NULL OR label_receiver IS NOT NULL THEN 1 ELSE 0 END) AS tagged_receiver_rows,
                    COUNT(*) AS total_rows
                FROM categorized_transfers;
                """
            )
            tagged_sender_rows, tagged_receiver_rows, total_rows = cur.fetchone()

    print("=== Tag Enrichment Summary ===")
    print(f"Sender updates: {sender_updates}")
    print(f"Receiver updates: {receiver_updates}")
    print(f"Tagged sender rows: {tagged_sender_rows}")
    print(f"Tagged receiver rows: {tagged_receiver_rows}")
    print(f"Total rows: {total_rows}")


if __name__ == "__main__":
    main()