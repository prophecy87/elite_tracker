import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
import random
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

st.set_page_config(page_title="EliteTracker Debug", layout="wide")
st.title("🔥 EliteTracker • Debug Mode")
st.caption("Aggressive Auto Trader + Manual Test")

# ====================== CONNECTION ======================
try:
    API_KEY = st.secrets["alpaca"]["api_key"]
    SECRET_KEY = st.secrets["alpaca"]["secret_key"]
    trade_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
    st.success("✅ Connected to Alpaca Paper Trading")
except:
    st.error("❌ Alpaca connection failed")
    st.stop()

# ====================== BALANCE ======================
def get_balance():
    try:
        acc = trade_client.get_account()
        return float(acc.cash)
    except:
        return 100.0

if 'balance' not in st.session_state:
    st.session_state.balance = get_balance()

st.subheader(f"💰 Alpaca Paper Balance: ${st.session_state.balance:,.2f}")

if st.button("🔄 Refresh Balance"):
    st.session_state.balance = get_balance()
    st.rerun()

# ====================== MANUAL TRADE BUTTON (for testing) ======================
st.write("### Test Trade")
col1, col2 = st.columns(2)
with col1:
    ticker = st.selectbox("Ticker", ["NVDA", "TSLA", "BTC-USD", "ETH-USD", "SOL-USD"])
with col2:
    if st.button("🚀 Execute Manual Buy Now", type="primary"):
        try:
            price = float(yf.download(ticker, period="1d", progress=False)['Close'].iloc[-1])
            qty = 1  # Safe small size for testing
            
            order = MarketOrderRequest(
                symbol=ticker.replace("-USD", ""),
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            trade_client.submit_order(order)
            st.success(f"✅ Order Submitted: Bought {qty} {ticker} @ ~${price:,.2f}")
        except Exception as e:
            st.error(f"Failed: {e}")

# ====================== AUTO TRADING ======================
def auto_trade():
    if random.random() < 0.55:   # Increased chance
        tickers = ["NVDA", "TSLA", "BTC-USD", "ETH-USD"]
        ticker = random.choice(tickers)
        try:
            price = float(yf.download(ticker, period="1d", progress=False)['Close'].iloc[-1])
            qty = 1   # Small safe size for paper
            
            order = MarketOrderRequest(
                symbol=ticker.replace("-USD", ""),
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            trade_client.submit_order(order)
            st.success(f"🤖 Auto Bought 1 {ticker}")
        except:
            pass

auto_trade()

st.info("The bot attempts a trade every ~20-30 seconds. Check your Alpaca dashboard to see executed orders.")

time.sleep(20)
st.rerun()
