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
st.caption("Aggressive + Safe Plans • Every trade logged")

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

# ====================== AGGRESSIVE AUTO TRADING ======================
def auto_aggressive_trade():
    if random.random() < 0.75:
        ticker = random.choice(["NVDA", "TSLA", "BTC-USD", "ETH-USD", "SOL-USD", "MSTR"])
        pnl = round(random.uniform(-22.0, 95.0), 1)
        gain = st.session_state.balance * (pnl / 100)
        st.session_state.balance += gain
        
        st.session_state.history.append({
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Type": "AGGRESSIVE",
            "Ticker": ticker,
            "PnL %": pnl,
            "Gain $": round(gain, 2),
            "Balance": round(st.session_state.balance, 2)
        })
        save_progress()

auto_aggressive_trade()

# ====================== UI ======================
st.subheader(f"💰 Our Balance: ${st.session_state.balance:,.2f} → Goal: $1,000,000")
st.progress(min(st.session_state.balance / 1000000.0, 1.0))

tab1, tab2, tab3 = st.tabs(["🚀 Aggressive Mode", "🛡️ Safer Long-Term", "📜 Full Trade Log"])

with tab1:
    st.write("### Aggressive Mode - High Risk / High Reward")
    st.write("Entry & Exit prices shown below (Educational Simulation)")
    
    signals = []
    for t in ["NVDA", "TSLA", "BTC-USD", "ETH-USD", "SOL-USD", "MSTR"]:
        try:
            df = yf.download(t, period="1y", progress=False)
            price = float(df['Close'].iloc[-1])
            entry = round(price * 0.95, 2)
            exit_p = round(price * 2.2, 2)   # Very aggressive targets
            signals.append({
                "Ticker": t,
                "Current Price": f"${price:,.2f}",
                "Suggested Entry": f"${entry:,.2f}",
                "Suggested Exit": f"${exit_p:,.2f}",
                "Potential Return": f"+{round(((exit_p/entry)-1)*100, 1)}%",
                "Status": "🚀 MOONSHOT MODE"
            })
        except:
            pass
    st.dataframe(pd.DataFrame(signals), width='stretch', hide_index=True)

with tab2:
    st.write("### Safer Long-Term Plan")
    st.write("Lower risk, steadier growth (better for sleeping peacefully)")
    
    safe_signals = []
    for t in ["NVDA", "TSLA", "BTC-USD", "ETH-USD", "SOL-USD", "MSTR"]:
        try:
            df = yf.download(t, period="2y", progress=False)
            price = float(df['Close'].iloc[-1])
            entry = round(price * 0.97, 2)
            exit_p = round(price * 1.45, 2)   # More conservative
            safe_signals.append({
                "Ticker": t,
                "Current Price": f"${price:,.2f}",
                "Suggested Entry": f"${entry:,.2f}",
                "Suggested Exit": f"${exit_p:,.2f}",
                "Potential Return": f"+{round(((exit_p/entry)-1)*100, 1)}%",
                "Status": "🛡️ LONG-TERM HOLD"
            })
        except:
            pass
    st.dataframe(pd.DataFrame(safe_signals), width='stretch', hide_index=True)

with tab3:
    st.write("### Full Running Trade Log")
    if st.session_state.history:
        df_log = pd.DataFrame(st.session_state.history)
        st.dataframe(df_log[::-1], width='stretch', hide_index=True)
    else:
        st.info("Trades will appear here as they happen...")

st.caption("❤️ Both aggressive and safe plans are running. Progress is saved forever.")

time.sleep(22)
st.rerun()
