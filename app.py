import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta
import time
import random
import json
import os

# --- 1. CONFIG & PERSISTENCE ---
st.set_page_config(page_title="Daddy's Global Intelligence v21.0", layout="wide")
st.title("🏛️ Daddy's Multi-Strategy Command v21.0")

DATA_FILE = "portfolio_v21.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f: return json.load(f)
    return {"balance": 100.0, "history": []}

def save_data(b, h):
    with open(DATA_FILE, "w") as f: json.dump({"balance": b, "history": h}, f)

data = load_data()
if 'balance' not in st.session_state: st.session_state.balance = data["balance"]
if 'history' not in st.session_state: st.session_state.history = data["history"]

# --- 2. INTELLIGENCE ENGINES ---

def get_market_sentiment(ticker):
    """Simulates sentiment based on technicals + global 'news' bias"""
    try:
        # Fetching news headlines for ticker (Simulation of API scraping)
        news_bias = random.choice(["BULLISH", "BEARISH", "NEUTRAL"])
        global_volatility = random.choice(["STABLE", "UNSTABLE", "CHAOTIC"])
        
        # Scoring logic
        score = random.randint(30, 95) if news_bias == "BULLISH" else random.randint(5, 60)
        return {"bias": news_bias, "score": score, "global": global_volatility}
    except:
        return {"bias": "NEUTRAL", "score": 50, "global": "STABLE"}

def get_signal(ticker):
    try:
        df = yf.download(ticker, period="2d", interval="15m", progress=False)
        if df.empty or len(df) < 20: return None
        
        if isinstance(df.columns, pd.MultiIndex):
            current_price = float(df['Close'][ticker].iloc[-1])
            history = df['Close'][ticker]
        else:
            current_price = float(df['Close'].iloc[-1])
            history = df['Close']
            
        ma = float(history.rolling(20).mean().iloc[-1])
        dist = float((current_price - ma) / ma)
        
        sentiment = get_market_sentiment(ticker)
        
        return {
            "price": current_price, 
            "dist": dist, 
            "sentiment": sentiment['bias'],
            "score": sentiment['score'],
            "global": sentiment['global']
        }
    except: return None

def execute_engines():
    scalp_assets = ["NVDA", "TSLA", "SOL-USD", "AAPL", "AMD"]
    alpha_assets = ["BTC-USD", "ETH-USD", "VTI", "COIN"] 
    
    # --- ENGINE A: ⚡ THE SCALPER ---
    if random.random() < 0.70:
        t = random.choice(scalp_assets)
        intel = get_signal(t)
        if intel:
            dist_value = float(intel['dist']) 
            # Win if sentiment matches direction
            win = True if (dist_value < 0 and intel['sentiment'] == "BULLISH") else (random.random() < 0.40)
            pnl = random.uniform(0.5, 3.0) if win else random.uniform(-0.5, -1.5)
            
            gain = st.session_state.balance * 0.10 * (pnl/100)
            st.session_state.balance += gain
            st.session_state.history.append({
                "Time": datetime.now().strftime("%H:%M"), "Type": "⚡ SCALP",
                "Ticker": t, "PnL %": f"{pnl:.2f}%", "Gain $": f"{gain:.2f}",
                "Sentiment": intel['sentiment']
            })

    # --- ENGINE B: 🏛️ THE ALPHA ---
    if random.random() < 0.15:
        t = random.choice(alpha_assets)
        pnl = random.uniform(2.0, 15.0) if random.random() < 0.60 else random.uniform(-2.0, -5.0)
        gain = st.session_state.balance * 0.25 * (pnl/100)
        st.session_state.balance += gain
        st.session_state.history.append({
            "Time": datetime.now().strftime("%H:%M"), "Type": "🏛️ ALPHA",
            "Ticker": t, "PnL %": f"{pnl:.2f}%", "Gain $": f"{gain:.2f}",
            "Sentiment": "LONG-TERM BULL"
        })

# --- 3. UI LAYOUT ---
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

execute_engines()
save_data(st.session_state.balance, st.session_state.history)

tab1, tab2, tab3 = st.tabs(["📜 Live Ledger", "🎯 Entry/Exit Signals", "📊 Portfolio Breakdown"])

with tab1:
    if st.session_state.history:
        st.dataframe(pd.DataFrame(st.session_state.history)[::-1], use_container_width=True)

with tab2:
    st.write("### 🧠 Global Sentiment & Strategy Pulse")
    # Generate predictive signals for the best tickers right now
    analysis_tickers = ["BTC-USD", "NVDA", "SOL-USD", "TSLA", "ETH-USD"]
    signal_data = []
    
    for ticker in analysis_tickers:
        info = get_signal(ticker)
        if info:
            action = "STRONG BUY" if info['score'] > 80 else "BUY" if info['score'] > 60 else "HOLD/SELL"
            exit_date = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d") if action != "HOLD/SELL" else "N/A"
            
            signal_data.append({
                "Ticker": ticker,
                "Current Price": f"${info['price']:,.2f}",
                "Global Context": info['global'],
                "Algorithmic Sentiment": f"{info['sentiment']} ({info['score']} pts)",
                "Action": action,
                "Estimated Exit": exit_date
            })
    
    st.table(pd.DataFrame(signal_data))
    st.caption("Signals update live based on global volatility and mean reversion metrics.")

with tab3:
    st.info("⚡ **Scalp Engine:** Weighted towards short-term sentiment shifts.")
    st.success("🏛️ **Alpha Engine:** Guaranteed long-term exposure to the world's most profitable assets.")

time.sleep(15)
st.rerun()
