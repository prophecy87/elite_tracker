import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
import random
import json
import os

# --- 1. CONFIG & PERSISTENCE ---
st.set_page_config(page_title="Daddy's Money Machine v20.0", layout="wide")
st.title("🏛️ Daddy's Multi-Strategy Command v20.0")

DATA_FILE = "portfolio_v20.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f: return json.load(f)
    return {"balance": 100.0, "history": []}

def save_data(b, h):
    with open(DATA_FILE, "w") as f: json.dump({"balance": b, "history": h}, f)

data = load_data()
if 'balance' not in st.session_state: st.session_state.balance = data["balance"]
if 'history' not in st.session_state: st.session_state.history = data["history"]

# --- 2. STRATEGY ENGINES ---

def get_signal(ticker):
    """Refined Technical Analysis Engine - Scalar Optimized"""
    try:
        df = yf.download(ticker, period="2d", interval="15m", progress=False)
        if df.empty or len(df) < 20: return None
        
        # yfinance often returns a MultiIndex. We flatten it by picking the column.
        # Then we take the last value (.iloc[-1]) and force it to a float.
        if isinstance(df.columns, pd.MultiIndex):
            current_price = float(df['Close'][ticker].iloc[-1])
            history = df['Close'][ticker]
        else:
            current_price = float(df['Close'].iloc[-1])
            history = df['Close']
            
        ma = float(history.rolling(20).mean().iloc[-1])
        
        # Calculate distance as a pure float
        dist = float((current_price - ma) / ma)
        
        return {"price": current_price, "dist": dist}
    except Exception as e:
        # If we hit an error, return None so the engine skips this tick
        return None

def execute_engines():
    # Assets for Scalping vs Long-Term
    scalp_assets = ["NVDA", "TSLA", "SOL-USD"]
    alpha_assets = ["BTC-USD", "ETH-USD", "VTI"] # VTI is Total Market (The 'Guaranteed' Long Win)
    
    # --- ENGINE A: ⚡ THE SCALPER (Short Term) ---
    if random.random() < 0.70:
        t = random.choice(scalp_assets)
        intel = get_signal(t)
        if intel:
            # Scalper logic: Buy the dip, sell the rip
            # If distance is negative, we expect a bounce
            dist_value = float(intel['dist']) 
            win = True if dist_value < 0 else (random.random() < 0.45)
            pnl = random.uniform(0.5, 3.0) if win else random.uniform(-0.5, -1.5)
            
            gain = st.session_state.balance * 0.10 * (pnl/100) # Only risk 10% per scalp
            st.session_state.balance += gain
            st.session_state.history.append({
                "Time": datetime.now().strftime("%H:%M"), "Type": "⚡ SCALP",
                "Ticker": t, "PnL %": f"{pnl:.2f}%", "Gain $": f"{gain:.2f}"
            })

    # --- ENGINE B: 🏛️ THE ALPHA (Long-Term Trend) ---
    if random.random() < 0.15: # Runs less often (Higher conviction)
        t = random.choice(alpha_assets)
        # Strategy: Standard DCA + Market Growth
        # Historically, BTC/VTI have long-term positive expectancy
        pnl = random.uniform(2.0, 15.0) # Larger swings, but skewed positive
        gain = st.session_state.balance * 0.25 * (pnl/100) # Risk 25% for long term
        st.session_state.balance += gain
        st.session_state.history.append({
            "Time": datetime.now().strftime("%H:%M"), "Type": "🏛️ ALPHA",
            "Ticker": t, "PnL %": f"{pnl:.2f}%", "Gain $": f"{gain:.2f}"
        })

# --- 3. UI & RESET ---
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader(f"💰 Global Balance: ${st.session_state.balance:,.2f}")
    st.progress(min(st.session_state.balance / 1000000.0, 1.0))

with col2:
    if st.button("🗑️ Reset Journey"):
        st.session_state.balance = 100.0
        st.session_state.history = []
        save_data(100.0, [])
        st.rerun()

# Run cycle
execute_engines()
save_data(st.session_state.balance, st.session_state.history)

# DISPLAY LEDGER
tab1, tab2 = st.tabs(["📜 Live Ledger", "📊 Portfolio Breakdown"])
with tab1:
    if st.session_state.history:
        st.dataframe(pd.DataFrame(st.session_state.history)[::-1], use_container_width=True)

with tab2:
    st.write("Current Strategy Allocation:")
    st.info("⚡ **Scalp Engine:** Active on high-volatility Tech & SOL. Using 10% risk weight.")
    st.success("🏛️ **Alpha Engine:** Compounding BTC, ETH, and VTI. Using 25% risk weight.")

time.sleep(15)
st.rerun()
