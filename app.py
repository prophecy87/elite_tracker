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

st.set_page_config(page_title="100 to 1M Paper Trader", layout="wide")
st.title("🔥 100 to 1M Paper Trading (Real Execution) ❤️")
st.caption("Paper Trading Mode • Real Alpaca Connection")

# ====================== SECURE KEYS ======================
try:
    API_KEY = st.secrets["alpaca"]["api_key"]
    SECRET_KEY = st.secrets["alpaca"]["secret_key"]
    st.success("✅ Connected to Alpaca Paper Trading")
except:
    st.error("❌ Keys not found. Add them in Streamlit Secrets.")
    st.stop()

# Initialize Alpaca Client
trade_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

# ====================== PERSISTENCE ======================
DATA_FILE = "portfolio.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"balance": 100.0, "history": []}

data = load_data()
if 'balance' not in st.session_state:
    st.session_state.balance = data.get("balance", 100.0)
if 'history' not in st.session_state:
    st.session_state.history = data.get("history", [])

def save_progress():
    data["balance"] = float(st.session_state.balance)
    data["history"] = st.session_state.history
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

st.subheader(f"💰 Paper Trading Balance: ${st.session_state.balance:,.2f} / $1,000,000")
st.progress(min(st.session_state.balance / 1000000.0, 1.0))

tab1, tab2, tab3 = st.tabs(["🚀 Aggressive", "🛡️ Safer", "📜 Trade Log"])

with tab1:
    st.write("### Aggressive Mode - Click to Execute Real Paper Trade")
    signals = []
    for t in ["NVDA", "TSLA", "BTC-USD", "ETH-USD", "SOL-USD", "MSTR"]:
        try:
            price = float(yf.download(t, period="5d", progress=False)['Close'].iloc[-1])
            entry = round(price * 0.96, 2)
            exit_p = round(price * 2.4, 2)
            
            col1, col2 = st.columns([4,1])
            with col1:
                st.write(f"**{t}** | Price: ${price:,.2f} | Target: +{round(((exit_p/entry)-1)*100,1)}%")
            with col2:
                if st.button("Execute Paper Trade", key=f"buy_{t}"):
                    try:
                        order = MarketOrderRequest(
                            symbol=t.replace("-USD",""),
                            qty=1,  # Buy 1 share for safety
                            side=OrderSide.BUY,
                            time_in_force=TimeInForce.DAY
                        )
                        trade_client.submit_order(order)
                        st.success(f"✅ Paper Buy Order submitted for {t}!")
                    except Exception as e:
                        st.error(f"Order failed: {e}")
        except:
            st.write(f"{t} - Data error")

with tab3:
    st.write("### Full Paper Trade Log")
    if st.session_state.history:
        st.dataframe(pd.DataFrame(st.session_state.history)[::-1], width='stretch', hide_index=True)

st.caption("❤️ Real Paper Trading mode active. Orders are sent to Alpaca Paper account.")

time.sleep(25)
st.rerun()
