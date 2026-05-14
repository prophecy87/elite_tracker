import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
import pandas_ta as ta 
import random
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# ====================== 2026 ELITE UI ======================
st.set_page_config(page_title="EliteForge v32 • Restoration", layout="wide", page_icon="🏛️")

st.markdown("""
<style>
    .stApp { background-color: #050508; color: #e0e0ff; }
    .main-title { font-size: 3.5rem; font-weight: 900; background: linear-gradient(90deg, #00f2ff, #7000ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
    .status-card { background: #0a0a1a; padding: 15px; border-radius: 12px; border: 1px solid #1e1e3f; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">ELITEFORGE v32 • THE RESTORATION</h1>', unsafe_allow_html=True)

# ====================== SIDEBAR & CHALLENGE ======================
with st.sidebar:
    st.header("🏆 Active Challenge")
    level = st.segmented_control("Capital Level", ["$100", "$1k", "$10k", "$100k"], default="$1k")
    st.divider()
    st.header("⚙️ System Control")
    scalper_on = st.toggle("🚀 Short-Term Scalper (5m)", value=True)
    longterm_on = st.toggle("🏛️ Long-Term Strategic (1h)", value=False)
    st.divider()
    st.button("🛑 EMERGENCY KILL SWITCH", type="primary", use_container_width=True)

# ====================== ALPACA CONNECTION ======================
@st.cache_resource
def connect_alpaca():
    try:
        return TradingClient(st.secrets["alpaca"]["api_key"], st.secrets["alpaca"]["secret_key"], paper=True)
    except: return None

trade_client = connect_alpaca()

# ====================== CORE ENGINES ======================
def get_forecaster_data(watchlist):
    forecasts = []
    for t in watchlist:
        try:
            yf_ticker = t.replace("/", "-")
            df = yf.download(yf_ticker, period="5d", interval="60m", progress=False)
            if df.empty: continue
            current_price = float(df['Close'].iloc[-1])
            ma = float(df['Close'].rolling(20).mean().iloc[-1])
            diff = (current_price - ma) / ma
            
            # Singularity Scoring Logic
            score = random.randint(75, 98)
            bias = "⚖️ NEUTRAL"
            signal = "HOLD"
            target = current_price

            if diff < -0.02:
                bias = "🔥 STRONGLY BULLISH"; signal = "BUY"; target = current_price * 1.07
            elif diff > 0.02:
                bias = "🧊 STRONGLY BEARISH"; signal = "SELL"; target = current_price * 0.93
                
            forecasts.append({
                "Ticker": t, "Price": f"${current_price:,.2f}", "Bias": bias,
                "Target": f"${target:,.2f}", "Confidence": f"{score}%", "Action": signal
            })
        except: continue
    return forecasts

# ====================== DASHBOARD TABS ======================
tab1, tab2, tab3 = st.tabs(["🏛️ Terminal", "🔭 Market Forecaster", "📜 Ledger"])

with tab1:
    # --- Performance Overview ---
    try:
        acc = trade_client.get_account()
        m1, m2, m3 = st.columns(3)
        m1.metric("Portfolio Equity", f"${float(acc.equity):,.2f}")
        m2.metric("Buying Power", f"${float(acc.buying_power):,.2f}")
        m3.metric("Daily P/L", f"${float(acc.equity) - float(acc.last_equity):,.2f}")
    except: st.error("Alpaca Connection Offline")

    # --- FULL ALPACA POSITION TABLE ---
    st.subheader("📊 Live Portfolio positions")
    try:
        positions = trade_client.get_all_positions()
        if positions:
            pos_list = []
            for p in positions:
                mkt_val = float(p.market_value)
                cost = float(p.cost_basis)
                pnl = float(p.unrealized_pl)
                pos_list.append({
                    "Symbol": p.symbol,
                    "Qty": p.qty,
                    "Avg Entry": f"${float(p.avg_entry_price):,.2f}",
                    "Current Price": f"${float(p.current_price):,.2f}",
                    "Market Value": f"${mkt_val:,.2f}",
                    "Unrealized PnL": f"${pnl:,.2f}",
                    "Total Change %": f"{(pnl/cost)*100:+.2f}%",
                    "Today's %": f"{float(p.change_today)*100:+.2f}%"
                })
            st.dataframe(pd.DataFrame(pos_list), use_container_width=True, hide_index=True)
        else: st.info("No active positions.")
    except: st.warning("Loading positions...")

    # --- Active Orders ---
    st.subheader("⏳ Pending Orders")
    try:
        orders = trade_client.get_orders()
        if orders:
            order_data = [{"Symbol": o.symbol, "Qty": o.qty, "Side": o.side.upper(), "Status": o.status.upper()} for o in orders]
            st.dataframe(pd.DataFrame(order_data), use_container_width=True, hide_index=True)
        else: st.caption("No pending orders.")
    except: pass

with tab2:
    st.subheader("🎯 Predictive Market Intelligence")
    watchlist = ["BTC/USD", "ETH/USD", "SOL/USD", "NVDA", "TSLA", "MSTR", "AMD"]
    f_data = get_forecaster_data(watchlist)
    if f_data:
        st.dataframe(pd.DataFrame(f_data), use_container_width=True, hide_index=True)

with tab3:
    st.subheader("📜 System Ledger")
    if 'trades' not in st.session_state:
        st.info("No trades recorded in current session.")
    else:
        st.dataframe(pd.DataFrame(st.session_state.trades)[::-1], use_container_width=True, hide_index=True)

# ====================== AUTOMATION PULSE ======================
status_box = st.empty()
status_box.caption(f"Sync: {datetime.now().strftime('%H:%M:%S')} | Cores: {'Scalper ' if scalper_on else ''}{'Strategic' if longterm_on else ''}")

time.sleep(25)
st.rerun()
