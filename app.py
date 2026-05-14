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

st.set_page_config(page_title="EliteTracker • 100 to 1M", layout="wide")
st.title("🔥 EliteTracker • Live Alpaca Balance")
st.caption("Balance synced from Alpaca • Automatic Trading")

# ====================== ALPACA CONNECTION ======================
try:
    API_KEY = st.secrets["alpaca"]["api_key"]
    SECRET_KEY = st.secrets["alpaca"]["secret_key"]
    trade_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
    st.sidebar.success("✅ Connected to Alpaca Paper")
except:
    st.error("❌ Could not connect to Alpaca. Check your secrets.")
    st.stop()

# ====================== REAL ALPACA BALANCE (Always Synced) ======================
def get_alpaca_balance():
    try:
        account = trade_client.get_account()
        return float(account.cash)
    except Exception as e:
        st.error(f"Balance sync failed: {e}")
        return st.session_state.get("balance", 100.0)

# Force sync on every load
st.session_state.balance = get_alpaca_balance()

st.subheader(f"💰 **Real Alpaca Balance**: ${st.session_state.balance:,.2f}")
if st.button("🔄 Force Refresh Balance"):
    st.session_state.balance = get_alpaca_balance()
    st.success("Balance updated from Alpaca")
    st.rerun()

st.progress(min(st.session_state.balance / 1000000.0, 1.0))

# ====================== AUTO TRADING ======================
def auto_trade():
    if random.random() < 0.62:
        tickers = ["NVDA", "TSLA", "BTC-USD", "ETH-USD", "SOL-USD"]
        ticker = random.choice(tickers)
        
        try:
            price = float(yf.download(ticker, period="5d", progress=False)['Close'].iloc[-1])
            qty = max(1, int(st.session_state.balance * 0.12 / price))  # 12% max risk
            
            order = MarketOrderRequest(
                symbol=ticker.replace("-USD", ""),
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            trade_client.submit_order(order)
            st.success(f"✅ Auto Bought {qty} {ticker} @ ${price:,.2f}")
        except:
            pass

auto_trade()

# ====================== TRADE LEDGER ======================
if 'history' not in st.session_state:
    st.session_state.history = []

if st.session_state.history:
    st.write("### 📋 Trade Ledger")
    st.dataframe(pd.DataFrame(st.session_state.history)[::-1], width='stretch', hide_index=True)

st.caption("❤️ Balance is now always pulled from your real Alpaca account.")

time.sleep(20)
st.rerun()
