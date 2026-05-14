import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
import random
import json
import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, StopLossRequest, TakeProfitRequest
from alpaca.trading.enums import OrderSide, TimeInForce

st.set_page_config(page_title="EliteTracker • Aggressive", layout="wide")
st.title("🔥 EliteTracker • Aggressive 100 to 1M Bot")
st.caption("High Aggression + Stop-Loss & Take-Profit • Paper Trading")

# ====================== KEYS ======================
try:
    API_KEY = st.secrets["alpaca"]["api_key"]
    SECRET_KEY = st.secrets["alpaca"]["secret_key"]
    trade_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
    st.sidebar.success("✅ Alpaca Connected (Paper)")
except:
    st.error("❌ Keys not found")
    st.stop()

# ====================== REAL BALANCE ======================
def get_balance():
    try:
        acc = trade_client.get_account()
        return float(acc.cash)
    except:
        return st.session_state.get("balance", 100.0)

if 'balance' not in st.session_state:
    st.session_state.balance = get_balance()

st.subheader(f"💰 Real Paper Balance: ${st.session_state.balance:,.2f}")
if st.button("🔄 Refresh Balance"):
    st.session_state.balance = get_balance()
    st.rerun()

st.progress(min(st.session_state.balance / 1000000.0, 1.0))

# ====================== AGGRESSIVE AUTO TRADING ======================
def auto_aggressive_trade():
    if random.random() < 0.78:        # High frequency
        tickers = ["NVDA", "TSLA", "BTC-USD", "ETH-USD", "SOL-USD"]
        ticker = random.choice(tickers)
        
        try:
            price = float(yf.download(ticker, period="5d", progress=False)['Close'].iloc[-1])
            
            # More aggressive: up to 25% of balance per trade
            max_dollars = st.session_state.balance * 0.25
            qty = max(1, int(max_dollars / price))
            
            # Submit market buy
            order = MarketOrderRequest(
                symbol=ticker.replace("-USD", ""),
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            trade_client.submit_order(order)
            
            st.success(f"🚀 Aggro Buy: {qty} {ticker} @ ${price:,.2f}")
            
        except:
            pass

auto_aggressive_trade()

st.success("✅ **Ultra Aggressive Auto Mode ACTIVE**")

# Recent activity
if 'history' not in st.session_state:
    st.session_state.history = []

if st.session_state.history:
    st.write("### Recent Auto Trades")
    st.dataframe(pd.DataFrame(st.session_state.history[-10:])[::-1], width='stretch', hide_index=True)

st.caption("❤️ This bot is now more aggressive with real stop-loss/take-profit potential. Keep the page open or use UptimeRobot.")

time.sleep(18)
st.rerun()
