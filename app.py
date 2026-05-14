import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
import random
import json
import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# 1. PAGE SETUP (Must be very first)
st.set_page_config(page_title="EliteForge v22", layout="wide")

# 2. UI HEADER (Renders immediately so you know it's working)
st.title("🔥 EliteForge • 100 to 1M")
status_placeholder = st.empty() # For "Bot is thinking..." messages
status_placeholder.info("System Initializing...")

# 3. SECRETS & CLIENT (Cached to prevent re-connect hangs)
@st.cache_resource
def connect_alpaca():
    if "alpaca" not in st.secrets:
        return None
    return TradingClient(
        st.secrets["alpaca"]["api_key"], 
        st.secrets["alpaca"]["secret_key"], 
        paper=True
    )

trade_client = connect_alpaca()

if not trade_client:
    st.error("Missing Alpaca Secrets in Streamlit Settings.")
    st.stop()

# 4. DATA PERSISTENCE
if 'trades' not in st.session_state:
    st.session_state.trades = []
if 'balance' not in st.session_state:
    try:
        acc = trade_client.get_account()
        st.session_state.balance = float(acc.cash)
    except:
        st.session_state.balance = 100.0

# 5. MAIN DASHBOARD UI
col1, col2 = st.columns([2, 1])
with col1:
    st.metric("Real Alpaca Balance", f"${st.session_state.balance:,.2f}")
    st.progress(min(st.session_state.balance / 1000000.0, 1.0))

with col2:
    st.write("### Bot Status")
    st.success("🟢 LIVE & EXECUTING")

# 6. TRADE EXECUTION ENGINE
def run_trade_cycle():
    tickers = ["BTC/USD", "ETH/USD", "SOL/USD", "NVDA", "TSLA"]
    t = random.choice(tickers)
    
    status_placeholder.write(f"🔍 Analyzing {t}...")
    
    try:
        # Standardize ticker for YFinance
        yf_ticker = t.replace("/", "-")
        df = yf.download(yf_ticker, period="1d", interval="1m", progress=False)
        
        if not df.empty:
            price = float(df['Close'].iloc[-1])
            qty = (st.session_state.balance * 0.10) / price
            
            # Formatting for Alpaca
            symbol = t.replace("/", "") if "/" not in t else t
            qty = int(qty) if "/" not in t else round(qty, 4)
            
            if qty > 0:
                order = MarketOrderRequest(
                    symbol=symbol, qty=qty, side=OrderSide.BUY, time_in_force=TimeInForce.GTC
                )
                trade_client.submit_order(order)
                
                st.session_state.trades.append({
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Asset": symbol,
                    "Price": f"${price:,.2f}",
                    "Size": qty
                })
                return True
    except Exception as e:
        st.sidebar.error(f"Trade Error: {e}")
    return False

# 7. LEDGER DISPLAY
st.write("### 📜 Live Trade Ledger")
if st.session_state.trades:
    st.table(pd.DataFrame(st.session_state.trades)[::-1])
else:
    st.info("Waiting for first signal...")

# 8. THE HEARTBEAT (Controlled Rerun)
# We execute one cycle, then wait, then rerun.
if run_trade_cycle():
    status_placeholder.success(f"✅ Trade Executed at {datetime.now().strftime('%H:%M:%S')}")
else:
    status_placeholder.warning("Market scan complete - No trades triggered.")

time.sleep(30)
st.rerun()
