"""
TRONICS configuration.
All values are read from environment variables so nothing sensitive
is hard-coded. Copy .env.example to .env and fill in your keys.
"""
import os

# --- TRON / USDT ---
USDT_TRC20_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # verified official contract

TRONGRID_BASE_URL = "https://api.trongrid.io"
TRONGRID_API_KEY = os.environ.get("TRONGRID_API_KEY", "")

TRONSCAN_BASE_URL = "https://apilist.tronscanapi.com/api"
TRONSCAN_API_KEY = os.environ.get("TRONSCAN_API_KEY", "")

# --- Tracing parameters (tune here, not buried in logic) ---
MAX_HOPS = 2
DUST_THRESHOLD_USDT = 100.0        # ignore transfers below this amount
SWEEP_RATIO_THRESHOLD = 0.90       # >=90% forwarded quickly => "sweep"
MAX_TRANSFERS_PER_QUERY = 100

# --- Known bridge contracts on TRON (detection only, not tracing) ---
# Source: Bungee official docs (verified). Extend this list as you verify more.
KNOWN_BRIDGE_ADDRESSES = {
    "TVLrWiPWF6xRanrMfET5xsQibDm2eSbFiP": "Bungee AUTO (TRON)",
    "TWMsLzKo9sCzQP4Sh4cbgZpCZnXCTyeiHn": "Bungee Depository Tron AUTO",
    "TVm2o3iaUAQ6JC5Rp1uzGqF91nn4Mvh2HW": "Bungee Simple AUTO",
}

# --- Alerts ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
ALERT_ON_TIERS = {"CONFIRMED", "PROBABLE"}  # which confidence tiers trigger an alert

# --- HTTP ---
REQUEST_TIMEOUT_SECONDS = 20

# --- Supabase ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
