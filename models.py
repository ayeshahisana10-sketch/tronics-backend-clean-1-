from typing import List, Optional
from pydantic import BaseModel, Field


class TraceRequest(BaseModel):
    suspect_address: str = Field(..., description="Victim-reported TRON address (starts with T)")


class TransferRecord(BaseModel):
    tx_hash: str
    from_address: str
    to_address: str
    amount_usdt: float
    timestamp_ms: int


class HopResult(BaseModel):
    hop_number: int
    address: str
    label: Optional[str] = None            # TRONSCAN label, if any
    is_bridge_contract: bool = False
    bridge_name: Optional[str] = None
    inbound_transfers: List[TransferRecord] = Field(default_factory=list)
    total_received_usdt: float = 0.0
    swept: bool = False                    # forwarded >= threshold quickly
    sweep_transfer: Optional[TransferRecord] = None


class TraceReport(BaseModel):
    suspect_address: str
    confidence_tier: str                   # CONFIRMED | PROBABLE | UNATTRIBUTED
    confidence_reason: str
    final_destination: Optional[str] = None
    final_destination_label: Optional[str] = None
    hops: List[HopResult] = Field(default_factory=list)
    cross_chain_flag: bool = False
    cross_chain_note: Optional[str] = None
    disclaimer: str = (
        "This report is generated from on-chain data and publicly available "
        "address labels. Attributions are probabilistic and based on documented "
        "heuristics. It does not constitute legal evidence and should be verified "
        "through official channels before any action is taken."
    )


class ComplaintIntake(BaseModel):
    """
    Mock schema modeled on the kind of payload NCRP/SAHYOG-style intake would
    plausibly use. This is NOT an official government data contract -- no
    public specification exists. Labeled explicitly as a mock integration.
    """
    complaint_id: str
    reported_wallet: str
    blockchain: str = "TRON"
    token: str = "USDT-TRC20"
    victim_amount: Optional[float] = None
    transaction_hash: Optional[str] = None
    timestamp: Optional[str] = None
