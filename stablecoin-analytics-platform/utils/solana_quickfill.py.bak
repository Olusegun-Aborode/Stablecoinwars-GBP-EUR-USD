"""
Quick Solana backfill to validate amount parsing and tagging.

Runs a short lookback (default 4 hours) for Solana tokens in STABLECOINS,
inserts into categorized_transfers with sender/receiver tags.

Usage:
    python utils/solana_quickfill.py --hours 4
"""

import os
import argparse
import sys
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
import psycopg

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.tokens import STABLECOINS
from extractor.solana_transfers import extract_solana_transfers
from extractor.transfers import ensure_table, load_tag_map


def main():
    parser = argparse.ArgumentParser(description="Quick Solana backfill")
    parser.add_argument("--hours", type=int, default=4, help="Lookback hours for Solana")
    args = parser.parse_args()

    load_dotenv()
    url = os.getenv("NEON_DB_URL")
    if not url:
        raise RuntimeError("NEON_DB_URL is not set")

    sol_tokens = STABLECOINS.get('solana', {})
    if not sol_tokens:
        print("No Solana tokens configured in STABLECOINS")
        return 0

    with psycopg.connect(url) as conn:
        ensure_table(conn)
        tag_map = load_tag_map(conn, 'solana')
        total = 0
        print(f"Running Solana quickfill for {args.hours} hours at {datetime.utcnow().isoformat()}Z")
        for token_symbol, token_address in sol_tokens.items():
            print(f"  Token: {token_symbol}")
            transfers = extract_solana_transfers(token_symbol, token_address, args.hours)
            if not transfers:
                print("    - No transfers found")
                continue
            inserted = 0
            with conn.cursor() as cur:
                for t in transfers:
                    s_addr = t.get('sender')
                    r_addr = t.get('receiver')
                    s_info = tag_map.get((s_addr or '').lower()) if isinstance(s_addr, str) else None
                    r_info = tag_map.get((r_addr or '').lower()) if isinstance(r_addr, str) else None
                    try:
                        cur.execute(
                            """
                            INSERT INTO categorized_transfers (
                                timestamp, chain, token_symbol, token_address, tx_hash,
                                from_address, to_address, amount,
                                category_sender, label_sender, category_receiver, label_receiver
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (tx_hash, token_address, from_address, to_address, amount)
                            DO NOTHING;
                            """,
                            (
                                t.get('timestamp'), t.get('chain', 'solana'), t.get('token_symbol', token_symbol),
                                t.get('token_address', token_address), t.get('transaction_hash'),
                                t.get('sender'), t.get('receiver'), float(t.get('value', 0) or 0),
                                (s_info['category'] if s_info else None),
                                (s_info['label'] if s_info else None),
                                (r_info['category'] if r_info else None),
                                (r_info['label'] if r_info else None),
                            )
                        )
                        inserted += 1
                    except Exception:
                        continue
                conn.commit()
            print(f"    ✓ Inserted {inserted} transfers")
            total += inserted
        print(f"✓ Solana quickfill inserted: {total}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())