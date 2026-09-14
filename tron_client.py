"""
Thin wrappers around TronGrid (transaction data) and TRONSCAN (address labels).

Both are queried with the official USDT-TRC20 contract filter applied at the
API level. Every returned record is re-checked at the application level in
tracer.py before being used -- filtering happens at both layers per our
locked technical decision.
"""
import httpx
from typing import List, Dict, Any, Optional

import config


class TronClientError(Exception):
    pass


def _trongrid_headers() -> Dict[str, str]:
    headers = {"accept": "application/json"}
    if config.TRONGRID_API_KEY:
        headers["TRON-PRO-API-KEY"] = config.TRONGRID_API_KEY
    return headers


def get_usdt_transfers(address: str, only_from: bool = True) -> List[Dict[str, Any]]:
    """
    Fetch USDT-TRC20 transfers for an address via TronGrid, filtered by the
    official contract address at the API-query level.

    only_from=True  -> outbound transfers only (what we need for tracing)
    only_from=False -> inbound transfers (useful for sweep verification)
    """
    url = f"{config.TRONGRID_BASE_URL}/v1/accounts/{address}/transactions/trc20"
    params = {
        "limit": config.MAX_TRANSFERS_PER_QUERY,
        "contract_address": config.USDT_TRC20_CONTRACT,
        "only_confirmed": "true",
    }
    if only_from:
        params["only_from"] = "true"
    else:
        params["only_to"] = "true"

    try:
        resp = httpx.get(
            url, headers=_trongrid_headers(), params=params,
            timeout=config.REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        payload = resp.json()
    except httpx.HTTPError as e:
        raise TronClientError(f"TronGrid request failed for {address}: {e}") from e

    records = payload.get("data", [])

    # Application-level re-check: never trust the API filter alone.
    verified = [
        r for r in records
        if r.get("token_info", {}).get("address") == config.USDT_TRC20_CONTRACT
    ]
    return verified


def normalize_transfer(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a raw TronGrid TRC-20 record into our internal shape."""
    decimals = raw.get("token_info", {}).get("decimals", 6)
    raw_value = int(raw.get("value", 0))
    amount_usdt = raw_value / (10 ** decimals)
    return {
        "tx_hash": raw.get("transaction_id", ""),
        "from_address": raw.get("from", ""),
        "to_address": raw.get("to", ""),
        "amount_usdt": amount_usdt,
        "timestamp_ms": raw.get("block_timestamp", 0),
    }


def get_tronscan_label(address: str) -> Optional[str]:
    """
    Look up a public TRONSCAN label for an address (e.g. exchange hot wallet
    tags). Returns None if no label is found or the lookup fails -- a failed
    lookup must never be treated as "confirmed no label", it should fall
    through to behavioral analysis.
    """
    url = f"{config.TRONSCAN_BASE_URL}/accountv2"
    params = {"address": address}
    headers = {"accept": "application/json"}
    if config.TRONSCAN_API_KEY:
        headers["TRON-PRO-API-KEY"] = config.TRONSCAN_API_KEY

    try:
        resp = httpx.get(url, headers=headers, params=params,
                          timeout=config.REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError:
        return None  # do not fail the whole trace over a label lookup

    name = data.get("name") or ""
    tag = data.get("addressTag", {}) or {}
    tag_name = tag.get("name") if isinstance(tag, dict) else None

    label = name or tag_name
    return label if label else None
