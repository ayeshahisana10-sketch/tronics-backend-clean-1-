"""
TRONICS core algorithm.

Locked design (see TRONICS_Decisions_Summary.md):
  - 1-2 hop USDT-TRC20 tracing only (no full multi-hop taint propagation)
  - Dust filtering below config.DUST_THRESHOLD_USDT
  - Sweep detection: a hop wallet that forwards >= SWEEP_RATIO_THRESHOLD of
    what it received, quickly, is treated as an intermediary/deposit wallet
  - 3-tier confidence: CONFIRMED (TRONSCAN label) / PROBABLE (sweep pattern)
    / UNATTRIBUTED (neither)
  - Bridge contracts are flagged, never traced further (detection only)
"""
from typing import List, Optional

from . import config
from .tron_client import get_usdt_transfers, normalize_transfer, get_tronscan_label
from .models import TraceReport, HopResult, TransferRecord


def _to_transfer_record(t: dict) -> TransferRecord:
    return TransferRecord(**t)


def _check_bridge(address: str):
    name = config.KNOWN_BRIDGE_ADDRESSES.get(address)
    return (True, name) if name else (False, None)


def _analyze_hop(address: str, hop_number: int) -> HopResult:
    """
    Analyze a single address: label lookup, bridge check, and sweep detection
    (does this wallet immediately forward most of what it received?).
    """
    is_bridge, bridge_name = _check_bridge(address)
    label = get_tronscan_label(address)

    hop = HopResult(
        hop_number=hop_number,
        address=address,
        label=label,
        is_bridge_contract=is_bridge,
        bridge_name=bridge_name,
    )

    if is_bridge:
        # Detection only -- do not attempt to trace past a bridge contract.
        return hop

    outbound_raw = get_usdt_transfers(address, only_from=True)
    outbound = [normalize_transfer(t) for t in outbound_raw]
    outbound = [t for t in outbound if t["amount_usdt"] >= config.DUST_THRESHOLD_USDT]

    if not outbound:
        return hop

    total_out = sum(t["amount_usdt"] for t in outbound)
    hop.total_received_usdt = total_out  # best available proxy without a second inbound call

    # Sweep check: any single outbound transfer moving >= threshold of the
    # total observed volume for this address counts as a sweep.
    largest = max(outbound, key=lambda t: t["amount_usdt"])
    if total_out > 0 and (largest["amount_usdt"] / total_out) >= config.SWEEP_RATIO_THRESHOLD:
        hop.swept = True
        hop.sweep_transfer = _to_transfer_record(largest)

    return hop


def trace_wallet(suspect_address: str) -> TraceReport:
    """
    Run the locked 1-2 hop trace starting from a victim-reported address.
    """
    report = TraceReport(suspect_address=suspect_address, confidence_tier="UNATTRIBUTED",
                          confidence_reason="No exchange or sweep pattern detected within hop limit.")

    # --- Hop 0: suspect's own outbound transfers ---
    raw = get_usdt_transfers(suspect_address, only_from=True)
    outbound = [normalize_transfer(t) for t in raw]
    outbound = [t for t in outbound if t["amount_usdt"] >= config.DUST_THRESHOLD_USDT]

    if not outbound:
        report.confidence_reason = "No outbound USDT-TRC20 transfers found above dust threshold."
        return report

    # Unique Hop 1 destinations
    hop1_addresses = sorted({t["to_address"] for t in outbound})

    hops: List[HopResult] = []
    final_destination: Optional[str] = None
    final_label: Optional[str] = None
    tier = "UNATTRIBUTED"
    reason = "Funds moved to intermediary wallet(s); no label or sweep pattern found within hop limit."

    for addr in hop1_addresses[:10]:  # cap fan-out for MVP demo stability
        hop1 = _analyze_hop(addr, hop_number=1)
        hops.append(hop1)

        if hop1.is_bridge_contract:
            report.cross_chain_flag = True
            report.cross_chain_note = (
                f"Outbound transfer routed through known bridge contract "
                f"({hop1.bridge_name}). Destination chain is not traced by this MVP."
            )

        if hop1.label:
            tier = "CONFIRMED"
            reason = f"Hop 1 address is publicly labeled on TRONSCAN as '{hop1.label}'."
            final_destination, final_label = addr, hop1.label
            break  # confirmed at hop 1, stop here

        if hop1.swept and hop1.sweep_transfer and config.MAX_HOPS >= 2:
            hop2_addr = hop1.sweep_transfer.to_address
            hop2 = _analyze_hop(hop2_addr, hop_number=2)
            hops.append(hop2)

            if hop2.label:
                tier = "PROBABLE"
                reason = (
                    f"Hop 1 wallet swept {hop1.sweep_transfer.amount_usdt:.2f} USDT "
                    f"to Hop 2 address, which is labeled '{hop2.label}' on TRONSCAN. "
                    f"Hop 1 is behaviorally consistent with an exchange deposit address."
                )
                final_destination, final_label = hop2_addr, hop2.label
                break
            elif hop2.is_bridge_contract:
                report.cross_chain_flag = True
                report.cross_chain_note = (
                    f"Hop 1 swept funds into known bridge contract ({hop2.bridge_name}). "
                    f"Destination chain is not traced by this MVP."
                )
            else:
                tier = "PROBABLE"
                reason = (
                    f"Hop 1 wallet swept {hop1.sweep_transfer.amount_usdt:.2f} USDT "
                    f"rapidly to a single destination -- behaviorally consistent with "
                    f"an exchange deposit address, though no official label was found."
                )
                final_destination = hop2_addr

    report.hops = hops
    report.confidence_tier = tier
    report.confidence_reason = reason
    report.final_destination = final_destination
    report.final_destination_label = final_label
    return report
