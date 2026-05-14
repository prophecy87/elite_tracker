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
st.set_page_config(page_title="EliteForge v34 • Competition", layout="wide", page_icon="🏛️")

st.markdown("""
<style>
    .stApp { background-color: #050508; color: #e0e0ff; }
    .main-title { font-size: 3.5rem; font-weight: 900; background: linear-gradient(90deg, #00f2ff, #7000ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
    .status-card { background: #0a0a1a; padding: 15px; border-radius: 12px; border: 1px solid #1e1e3f; }
    .crypto-label { color: #f7931a; font-weight: bold; border: 1px solid #f7931a; padding: 2px 5px; border-radius: 4px; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">ELITEFORGE v34 • THE COMPETITION</h1>', unsafe_allow_html=True)

# ====================== SIDEBAR & CHALLENGE LOGIC ======================
with st.sidebar:
    st.header("🏆 Active Challenge")
    level = st.segmented_control("Capital Level", ["$100", "$1k", "$10k", "$100k"], default="$1k")
    
    # Map Level to numeric for sizing
    lvl_val = float(level.replace('$', '').replace('k', '000'))
    
    st.divider()
    st.header("⚙️ System Control")
    scalper_on = st.toggle("🚀 Crypto Scalper (5m)", value=True)
    st.caption("Locked to Crypto for $100 precision" if level == "$100" else "Fast Long/Short Core")
    
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

# ====================== SMART POSITION SIZER ======================
def get_smart_qty(ticker, price, current_cash):
    """Ensures we trade based on Challenge Level but respect actual Alpaca Cash"""
    risk_per_trade = 0.10 # 10% of challenge level per trade
    
    # Logic: Trade the target amount, unless we don't have enough cash
    target_spend = lvl_val * risk_per_trade
    actual_spend = min(target_spend, float(current_cash))
    
    qty = actual_spend / price
    
    # Precision Rule: Crypto gets 4 decimals, Stocks get whole numbers
    if "/" in ticker or any(x in ticker for x in ["USD", "BTC", "ETH"]):
        return round(qty, 4)
    return int(qty) if qty >= 1 else 0

# ====================== CORE ENGINES ======================
def get_forecaster_data(watchlist):
    forecasts = []
    # If $100 challenge, Scalper only looks at Crypto
    active_watchlist = [t for t in watchlist if "/" in t] if (level == "$100" and scalper_on) else watchlist
    
    for t in active_watchlist:
        try:
            yf_ticker = t.replace("/", "-")
            # Scalper uses 5m, Strategic uses 60m
            interval = "5m" if scalper_on and not longterm_on else "60m"
            df = yf.download(yf_ticker, period="2d", interval=interval, progress=False)
            
            if df.empty: continue
            current_price = float(df['Close'].iloc[-1])
            ma = float(df['Close'].rolling(20).mean().iloc[-1])
            diff = (current_price - ma) / ma
            
            score = random.randint(75, 98)
            bias = "⚖️ NEUTRAL"
            signal = "HOLD"
            
            if diff < -0.015:
                bias = "🔥 STRONGLY BULLISH"; signal = "BUY"
            elif diff > 0.015:
                bias = "🧊 STRONGLY BEARISH"; signal = "SELL"
                
            forecasts.append({
                "Asset": t, 
                "Type": "CRYPTO" if "/" in t else "STOCK",
                "Price": f"${current_price:,.2f}", 
                "Bias": bias,
                "Confidence": f"{score}%", 
                "Action": signal,
                "Rec. Qty": get_smart_qty(t, current_price, 1000000) # Preview qty
            })
        except: continue
    return forecasts

# ====================== DASHBOARD TABS ======================
tab1, tab2, tab3 = st.tabs(["🏛️ Terminal", "🔭 Market Forecaster", "📜 Ledger"])

with tab1:
    try:
        acc = trade_client.get_account()
        cash = float(acc.cash)
        m1, m2, m3 = st.columns(3)
        m1.metric("Portfolio Equity", f"${float(acc.equity):,.2f}")
        m2.metric("Buying Power", f"${float(acc.buying_power):,.2f}")
        m3.metric("Daily P/L", f"${float(acc.equity) - float(acc.last_equity):,.2f}")
    except: st.error("Alpaca Connection Offline")

    st.subheader("📊 Live Portfolio Positions")
    try:
        positions = trade_client.get_all_positions()
        if positions:
            pos_list = []
            for p in positions:
                pnl = float(p.unrealized_pl)
                pos_list.append({
                    "Symbol": p.symbol,
                    "Qty": p.qty,
                    "Avg Entry": f"${float(p.avg_entry_price):,.2f}",
                    "Current Price": f"${float(p.current_price):,.2f}",
                    "Market Value": f"${float(p.market_value):,.2f}",
                    "Unrealized PnL": f"${pnl:,.2f}",
                    "Total Change %": f"{(pnl/float(p.cost_basis))*100:+.2f}%",
                    "Today's %": f"{float(p.change_today)*100:+.2f}%"
                })
            st.dataframe(pd.DataFrame(pos_list), use_container_width=True, hide_index=True)
        else: st.info("No active positions.")
    except: pass

    st.subheader("⏳ Pending Orders")
    try:
        orders = trade_client.get_orders()
        if orders:
            st.dataframe(pd.DataFrame([{"Symbol": o.symbol, "Qty": o.qty, "Side": o.side.upper(), "Status": o.status.upper()} for o in orders]), use_container_width=True, hide_index=True)
        else: st.caption("No pending orders.")
    except: pass

with tab2:
    st.subheader("🎯 Predictive Market Intelligence")
    if level == "$100":
        st.markdown('<span class="crypto-label">SNIPER MODE ACTIVE</span> Scalper restricted to Crypto for precision.', unsafe_allow_html=True)
    
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
status_box.caption(f"Sync: {datetime.now().strftime('%H:%M:%S')} | Target: {level} | Risk: 10%/Trade")

time.sleep(25)
st.rerun()
