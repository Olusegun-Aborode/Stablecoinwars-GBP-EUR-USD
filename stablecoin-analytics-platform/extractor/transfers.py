"""
Transfers Extraction and Categorization

Creates the categorized_transfers table, extracts recent transfers
from supported EVM chains for the last ~1 hour, and categorizes each
transfer using tagged_addresses.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from dotenv import load_dotenv
import psycopg
from web3 import Web3

# Ensure project root is on sys.path when running as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.tokens import STABLECOINS
from extractor.evm import get_web3_connection, ERC20_ABI
from extractor.solana_transfers import extract_solana_transfers


BLOCKS_PER_HOUR = {
    'ethereum': 300,
}

# Default lookback window in hours
DEFAULT_LOOKBACK_HOURS = 6

# Exclude specific tokens per chain from transfer extraction
EXCLUDED_TOKENS = {
    'ethereum': {'USDC', 'USDT'},
    'solana': {'USDC', 'USDT'},
}


def ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS categorized_transfers (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                chain VARCHAR(20) NOT NULL,
                token_symbol VARCHAR(16) NOT NULL,
                token_address VARCHAR(128) NOT NULL,
                tx_hash VARCHAR(128) NOT NULL,
                from_address VARCHAR(128) NOT NULL,
                to_address VARCHAR(128) NOT NULL,
                amount DECIMAL(38,18) NOT NULL,
                category_sender VARCHAR(32),
                label_sender VARCHAR(64),
                category_receiver VARCHAR(32),
                label_receiver VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tx_hash, token_address, from_address, to_address, amount)
            );
            """
        )
        conn.commit()


def load_tag_map(conn, chain: str) -> Dict[str, Dict[str, str]]:
    """Return mapping of lowercase address -> {category,label} for a chain."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT LOWER(address), category, COALESCE(label, category)
            FROM tagged_addresses
            WHERE chain = %s
            """,
            (chain,)
        )
        rows = cur.fetchall()
    return {addr: {'category': cat, 'label': lbl} for addr, cat, lbl in rows}


def extract_chain_transfers(conn, chain: str, tokens: Dict[str, str], lookback_hours: int = DEFAULT_LOOKBACK_HOURS) -> int:
    """Extract transfers for a specific chain and insert categorized rows."""
    w3 = get_web3_connection(chain)
    if not w3:
        print(f"Warning: Could not connect to {chain} RPC; skipping")
        return 0

    tag_map = load_tag_map(conn, chain)
    total_inserted = 0

    excluded = EXCLUDED_TOKENS.get(chain, set())
    for symbol, token_addr in tokens.items():
        # Skip excluded tokens for this chain
        if symbol in excluded:
            continue
        try:
            checksum_addr = Web3.to_checksum_address(token_addr)
        except Exception:
            # Skip placeholder or invalid addresses
            continue

        contract = w3.eth.contract(address=checksum_addr, abi=ERC20_ABI)
        try:
            decimals = contract.functions.decimals().call()
        except Exception:
            decimals = 18

        current_block = w3.eth.block_number
        hours = max(1, int(lookback_hours or 1))
        from_block = max(0, current_block - BLOCKS_PER_HOUR.get(chain, 300) * hours)

        transfer_topic = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'

        # Chunk fetching to be provider-friendly
        default_blocks = BLOCKS_PER_HOUR.get(chain, 300) * hours
        chunk_size = max(100, min(1000, default_blocks))
        start_block = from_block
        logs: List[dict] = []
        while start_block <= current_block:
            end_block = min(start_block + chunk_size - 1, current_block)
            try:
                logs_chunk = w3.eth.get_logs({
                    'address': checksum_addr,
                    'topics': [transfer_topic],
                    'fromBlock': start_block,
                    'toBlock': end_block
                })
                if logs_chunk:
                    logs.extend(logs_chunk)
            except Exception:
                pass
            finally:
                start_block = end_block + 1

        if not logs:
            continue

        with conn.cursor() as cur:
            for log in logs:
                try:
                    evt = contract.events.Transfer().process_log(log)
                    from_addr = evt['args']['from']
                    to_addr = evt['args']['to']
                    value = evt['args']['value']
                    amount = value / (10 ** decimals)

                    # Block timestamp
                    try:
                        blk = w3.eth.get_block(log['blockNumber'])
                        ts = datetime.fromtimestamp(blk['timestamp'], tz=timezone.utc)
                    except Exception:
                        ts = datetime.utcnow()

                    sender_info = tag_map.get(from_addr.lower())
                    receiver_info = tag_map.get(to_addr.lower())

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
                            ts, chain, symbol, checksum_addr, log['transactionHash'].hex(),
                            from_addr, to_addr, amount,
                            sender_info['category'] if sender_info else None,
                            sender_info['label'] if sender_info else None,
                            receiver_info['category'] if receiver_info else None,
                            receiver_info['label'] if receiver_info else None,
                        )
                    )
                    total_inserted += 1
                except Exception:
                    # Skip malformed log
                    continue
            conn.commit()

    return total_inserted


def insert_solana_transfers(conn, lookback_hours: int = DEFAULT_LOOKBACK_HOURS) -> int:
    """Extract Solana transfers for supported tokens and insert categorized rows."""
    tag_map = load_tag_map(conn, 'solana')
    total_inserted = 0

    solana_tokens = STABLECOINS.get('solana', {})
    if not solana_tokens:
        return 0

    excluded = EXCLUDED_TOKENS.get('solana', set())
    with conn.cursor() as cur:
        for symbol, token_addr in solana_tokens.items():
            # Skip excluded tokens on Solana
            if symbol in excluded:
                continue
            transfers = extract_solana_transfers(symbol, token_addr, lookback_hours)
            for t in transfers:
                sender = (t.get('sender') or '').lower()
                receiver = (t.get('receiver') or '').lower()
                # Require both addresses to avoid NOT NULL violations
                if not sender or not receiver:
                    continue

                sender_info = tag_map.get(sender)
                receiver_info = tag_map.get(receiver)

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
                            t.get('timestamp'), 'solana', symbol, token_addr, t.get('transaction_hash'),
                            t.get('sender'), t.get('receiver'), t.get('value') or 0,
                            sender_info['category'] if sender_info else None,
                            sender_info['label'] if sender_info else None,
                            receiver_info['category'] if receiver_info else None,
                            receiver_info['label'] if receiver_info else None,
                        )
                    )
                    total_inserted += 1
                except Exception:
                    continue
            # Commit per-token to avoid large transactions causing connection loss
            try:
                conn.commit()
            except Exception:
                # If commit fails, skip committing this token to avoid blocking the rest
                # Subsequent tokens will still be attempted
                pass

    return total_inserted


def extract_all_transfers(conn, lookback_hours: int = DEFAULT_LOOKBACK_HOURS) -> Dict[str, int]:
    """Extract and insert transfers for all supported chains, including Solana.

    Returns a dict of inserted counts per chain.
    """
    counts: Dict[str, int] = {}

    # EVM chains (restricted to ETH only)
    for chain in ['ethereum']:
        tokens = STABLECOINS.get(chain, {})
        if not tokens:
            counts[chain] = 0
            continue
        counts[chain] = extract_chain_transfers(conn, chain, tokens, lookback_hours)

    # Solana
    counts['solana'] = insert_solana_transfers(conn, lookback_hours)

    return counts


def main():
    load_dotenv()
    # Override RPC endpoints if provided via environment
    rpc_endpoints = {
        "ethereum": os.getenv("ALCHEMY_ETH_URL"),
    }
    try:
        import extractor.evm as evm_mod
        for k, v in rpc_endpoints.items():
            if v:
                evm_mod.RPC_ENDPOINTS[k] = v
    except Exception:
        pass
    url = os.getenv("NEON_DB_URL")
    if not url:
        print("ERROR: NEON_DB_URL is not set")
        return 1

    try:
        with psycopg.connect(url) as conn:
            ensure_table(conn)

            counts = extract_all_transfers(conn, lookback_hours=DEFAULT_LOOKBACK_HOURS)
            for chain, inserted in counts.items():
                print(f"Chain {chain}: inserted {inserted} transfers")
            total = sum(counts.values())
            print(f"✓ Total transfers inserted: {total}")
            return 0
    except Exception as e:
        print("ERROR during transfer extraction:", e)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())