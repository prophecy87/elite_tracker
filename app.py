import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
import random
import json
import os

st.set_page_config(page_title="100 to 1M Challenge", layout="wide")
st.title("🔥 100 to 1 Million Challenge ❤️")
st.caption("Real Data + Copy Trader • Keys Secured")

# ====================== SECURE KEYS (DO NOT HARD CODE) ======================
try:
    API_KEY = st.secrets["alpaca"]["api_key"]
    SECRET_KEY = st.secrets["alpaca"]["secret_key"]
    st.success("✅ Alpaca Keys Loaded Securely")
except:
    st.error("❌ No Alpaca keys found. Add them in .streamlit/secrets.toml or Streamlit Cloud Secrets")
    API_KEY = None
    SECRET_KEY = None

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

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()
if 'balance' not in st.session_state:
    st.session_state.balance = data.get("balance", 100.0)
if 'history' not in st.session_state:
    st.session_state.history = data.get("history", [])

def save_progress():
    data["balance"] = float(st.session_state.balance)
    data["history"] = st.session_state.history
    save_data(data)

# Auto trade simulation (for now - we can connect real later)
def auto_trade():
    if random.random() < 0.7:
        ticker = random.choice(["NVDA", "TSLA", "BTC-USD", "ETH-USD", "SOL-USD", "MSTR"])
        pnl = round(random.uniform(-20.0, 80.0), 1)
        gain = st.session_state.balance * (pnl / 100)
        st.session_state.balance += gain
        st.session_state.history.append({
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Type": "AUTO",
            "Ticker": ticker,
            "PnL %": pnl,
            "Gain $": round(gain, 2),
            "Balance": round(st.session_state.balance, 2)
        })
        save_progress()

auto_trade()

st.subheader(f"💰 Our Balance: ${st.session_state.balance:,.2f} / $1,000,000")
st.progress(min(st.session_state.balance / 1000000.0, 1.0))

tab1, tab2, tab3 = st.tabs(["🚀 Aggressive", "🛡️ Safer", "📜 Trade Log"])

with tab1:
    st.write("### Aggressive Mode")
    # Real data table with Entry/Exit
    signals = []
    for t in ["NVDA", "TSLA", "BTC-USD", "ETH-USD", "SOL-USD", "MSTR"]:
        try:
            price = float(yf.download(t, period="1y", progress=False)['Close'].iloc[-1])
            entry = round(price * 0.94, 2)
            exit_p = round(price * 2.5, 2)
            signals.append({
                "Ticker": t,
                "Current": f"${price:,.2f}",
                "Entry": f"${entry:,.2f}",
                "Exit": f"${exit_p:,.2f}",
                "Potential": f"+{round(((exit_p/entry)-1)*100,1)}%"
            })
        except:
            signals.append({"Ticker": t, "Current": "Data error", "Entry": "-", "Exit": "-", "Potential": "-"})
    st.dataframe(pd.DataFrame(signals), width='stretch', hide_index=True)

with tab2:
    st.write("### Safer Long-Term Plan")
    st.info("Lower risk version will go here")

with tab3:
    st.write("### Full Trade Log")
    if st.session_state.history:
        st.dataframe(pd.DataFrame(st.session_state.history)[::-1], width='stretch', hide_index=True)

st.caption("❤️ Keys are now secured using Streamlit Secrets.")
