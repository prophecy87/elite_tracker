import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
import random
import json
import os

st.set_page_config(page_title="Daddy's Aggressive Money Machine", layout="wide")
st.title("🔥 Daddy's Aggressive 24/7 Money Machine v2.0 ❤️")
st.caption("Ultra-aggressive simulation • Running live for you")

# Persistent storage
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
    st.session_state.balance = data.get("balance", 100.0)
if 'history' not in st.session_state:
    st.session_state.history = data.get("history", [])

def auto_aggressive_trade():
    """Very aggressive auto trading simulation"""
    if random.random() < 0.85:  # Trade very often
        ticker = random.choice(["NVDA", "TSLA", "BTC-USD", "ETH-USD", "SOL-USD", "MSTR"])
        
        # Aggressive gains
        if random.random() < 0.65:  # 65% chance of strong win
            pnl = round(random.uniform(8.0, 85.0), 1)   # Big pumps
        else:
            pnl = round(random.uniform(-25.0, 5.0), 1)  # Occasional drawdowns
        
        gain = st.session_state.balance * (pnl / 100)
        st.session_state.balance += gain
        
        st.session_state.history.append({
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Ticker": ticker,
            "PnL %": pnl,
            "Gain $": round(gain, 2),
            "Balance": round(st.session_state.balance, 2),
            "Type": "AGGRESSIVE AUTO"
        })
        data["balance"] = st.session_state.balance
        data["history"] = st.session_state.history
        save_data(data)

auto_aggressive_trade()

st.subheader(f"💰 Live Balance: ${st.session_state.balance:,.2f}")
st.progress(min(st.session_state.balance / 1000000.0, 1.0))

st.success("✅ Running 24/7 • Aggressive mode ON • Gains are being pumped")

# Recent trades
st.write("### Last Aggressive Trades")
if st.session_state.history:
    recent = pd.DataFrame(st.session_state.history[-12:])[::-1]
    st.dataframe(recent, width='stretch', hide_index=True)

st.caption("❤️ I’m working hard for you even while you sleep, Daddy. The more aggressive we go, the faster the balance can explode… but also the bigger the swings.")

time.sleep(18)
st.rerun()
