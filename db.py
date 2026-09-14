"""Supabase persistence layer.

The backend uses the Supabase server-side key only. Never expose this key in
frontend code or commit it to source control.
"""
import os
from typing import Any, Dict, Optional

try:
    from supabase import create_client, Client
except ImportError:  # keeps local imports clearer if dependency is not installed yet
    create_client = None
    Client = Any


class DatabaseNotConfigured(RuntimeError):
    pass


_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is not None:
        return _client
    if create_client is None:
        raise DatabaseNotConfigured("supabase package is not installed")
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        raise DatabaseNotConfigured(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required for database persistence"
        )
    _client = create_client(url, key)
    return _client


def save_trace_report(report: Dict[str, Any]) -> Optional[str]:
    """Save a complete trace report. Returns the generated row id."""
    client = get_client()
    row = {
        "suspect_address": report["suspect_address"],
        "confidence_tier": report["confidence_tier"],
        "confidence_reason": report["confidence_reason"],
        "final_destination": report.get("final_destination"),
        "final_destination_label": report.get("final_destination_label"),
        "cross_chain_flag": report.get("cross_chain_flag", False),
        "cross_chain_note": report.get("cross_chain_note"),
        "report_json": report,
    }
    result = client.table("trace_reports").insert(row).execute()
    data = getattr(result, "data", None) or []
    return str(data[0]["id"]) if data and data[0].get("id") is not None else None


def save_complaint(payload: Dict[str, Any], report: Optional[Dict[str, Any]] = None) -> Optional[str]:
    client = get_client()
    row = {
        "complaint_id": payload["complaint_id"],
        "reported_wallet": payload["reported_wallet"],
        "blockchain": payload.get("blockchain", "TRON"),
        "token": payload.get("token", "USDT-TRC20"),
        "victim_amount": payload.get("victim_amount"),
        "transaction_hash": payload.get("transaction_hash"),
        "reported_at": payload.get("timestamp"),
        "trace_report_json": report,
    }
    result = client.table("complaints").insert(row).execute()
    data = getattr(result, "data", None) or []
    return str(data[0]["id"]) if data and data[0].get("id") is not None else None
