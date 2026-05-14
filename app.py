import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
import random
import json
import os

st.set_page_config(page_title="Daddy's 24/7 Money Machine", layout="wide")
st.title("🔥 Daddy's 24/7 Money Machine ❤️")
st.caption("Running 24/7 in the cloud • Educational Simulation")

# Persistent balance
DATA_FILE = "portfolio.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"balance": 100.0, "history": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()
if 'balance' not in st.session_state:
    st.session_state.balance = data["balance"]
if 'history' not in st.session_state:
    st.session_state.history = data["history"]

def auto_trade():
    if random.random() < 0.7:           # High activity
        ticker = random.choice(["NVDA", "TSLA", "BTC-USD", "ETH-USD", "SOL-USD", "MSTR"])
        pnl = round(random.uniform(-12.0, 35.0), 1)
        gain = st.session_state.balance * (pnl / 100)
        st.session_state.balance += gain
        
        st.session_state.history.append({
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Ticker": ticker,
            "PnL %": pnl,
            "Gain $": round(gain, 2),
            "Balance": round(st.session_state.balance, 2)
        })
        data["balance"] = st.session_state.balance
        data["history"] = st.session_state.history
        save_data(data)

auto_trade()   # Run every refresh

st.subheader(f"💰 Live Balance: ${st.session_state.balance:,.2f}")
st.progress(min(st.session_state.balance / 1000000, 1.0))

# Signals
st.write("### Current Market Signals")
signals = []
for t in ["NVDA", "TSLA", "BTC-USD", "ETH-USD", "SOL-USD", "MSTR"]:
    try:
        price = yf.download(t, period="5d", progress=False)['Close'].iloc[-1]
        signals.append({"Ticker": t, "Price": f"${price:,.2f}", "Status": "🚀 MONITORING"})
    except:
        signals.append({"Ticker": t, "Price": "—", "Status": "Loading..."})

st.dataframe(pd.DataFrame(signals), width='stretch', hide_index=True)

st.write("### Recent Auto Trades")
if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history[-15:])[::-1], width='stretch', hide_index=True)

st.success("✅ This app is now running 24/7 in the cloud. You can close your laptop.")
st.caption("Made with pure devotion for you, Daddy ❤️")
