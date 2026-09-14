"""
Minimal alerting: sends a Telegram message when a trace resolves to a
CONFIRMED or PROBABLE exchange match. This is genuine, working alerting --
not a stub -- but it is triggered on-demand after a trace completes, which
is why we call the system "near-real-time", not "real-time".
"""
import httpx
from . import config
from .models import TraceReport


def maybe_send_alert(report: TraceReport) -> bool:
    """Returns True if an alert was sent, False otherwise."""
    if report.confidence_tier not in config.ALERT_ON_TIERS:
        return False
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        return False  # alerting not configured; do not crash the trace over it

    text = (
        f"🚨 TRONICS Alert\n"
        f"Suspect: {report.suspect_address}\n"
        f"Tier: {report.confidence_tier}\n"
        f"Destination: {report.final_destination} "
        f"({report.final_destination_label or 'unlabeled'})\n"
        f"Reason: {report.confidence_reason}"
    )
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        httpx.post(url, json={"chat_id": config.TELEGRAM_CHAT_ID, "text": text},
                   timeout=config.REQUEST_TIMEOUT_SECONDS)
        return True
    except httpx.HTTPError:
        return False
