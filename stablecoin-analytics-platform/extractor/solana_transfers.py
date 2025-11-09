import os
import requests
import base58
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple


def _rpc_url() -> str:
    # Prefer Helius if provided, fallback to public Solana RPC
    return os.getenv('ALCHEMY_SOL_URL', 'https://api.mainnet-beta.solana.com')


def _get_mint_decimals(mint: str) -> int:
    """Fetch mint decimals using getTokenSupply; default to 6 on failure."""
    rpc_url = _rpc_url()
    try:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getTokenSupply", "params": [mint]}
        resp = requests.post(rpc_url, json=payload, timeout=15)
        val = (resp.json() or {}).get('result', {}).get('value', {})
        dec = val.get('decimals')
        if isinstance(dec, int):
            return dec
    except Exception:
        pass
    return 6


def _get_account_owner(token_account: str) -> Optional[str]:
    """Return the wallet owner of a SPL token account via getAccountInfo."""
    rpc_url = _rpc_url()
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAccountInfo",
            "params": [
                token_account,
                {"encoding": "jsonParsed"}
            ],
        }
        resp = requests.post(rpc_url, json=payload, timeout=20)
        val = (resp.json() or {}).get('result', {}).get('value')
        if not val:
            return None
        data = val.get('data') or {}
        parsed = data.get('parsed') or {}
        info = parsed.get('info') or {}
        owner = info.get('owner')
        if isinstance(owner, str):
            return owner
    except Exception:
        pass
    return None


def _get_account_mint_and_decimals(token_account: str) -> Tuple[Optional[str], Optional[int]]:
    """Return (mint, decimals) for a SPL token account via getAccountInfo."""
    rpc_url = _rpc_url()
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAccountInfo",
            "params": [
                token_account,
                {"encoding": "jsonParsed"}
            ],
        }
        resp = requests.post(rpc_url, json=payload, timeout=20)
        val = (resp.json() or {}).get('result', {}).get('value')
        if not val:
            return (None, None)
        data = val.get('data') or {}
        parsed = data.get('parsed') or {}
        info = parsed.get('info') or {}
        mint = info.get('mint')
        token_amount = info.get('tokenAmount') or {}
        decimals = token_amount.get('decimals')
        if isinstance(decimals, int):
            return (mint, decimals)
        return (mint, None)
    except Exception:
        return (None, None)


def _fetch_signatures_paginated(address: str, start_ts: int, end_ts: int, max_pages: int = 20) -> List[Dict]:
    """Fetch signatures for an address, paging backwards until outside time window.

    Uses `before` to paginate and stops when results are empty or oldest entry
    falls before `start_ts`. Caps pages to avoid runaway loops.
    """
    rpc_url = _rpc_url()
    all_results: List[Dict] = []
    before = None
    pages = 0

    while pages < max_pages:
        params = [address, {"limit": 1000}]
        if before:
            params[1]["before"] = before
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getSignaturesForAddress", "params": params}
        resp = requests.post(rpc_url, json=payload, timeout=30)
        page = resp.json().get('result', []) or []
        if not page:
            break

        # Filter to time window; stop if oldest is outside window
        page_in_window = [s for s in page if s.get('blockTime') and start_ts <= s['blockTime'] <= end_ts]
        all_results.extend(page_in_window)

        oldest = page[-1]
        bt = oldest.get('blockTime')
        sig = oldest.get('signature')
        if not sig or not bt:
            break
        if bt < start_ts:
            break

        before = sig
        pages += 1

    return all_results


def _get_parsed_transactions(signatures: List[str]) -> List[Dict]:
    """Fetch parsed transactions for given signatures using batch JSON-RPC.

    Falls back to per‑signature requests if batch is not supported.
    """
    rpc_url = _rpc_url()
    if not signatures:
        return []

    parsed: List[Dict] = []
    chunk = 50
    for i in range(0, len(signatures), chunk):
        batch = [
            {
                "jsonrpc": "2.0",
                "id": idx,
                "method": "getTransaction",
                "params": [sig, {"encoding": "jsonParsed"}]
            }
            for idx, sig in enumerate(signatures[i:i+chunk], start=1)
        ]
        try:
            r = requests.post(rpc_url, json=batch, timeout=60)
            data = r.json()
            # If batch response is a dict (non‑batch), fall back to single
            if isinstance(data, dict):
                # Fallback to single requests for this chunk
                for sig in signatures[i:i+chunk]:
                    sr = requests.post(rpc_url, json={
                        "jsonrpc": "2.0", "id": 1, "method": "getTransaction",
                        "params": [sig, {"encoding": "jsonParsed"}]
                    }, timeout=30)
                    res = sr.json().get('result')
                    if res:
                        parsed.append(res)
            else:
                for item in data:
                    res = item.get('result') if isinstance(item, dict) else None
                    if res:
                        parsed.append(res)
        except Exception:
            # On error, try single requests for each signature in chunk
            for sig in signatures[i:i+chunk]:
                try:
                    sr = requests.post(rpc_url, json={
                        "jsonrpc": "2.0", "id": 1, "method": "getTransaction",
                        "params": [sig, {"encoding": "jsonParsed"}]
                    }, timeout=30)
                    res = sr.json().get('result')
                    if res:
                        parsed.append(res)
                except Exception:
                    continue
    return parsed


def _get_block_transactions(slots: List[int]) -> List[Dict]:
    """Fetch transactions for given slots via getBlock as a fallback when getTransaction is unreliable."""
    rpc_url = _rpc_url()
    if not slots:
        return []
    results: List[Dict] = []
    for slot in sorted(set(slots))[:200]:  # cap to avoid overload
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBlock",
                "params": [
                    slot,
                    {
                        "transactionDetails": "full",
                        "rewards": False,
                        "maxSupportedTransactionVersion": 0
                    }
                ]
            }
            r = requests.post(rpc_url, json=payload, timeout=60)
            block = (r.json() or {}).get('result') or {}
            txs = block.get('transactions') or []
            bt = block.get('blockTime')
            for t in txs:
                # Normalize to shape similar to getTransaction
                item = {
                    'transaction': t.get('transaction') or {},
                    'meta': t.get('meta') or {},
                    'slot': slot,
                    'blockTime': bt,
                }
                results.append(item)
        except Exception:
            continue
    return results


def extract_solana_transfers(token_symbol: str, token_address: str, lookback_hours: int) -> List[Dict]:
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=lookback_hours)
    start_ts = int(start_time.timestamp())
    end_ts = int(end_time.timestamp())

    print(f"    Extracting Solana {token_symbol}...")
    try:
        sigs = _fetch_signatures_paginated(token_address, start_ts, end_ts)
        # Fallback: include signatures where SPL Token programs are present (cache per window)
        window_key = (start_ts, end_ts)
        # Module-level cache to avoid re-fetching per token and hitting rate limits
        global _PROGRAM_SIG_CACHE
        try:
            _PROGRAM_SIG_CACHE
        except NameError:
            _PROGRAM_SIG_CACHE = {}

        if window_key not in _PROGRAM_SIG_CACHE:
            program_sigs: List[Dict] = []
            for pid in [
                "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                "TokenzQdBNbGqVY7YvETcWRmZz4fsZNb7wG9Y8v7cB",
            ]:
                try:
                    extra = _fetch_signatures_paginated(pid, start_ts, end_ts)
                    if extra:
                        program_sigs.extend(extra)
                except Exception:
                    continue
            # De-duplicate by signature
            _PROGRAM_SIG_CACHE[window_key] = list({s['signature']: s for s in program_sigs}.values())

        # Merge cached program signatures into token sigs
        sigs_map = {s['signature']: s for s in sigs}
        for e in _PROGRAM_SIG_CACHE.get(window_key, []):
            sigs_map[e['signature']] = e
        sigs = list(sigs_map.values())
        print(f"    Found {len(sigs)} signatures in window")

        signatures = [s['signature'] for s in sigs]
        txs = _get_parsed_transactions(signatures)
        if not txs:
            # Fallback to block-level fetch using slots
            slots = [s.get('slot') for s in sigs if isinstance(s.get('slot'), int)]
            txs = _get_block_transactions(slots)

        transfers: List[Dict] = []
        mint_decimals = _get_mint_decimals(token_address)

        # Cache owners to reduce RPC calls
        owners_cache: Dict[str, Optional[str]] = {}

        # Normalize account keys from message (strings or objects)
        def _normalize_account_keys(msg: Dict) -> List[str]:
            raw_keys = msg.get('accountKeys') or []
            keys: List[str] = []
            for k in raw_keys:
                if isinstance(k, dict):
                    pk = k.get('pubkey') or k.get('pubKey')
                    if isinstance(pk, str):
                        keys.append(pk)
                elif isinstance(k, str):
                    keys.append(k)
            return keys

        SPL_PROGRAM_IDS = {
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
            "TokenzQdBNbGqVY7YvETcWRmZz4fsZNb7wG9Y8v7cB",
        }

        def _decode_transfer_ix(inst: Dict, account_keys: List[str]) -> Optional[Dict]:
            try:
                # Determine program id
                pid = inst.get('programId')
                if pid is None:
                    idx = inst.get('programIdIndex')
                    if isinstance(idx, int) and idx < len(account_keys):
                        pid = account_keys[idx]
                if pid not in SPL_PROGRAM_IDS:
                    return None

                data_b58 = inst.get('data')
                if not isinstance(data_b58, str):
                    return None
                blob = base58.b58decode(data_b58)
                if not blob or len(blob) < 9:
                    return None
                instr_type = blob[0]
                if instr_type not in (3, 12):
                    return None
                amount = int.from_bytes(blob[1:9], byteorder='little')
                accts = inst.get('accounts') or []
                # Map indices to addresses if indices
                def addr_at(i: int) -> Optional[str]:
                    if not isinstance(i, int):
                        return None
                    if 0 <= i < len(account_keys):
                        return account_keys[i]
                    return None

                if instr_type == 12:  # TransferChecked: [src, mint, dst, owner, ...]
                    if len(accts) < 4:
                        return None
                    src = addr_at(accts[0])
                    mint = addr_at(accts[1])
                    dst = addr_at(accts[2])
                    owner = addr_at(accts[3])
                    return {
                        'source': src,
                        'destination': dst,
                        'authority': owner,
                        'mint': mint,
                        'amount': amount,
                        'tokenAmount': {'decimals': None},
                    }
                else:  # Transfer: [src, dst, owner]
                    if len(accts) < 3:
                        return None
                    src = addr_at(accts[0])
                    dst = addr_at(accts[1])
                    owner = addr_at(accts[2])
                    # Mint/decimals will be resolved from source account in append_transfer
                    return {
                        'source': src,
                        'destination': dst,
                        'authority': owner,
                        'amount': amount,
                    }
            except Exception:
                return None

        for tx in txs:
            bt = tx.get('blockTime')
            ts = datetime.fromtimestamp(bt, tz=timezone.utc) if bt else end_time
            slot = tx.get('slot', 0)

            # Helper to append a parsed transfer
            def append_transfer(info: Dict):
                mint = info.get('mint')
                source = info.get('source')
                destination = info.get('destination')
                authority = info.get('authority')

                # For plain 'transfer' (no mint in info), resolve via source token account
                source_decimals: Optional[int] = None
                if not mint and source:
                    mint, source_decimals = _get_account_mint_and_decimals(source)
                    if not mint:
                        return
                if mint != token_address:
                    return

                # Resolve owners for token accounts if needed
                def resolve_owner(acct: Optional[str]) -> Optional[str]:
                    if not acct:
                        return None
                    if acct in owners_cache:
                        return owners_cache[acct]
                    owner = _get_account_owner(acct)
                    owners_cache[acct] = owner
                    return owner

                sender = authority or resolve_owner(source) or source
                receiver = resolve_owner(destination) or destination

                amount_raw = info.get('amount') or (info.get('tokenAmount') or {}).get('amount')
                decimals = (info.get('tokenAmount') or {}).get('decimals')
                try:
                    if amount_raw is None:
                        amount = 0.0
                    elif decimals is not None:
                        amount = float(amount_raw) / (10 ** int(decimals))
                    else:
                        # Use source account decimals if available, else mint decimals
                        use_decimals = source_decimals if source_decimals is not None else mint_decimals
                        amount = float(amount_raw) / (10 ** int(use_decimals))
                except Exception:
                    amount = 0.0

                transfers.append({
                    'transaction_hash': (tx.get('transaction') or {}).get('signatures', [''])[0],
                    'sender': sender,
                    'receiver': receiver,
                    'value': amount,
                    'timestamp': ts,
                    'token_symbol': token_symbol,
                    'token_address': token_address,
                    'chain': 'solana',
                    'block_number': slot,
                })

            # Top-level instructions
            message = (tx.get('transaction') or {}).get('message') or {}
            account_keys = _normalize_account_keys(message)
            instructions = message.get('instructions') or []
            for inst in instructions:
                program = inst.get('program')
                if program not in ('spl-token', 'spl-token-2022'):
                    # Try decoding if no parsed helper
                    info_dec = _decode_transfer_ix(inst, account_keys)
                    if info_dec:
                        append_transfer(info_dec)
                    continue
                parsed = inst.get('parsed') or {}
                if parsed.get('type') in ('transfer', 'transferChecked'):
                    info = parsed.get('info') or {}
                    append_transfer(info)

            # Inner instructions (where many router and programmatic transfers occur)
            meta = tx.get('meta') or {}
            inner_groups = meta.get('innerInstructions') or []
            for group in inner_groups:
                for inst in group.get('instructions', []):
                    parsed = inst.get('parsed') or {}
                    # If parsed present and indicates transfer, use that
                    if parsed.get('type') in ('transfer', 'transferChecked'):
                        info = parsed.get('info') or {}
                        append_transfer(info)
                        continue
                    # Otherwise attempt base58 decode using account keys
                    info_dec = _decode_transfer_ix(inst, account_keys)
                    if info_dec:
                        append_transfer(info_dec)

        print(f"    ✓ Found {len(transfers)} transfers in range")
        return transfers
    except Exception as e:
        print(f"    ✗ Solana error: {e}")
        return []


def get_solana_activity_summary(token_address: str, days: int = 7) -> Dict:
    try:
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        start_ts = int(start_time.timestamp())
        end_ts = int(end_time.timestamp())
        sigs = _fetch_signatures_paginated(token_address, start_ts, end_ts)
        return {'total': len(sigs), 'recent': len(sigs), 'days': days}
    except Exception as e:
        return {'error': str(e)}
