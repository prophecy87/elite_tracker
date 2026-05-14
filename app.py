"""
EliteForge v35 — Dual-Mode Trading System
Python 3.12 | Alpaca Paper Trading | Streamlit UI
Strategies:
  - Scalper : 5m BTC/ETH/SOL — EMA cross + RSI + volume surge confirmation
  - Swing   : 1h NVDA/TSLA/MSTR/BTC — EMA trend + MACD + ATR-based sizing
Risk management:
  - Per-trade risk capped at configurable % of equity (default 2%)
  - ATR stop-loss distance used for position sizing
  - Max N concurrent positions enforced
  - Drawdown circuit-breaker: halt if equity drops >X% from session high
"""

import time
import math
from datetime import datetime, timezone

import pandas as pd
import pandas_ta as ta
import streamlit as st
import yfinance as yf
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# ── page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EliteForge v35 • Dual-Mode",
    layout="wide",
    page_icon="⚔️",
)
st.markdown("""
<style>
    .stApp { background: #04040a; color: #dde3ff; font-family: 'Segoe UI', sans-serif; }
    .title { font-size:3rem; font-weight:900;
             background:linear-gradient(90deg,#00f2ff,#7b2fff);
             -webkit-background-clip:text; -webkit-text-fill-color:transparent;
             text-align:center; margin-bottom:0.2rem; }
    .sub   { text-align:center; color:#666; font-size:.85rem; margin-bottom:1.5rem; }
    .pill-green { background:rgba(0,255,150,.12); border:1px solid #00ff96;
                  color:#00ff96; padding:3px 10px; border-radius:20px;
                  font-size:.78rem; font-weight:700; }
    .pill-red   { background:rgba(255,60,60,.12); border:1px solid #ff3c3c;
                  color:#ff3c3c; padding:3px 10px; border-radius:20px;
                  font-size:.78rem; font-weight:700; }
    .pill-grey  { background:rgba(150,150,150,.1); border:1px solid #555;
                  color:#aaa; padding:3px 10px; border-radius:20px;
                  font-size:.78rem; }
    .risk-box { background:rgba(255,180,0,.08); border:1px solid #ffb400;
                border-radius:8px; padding:10px 16px; color:#ffb400;
                font-size:.82rem; margin-top:6px; }
    .halt-box { background:rgba(255,40,40,.12); border:1px solid #ff2828;
                border-radius:8px; padding:12px 16px; color:#ff4444;
                font-weight:700; text-align:center; font-size:1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">⚔️ ELITEFORGE v35</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">Dual-Mode Alpha Engine • Risk-First Architecture</div>', unsafe_allow_html=True)

# ── session state init ─────────────────────────────────────────────────────────
for key, default in {
    "session_high_equity": 0.0,
    "halted": False,
    "trade_log": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── sidebar controls ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")

    st.subheader("💰 Starting Capital")
    capital_tier = st.selectbox(
        "Challenge level",
        ["$100  — Crypto only", "$500", "$1,000", "$5,000", "$10,000", "$100,000"],
        index=0,
    )
    # Derive the rule: <$500 → crypto-only universe
    crypto_only: bool = capital_tier.startswith("$100 ")

    if crypto_only:
        st.markdown(
            '<div class="risk-box">🎯 <b>Sniper Mode</b> — $100 tier restricts '
            'execution to crypto assets only (BTC, ETH, SOL).</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="risk-box" style="border-color:#00ff96;color:#00ff96;">'
            '🌐 <b>Full Universe</b> — crypto + equities unlocked.</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.subheader("Strategies")
    scalper_on = st.toggle("🚀 Scalper  (5m crypto)", value=True)
    # Swing toggle is only meaningful when capital ≥ $500
    swing_on = st.toggle(
        "🏛️ Swing    (1h multi-asset)",
        value=not crypto_only,
        disabled=crypto_only,
        help="Requires $500+ capital tier to access equities.",
    )

    st.divider()
    st.subheader("Risk Controls")
    risk_pct      = st.slider("Risk per trade (%)", 0.5, 4.0, 2.0, 0.5)
    max_positions = st.slider("Max open positions", 2, 10, 5)
    drawdown_halt = st.slider("Circuit-breaker drawdown (%)", 3.0, 15.0, 8.0, 0.5)

    st.divider()
    st.subheader("Execution")
    paper_mode = st.toggle("Paper trading only", value=True)
    auto_trade = st.toggle("Auto-execute signals", value=False)
    scan_every = st.selectbox("Scan interval (s)", [30, 60, 120, 300], index=1)

    if not auto_trade:
        st.markdown(
            '<div class="risk-box">⚠️ Auto-execute OFF — signals shown but no orders placed.</div>',
            unsafe_allow_html=True,
        )

# ── alpaca client ──────────────────────────────────────────────────────────────
@st.cache_resource
def connect_alpaca() -> TradingClient | None:
    try:
        return TradingClient(
            st.secrets["alpaca"]["api_key"],
            st.secrets["alpaca"]["secret_key"],
            paper=paper_mode,
        )
    except Exception:
        return None

client = connect_alpaca()

# ── account helpers ────────────────────────────────────────────────────────────
def get_equity() -> float:
    if client is None:
        return 0.0
    try:
        return float(client.get_account().equity)
    except Exception:
        return 0.0

def get_buying_power() -> float:
    if client is None:
        return 0.0
    try:
        return float(client.get_account().buying_power)
    except Exception:
        return 0.0

def open_position_count() -> int:
    if client is None:
        return 0
    try:
        return len(client.get_all_positions())
    except Exception:
        return 0

def already_holding(symbol: str) -> bool:
    if client is None:
        return False
    try:
        held = {p.symbol for p in client.get_all_positions()}
        return symbol.replace("/", "") in held
    except Exception:
        return False

# ── position sizing ────────────────────────────────────────────────────────────
def calc_qty(price: float, equity: float, atr: float, is_crypto: bool) -> float:
    """
    ATR-based position sizing.
    risk_dollars / stop_distance = max units we can hold with defined risk.
    Also capped at risk_dollars / price to avoid oversizing.
    """
    if price <= 0 or atr <= 0:
        return 0.0
    risk_dollars   = equity * (risk_pct / 100.0)
    stop_distance  = max(atr * 1.5, price * 0.005)  # at least 0.5% stop
    qty            = risk_dollars / stop_distance
    max_qty        = risk_dollars / price             # spending cap
    qty            = min(qty, max_qty)
    if is_crypto:
        return round(qty, 6)
    qty = math.floor(qty)
    return float(qty) if qty >= 1 else 0.0

# ── order execution ────────────────────────────────────────────────────────────
def place_order(symbol: str, side: OrderSide, qty: float, reason: str) -> bool:
    if not auto_trade or client is None or qty <= 0:
        return False
    try:
        req = MarketOrderRequest(
            symbol=symbol.replace("/", ""),
            qty=qty,
            side=side,
            time_in_force=TimeInForce.GTC,
        )
        client.submit_order(req)
        st.session_state.trade_log.append({
            "time":   datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "symbol": symbol,
            "side":   side.value.upper(),
            "qty":    qty,
            "reason": reason,
        })
        return True
    except Exception as e:
        st.session_state.trade_log.append({
            "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "symbol": symbol, "side": "ERROR", "qty": qty, "reason": str(e),
        })
        return False

# ── data fetch ─────────────────────────────────────────────────────────────────
def fetch_ohlcv(asset: str, interval: str, period: str) -> pd.DataFrame | None:
    try:
        sym = asset.replace("/", "-")
        df  = yf.download(sym, period=period, interval=interval,
                          progress=False, auto_adjust=True)
        if df.empty or len(df) < 50:
            return None
        # flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0].lower() for c in df.columns]
        else:
            df.columns = [c.lower() for c in df.columns]
        return df
    except Exception:
        return None

# ── signal engines ─────────────────────────────────────────────────────────────
SCALPER_ASSETS      = ["BTC/USD", "ETH/USD", "SOL/USD"]
SWING_ASSETS_CRYPTO = ["BTC/USD", "ETH/USD", "SOL/USD"]
SWING_ASSETS_FULL   = ["BTC/USD", "ETH/USD", "NVDA", "TSLA", "MSTR", "SOL/USD"]

# Active swing universe — determined by capital tier
SWING_ASSETS = SWING_ASSETS_CRYPTO if crypto_only else SWING_ASSETS_FULL

def scalper_signal(asset: str) -> dict:
    """
    5m scalping:
      BUY  — EMA9 crosses above EMA21, RSI 35-65, volume > 1.5× 20-bar avg
      SELL — EMA9 crosses below EMA21, OR RSI > 72
    """
    df = fetch_ohlcv(asset, "5m", "3d")
    if df is None:
        return {"asset": asset, "signal": "NO DATA", "price": 0.0, "atr": 0.0, "detail": "fetch failed"}

    df["ema9"]  = ta.ema(df["close"], length=9)
    df["ema21"] = ta.ema(df["close"], length=21)
    df["rsi"]   = ta.rsi(df["close"], length=14)
    atr_s       = ta.atr(df["high"], df["low"], df["close"], length=14)
    df["atr"]   = atr_s

    vol_mean       = df["volume"].rolling(20).mean()
    df["vol_surge"] = df["volume"] > vol_mean * 1.5

    last  = df.iloc[-1]
    prev  = df.iloc[-2]
    price = float(last["close"])
    atr   = float(last["atr"]) if pd.notna(last["atr"]) else price * 0.01
    rsi   = float(last["rsi"]) if pd.notna(last["rsi"]) else 50.0

    ema_up   = (float(prev["ema9"]) <= float(prev["ema21"])) and (float(last["ema9"]) > float(last["ema21"]))
    ema_down = (float(prev["ema9"]) >= float(prev["ema21"])) and (float(last["ema9"]) < float(last["ema21"]))

    if ema_up and (35 < rsi < 65) and bool(last["vol_surge"]):
        signal = "BUY"
    elif ema_down or rsi > 72:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "asset":  asset,
        "signal": signal,
        "price":  price,
        "atr":    atr,
        "detail": f"EMA9={float(last['ema9']):.2f}  EMA21={float(last['ema21']):.2f}  RSI={rsi:.1f}",
    }

def swing_signal(asset: str) -> dict:
    """
    1h swing:
      BUY  — price > EMA50, MACD histogram flips positive, RSI < 70
      SELL — price < EMA50, OR MACD histogram flips negative, OR RSI > 75
    """
    df = fetch_ohlcv(asset, "1h", "60d")
    if df is None:
        return {"asset": asset, "signal": "NO DATA", "price": 0.0, "atr": 0.0, "detail": "fetch failed"}

    df["ema50"] = ta.ema(df["close"], length=50)
    macd_df     = ta.macd(df["close"], fast=12, slow=26, signal=9)
    df["macd_h"] = macd_df["MACDh_12_26_9"] if macd_df is not None else 0.0
    df["rsi"]    = ta.rsi(df["close"], length=14)
    atr_s        = ta.atr(df["high"], df["low"], df["close"], length=14)
    df["atr"]    = atr_s

    last  = df.iloc[-1]
    prev  = df.iloc[-2]
    price = float(last["close"])
    atr   = float(last["atr"]) if pd.notna(last["atr"]) else price * 0.015
    rsi   = float(last["rsi"]) if pd.notna(last["rsi"]) else 50.0
    ema50 = float(last["ema50"]) if pd.notna(last["ema50"]) else price

    above_ema    = price > ema50
    macd_up      = float(prev["macd_h"]) < 0 and float(last["macd_h"]) > 0
    macd_down    = float(prev["macd_h"]) > 0 and float(last["macd_h"]) < 0

    if above_ema and macd_up and rsi < 70:
        signal = "BUY"
    elif (not above_ema) or macd_down or rsi > 75:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "asset":  asset,
        "signal": signal,
        "price":  price,
        "atr":    atr,
        "detail": f"EMA50={ema50:.2f}  MACD_H={float(last['macd_h']):.4f}  RSI={rsi:.1f}",
    }

# ── circuit breaker ────────────────────────────────────────────────────────────
def check_circuit_breaker(equity: float) -> bool:
    if equity > st.session_state.session_high_equity:
        st.session_state.session_high_equity = equity
    high = st.session_state.session_high_equity
    if high > 0 and (high - equity) / high * 100 >= drawdown_halt:
        st.session_state.halted = True
    return st.session_state.halted

# ── execute a list of signals ──────────────────────────────────────────────────
def execute_signals(signals: list[dict], mode: str) -> None:
    eq = get_equity()
    n  = open_position_count()
    for s in signals:
        if s["signal"] == "BUY":
            # Capital-tier guard: $100 mode → crypto only
            is_crypto = "/" in s["asset"]
            if crypto_only and not is_crypto:
                continue
            if n >= max_positions:
                continue
            if already_holding(s["asset"]):
                continue
            qty = calc_qty(s["price"], eq, s["atr"], is_crypto)
            if place_order(s["asset"], OrderSide.BUY, qty, f"{mode} | {s['detail']}"):
                n += 1
        elif s["signal"] == "SELL" and already_holding(s["asset"]):
            # Look up actual held qty for a clean exit
            try:
                positions = client.get_all_positions()
                sym_clean = s["asset"].replace("/", "")
                for p in positions:
                    if p.symbol == sym_clean:
                        place_order(s["asset"], OrderSide.SELL,
                                    float(p.qty), f"{mode} exit | {s['detail']}")
                        break
            except Exception:
                pass

# ── dashboard ──────────────────────────────────────────────────────────────────
equity      = get_equity()
buy_power   = get_buying_power()
halted      = check_circuit_breaker(equity)
n_positions = open_position_count()
session_high = st.session_state.session_high_equity
dd = (session_high - equity) / session_high * 100 if session_high > 0 else 0.0

tab_term, tab_sig, tab_log = st.tabs(["⚡ Terminal", "🎯 Signals", "📜 Trade Log"])

# ── Terminal ───────────────────────────────────────────────────────────────────
with tab_term:
    if halted:
        st.markdown(
            f'<div class="halt-box">🛑 CIRCUIT BREAKER — Drawdown ≥ {drawdown_halt:.1f}% '
            f'from session high. Trading halted.</div>',
            unsafe_allow_html=True,
        )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Equity",          f"${equity:,.2f}")
    c2.metric("Buying Power",    f"${buy_power:,.2f}")
    c3.metric("Open Positions",  f"{n_positions} / {max_positions}")
    c4.metric("Session Drawdown", f"{dd:.2f}%", delta_color="inverse")

    tier_label = "🎯 Crypto-Only (Sniper)" if crypto_only else "🌐 Full Universe"
    st.markdown(
        f'<div class="risk-box" style="{"" if crypto_only else "border-color:#00ff96;color:#00ff96;"}">'
        f'Capital Tier: <b>{capital_tier}</b> &nbsp;|&nbsp; Mode: <b>{tier_label}</b>'
        f'{"&nbsp;— equities locked" if crypto_only else "&nbsp;— crypto + equities active"}</div>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.subheader("📊 Open Positions")
    if client:
        try:
            positions = client.get_all_positions()
            if positions:
                rows = [{
                    "Symbol": p.symbol,
                    "Qty":    p.qty,
                    "Entry":  f"${float(p.avg_entry_price):,.4f}",
                    "Price":  f"${float(p.current_price):,.4f}",
                    "Value":  f"${float(p.market_value):,.2f}",
                    "PnL $":  f"${float(p.unrealized_pl):+,.2f}",
                    "PnL %":  f"{(float(p.unrealized_pl)/float(p.cost_basis))*100:+.2f}%",
                } for p in positions]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.info("No open positions.")
        except Exception as e:
            st.error(f"Position fetch error: {e}")
    else:
        st.error("Alpaca offline — check st.secrets['alpaca'].")

# ── Signals ────────────────────────────────────────────────────────────────────
with tab_sig:
    if halted:
        st.error("🛑 Circuit breaker active — signals suppressed.")
    else:
        if scalper_on:
            st.subheader("🚀 Scalper  (5m)")
            with st.spinner("Scanning crypto…"):
                s_sigs = [scalper_signal(a) for a in SCALPER_ASSETS]
            execute_signals(s_sigs, "SCALP")
            st.dataframe(
                pd.DataFrame([{
                    "Asset":  s["asset"],
                    "Price":  f"${s['price']:,.2f}" if s["price"] else "—",
                    "Signal": s["signal"],
                    "ATR":    f"${s['atr']:.2f}" if s["atr"] else "—",
                    "Detail": s["detail"],
                } for s in s_sigs]),
                use_container_width=True, hide_index=True,
            )

        if swing_on and not crypto_only:
            st.subheader("🏛️ Swing  (1h)")
            with st.spinner("Scanning swing assets…"):
                sw_sigs = [swing_signal(a) for a in SWING_ASSETS]
            execute_signals(sw_sigs, "SWING")
            st.dataframe(
                pd.DataFrame([{
                    "Asset":  s["asset"],
                    "Price":  f"${s['price']:,.2f}" if s["price"] else "—",
                    "Signal": s["signal"],
                    "ATR":    f"${s['atr']:.2f}" if s["atr"] else "—",
                    "Detail": s["detail"],
                } for s in sw_sigs]),
                use_container_width=True, hide_index=True,
            )
        elif crypto_only:
            st.info("🔒 Swing equities (NVDA, TSLA, MSTR) locked — upgrade to $500+ tier to unlock.")

        if not scalper_on and not swing_on:
            st.info("Enable at least one strategy in the sidebar.")

# ── Trade Log ──────────────────────────────────────────────────────────────────
with tab_log:
    st.subheader("📜 Session Trade Log")
    log = st.session_state.trade_log
    if log:
        st.dataframe(
            pd.DataFrame(log[::-1]),
            use_container_width=True, hide_index=True,
        )
        if st.button("🗑️ Clear log"):
            st.session_state.trade_log = []
            st.rerun()
    else:
        st.info("No trades this session.")

    st.divider()
    st.caption(
        "Risk per trade is ATR-based, capped at the configured % of equity. "
        "All orders are GTC market orders. Signals are informational — "
        "enable Auto-execute to place real orders. Paper mode recommended."
    )

# ── auto-refresh (non-blocking caption) ───────────────────────────────────────
st.caption(f"⏱️ Next scan in ~{scan_every}s  •  {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")
time.sleep(scan_every)
st.rerun()
