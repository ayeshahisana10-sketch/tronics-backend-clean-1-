"""
TRONICS backend.

Endpoints:
  POST /trace              -> run a 1-2 hop USDT-TRC20 trace on a suspect address
  POST /complaint-intake   -> MOCK NCRP/SAHYOG-style intake (clearly labeled, not
                              a real government integration -- none exists publicly)
  GET  /health             -> basic liveness check

Run locally:
  pip install -r requirements.txt
  export TRONGRID_API_KEY=your_key
  uvicorn app.main:app --reload
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import TraceRequest, TraceReport, ComplaintIntake
from tracer import trace_wallet
from alerts import maybe_send_alert
from tron_client import TronClientError
from db import save_trace_report, save_complaint, DatabaseNotConfigured

app = FastAPI(
    title="TRONICS",
    description=(
        "SIH26183 prototype: 1-2 hop USDT-TRC20 fund tracing from "
        "victim-reported TRON addresses toward possible exchange deposit points. "
        "All attributions are probabilistic; see disclaimer in every report."
    ),
    version="0.1.0-mvp",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before any real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


def _validate_tron_address(address: str) -> None:
    if not address.startswith("T") or len(address) != 34:
        raise HTTPException(
            status_code=400,
            detail="Invalid TRON address format (expected Base58, starts with 'T', 34 chars).",
        )


@app.post("/trace", response_model=TraceReport)
def trace(req: TraceRequest):
    _validate_tron_address(req.suspect_address)
    try:
        report = trace_wallet(req.suspect_address)
    except TronClientError as e:
        raise HTTPException(status_code=502, detail=str(e))

    maybe_send_alert(report)
    try:
        report_id = save_trace_report(report.model_dump())
    except DatabaseNotConfigured:
        report_id = None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trace completed but database save failed: {e}")
    response = report.model_copy()
    # Keep the response schema stable; the ID is available in a response header.
    from fastapi.responses import JSONResponse
    return JSONResponse(content=response.model_dump(), headers={"X-Trace-Report-ID": report_id or ""})


@app.post("/complaint-intake")
def complaint_intake(payload: ComplaintIntake):
    """
    MOCK integration endpoint. Demonstrates the data flow an NCRP/SAHYOG-style
    complaint submission could plausibly take -- no public API specification
    exists for either portal, so this is explicitly a mock, not a real
    integration. See Decisions Summary section 5.
    """
    _validate_tron_address(payload.reported_wallet)
    # In the real MVP demo: store payload, then run the same trace_wallet()
    # pipeline as /trace and attach the resulting report to this complaint.
    report = trace_wallet(payload.reported_wallet)
    maybe_send_alert(report)
    try:
        complaint_row_id = save_complaint(payload.model_dump(), report.model_dump())
        trace_row_id = save_trace_report(report.model_dump())
    except DatabaseNotConfigured:
        complaint_row_id = None
        trace_row_id = None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trace completed but database save failed: {e}")
    return {
        "status": "received",
        "reference_id": f"MOCK-REF-{payload.complaint_id}",
        "note": "This is a MOCK integration endpoint; no live NCRP/SAHYOG connection exists.",
        "complaint_row_id": complaint_row_id,
        "trace_report_id": trace_row_id,
        "trace_report": report,
    }
