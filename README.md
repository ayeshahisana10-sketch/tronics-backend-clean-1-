# TRONICS Backend — SIH26183 MVP

1–2 hop USDT-TRC20 fund tracing from a victim-reported TRON address toward
a possible exchange deposit point, with a 3-tier confidence system and a
mock NCRP/SAHYOG-style intake endpoint.

## Setup

```bash
cd tronics
pip install -r requirements.txt
cp .env.example .env
```

Get a free TronGrid API key at https://www.trongrid.io (2-minute signup),
then put it in `.env`:

```
TRONGRID_API_KEY=your_key_here
```

## Run

```bash
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs for interactive API docs (FastAPI
auto-generates this — use it to test without building the frontend first).

## Try the verified test case

Once running, POST to `/trace`:

```json
{
  "suspect_address": "TWPma8xH48AEN93x2krdukV9e1j6sPsBeS"
}
```

This is the largest of the 10 wallets frozen by Tether on Sept 8, 2026 in
connection with Xinbi Guarantee (confirmed via MistTrack + multiple
independent news sources — see Decisions Summary doc). It's a genuine,
verifiable, high-profile case, good for demoing and for judges' Q&A.

## What this MVP does and does not do

**Does:**
- Fetches real USDT-TRC20 transfers via TronGrid, filtered to the official
  contract at both API and application level
- Detects "sweep" behavior (Hop 1 wallet forwarding most received funds
  quickly to Hop 2)
- Checks TRONSCAN for public exchange labels
- Assigns CONFIRMED / PROBABLE / UNATTRIBUTED confidence tiers
- Flags (but does not trace through) known bridge contracts
- Sends a Telegram alert on CONFIRMED/PROBABLE results (optional, needs
  bot token configured)
- Provides a mock `/complaint-intake` endpoint modeled on the shape an
  NCRP/SAHYOG submission would plausibly take

**Does not do (by design, stated explicitly in the PPT):**
- Full multi-hop taint propagation beyond 2 hops
- Real cross-chain fund tracing (bridge interactions are flagged, not
  followed onto the destination chain)
- Real NCRP/SAHYOG integration (no public API exists for either — verified)
- ML/GNN-based scoring
- Multi-blockchain support (TRON/USDT-TRC20 only)

See `TRONICS_Decisions_Summary.md` for the full rationale behind every
one of these choices and the exact language to use (and avoid) in the PPT.

## Next step: frontend

This backend exposes `/trace` (POST) and `/complaint-intake` (POST). The
frontend just needs: a form for the suspect address, a call to `/trace`,
and a display of the returned `TraceReport` (hops, confidence tier, reason,
final destination) — ideally with the hop chain rendered as a simple graph.

## Supabase setup

1. Open the Supabase SQL Editor for your project.
2. Run `supabase_schema.sql`.
3. Copy `.env.example` to `.env`.
4. Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in the backend `.env`.
5. Install dependencies again with `pip install -r requirements.txt`.

Use the Supabase **server-side secret/service-role key only in the backend**.
Do not put it in the frontend, GitHub, or the browser. The `/trace` endpoint
saves reports in `trace_reports`; `/complaint-intake` saves complaints in
`complaints` and also saves the generated trace report.

If Supabase variables are absent, tracing can still run, but persistence is
skipped. For a deployed demo, configure the variables so persistence is active.
