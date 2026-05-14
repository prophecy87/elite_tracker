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

# ====================== 2026 COMPETITION UI ======================
st.set_page_config(page_title="EliteForge v34 • Competition", layout="wide", page_icon="🏛️")

st.markdown("""
<style>
    .stApp { background-color: #020205; color: #e0e0ff; }
    .main-title { font-size: 3.5rem; font-weight: 900; background: linear-gradient(90deg, #00f2ff, #7000ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
    .sniper-status { background: rgba(0, 255, 204, 0.1); border: 1px solid #00ffcc; padding: 10px; border-radius: 8px; text-align: center; color: #00ffcc; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">ELITEFORGE v34</h1>', unsafe_allow_html=True)

# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("🏆 Challenge Selection")
    level = st.segmented_control("Initial Capital", ["$100", "$1k", "$10k", "$100k"], default="$100")
    
    st.divider()
    st.header("⚙️ Engine Toggles")
    scalper_on = st.toggle("🚀 Crypto Scalper (5m)", value=True)
    longterm_on = st.toggle("🏛️ Strategic (1h)", value=False)
    
    # Quantitative Guardrail
    lvl_val = float(level.replace('$', '').replace('k', '000'))
    risk_amt = lvl_val * 0.10 # 10% Risk

# ====================== ALPACA ======================
@st.cache_resource
def connect_alpaca():
    try:
        return TradingClient(st.secrets["alpaca"]["api_key"], st.secrets["alpaca"]["secret_key"], paper=True)
    except: return None

trade_client = connect_alpaca()

# ====================== QUANT SIZING ENGINE ======================
def get_qty(ticker, price, cash):
    # The Sniper Rule: If $100 challenge, only trade Crypto
    if level == "$100" and not ("/" in ticker or "USD" in ticker):
        return 0
        
    target_spend = min(risk_amt, float(cash))
    qty = target_spend / price
    return round(qty, 4) if "/" in ticker else int(qty)

# ====================== DASHBOARD ======================
tab1, tab2, tab3 = st.tabs(["🏛️ Terminal", "🔭 Forecaster", "📜 Ledger"])

with tab1:
    try:
        acc = trade_client.get_account()
        m1, m2, m3 = st.columns(3)
        m1.metric("Account Equity", f"${float(acc.equity):,.2f}")
        m2.metric("Buying Power", f"${float(acc.buying_power):,.2f}")
        m3.metric("Challenge Mode", level)
        
        if level == "$100":
            st.markdown('<div class="sniper-status">🎯 SNIPER MODE: Crypto-Only Execution Active</div>', unsafe_allow_html=True)
    except: st.error("Connection Offline")

    # FULL POSITION TABLE (Restored)
    st.subheader("📊 Open Positions")
    try:
        positions = trade_client.get_all_positions()
        if positions:
            df_pos = pd.DataFrame([{
                "Symbol": p.symbol, "Qty": p.qty, 
                "Entry": f"${float(p.avg_entry_price):,.2f}",
                "Price": f"${float(p.current_price):,.2f}",
                "Value": f"${float(p.market_value):,.2f}",
                "PnL": f"${float(p.unrealized_pl):,.2f}",
                "Total %": f"{(float(p.unrealized_pl)/float(p.cost_basis))*100:+.2f}%"
            } for p in positions])
            st.dataframe(df_pos, use_container_width=True, hide_index=True)
        else: st.info("Waiting for entry signal...")
    except: pass

with tab2:
    st.subheader("🎯 Predictive Signals")
    # Sniper-restricted watchlist
    watchlist = ["BTC/USD", "ETH/USD", "SOL/USD"] if level == "$100" else ["BTC/USD", "NVDA", "TSLA", "MSTR"]
    
    results = []
    for asset in watchlist:
        try:
            df = yf.download(asset.replace("/","-"), period="2d", interval="5m", progress=False)
            curr = df['Close'].iloc[-1]
            ma = df['Close'].rolling(20).mean().iloc[-1]
            diff = (curr - ma) / ma
            results.append({
                "Asset": asset, "Price": f"${curr:,.2f}", 
                "Bias": "BULLISH" if diff < -0.01 else "BEARISH" if diff > 0.01 else "NEUTRAL",
                "Action": "BUY" if diff < -0.01 else "SELL" if diff > 0.01 else "HOLD"
            })
        except: continue
    st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)

# ====================== PULSE ======================
time.sleep(25)
st.rerun()
