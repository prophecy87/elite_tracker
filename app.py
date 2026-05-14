import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta
import time
import random
import json
import os
import smtplib
from email.message import EmailMessage
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# ====================== PAGE SETUP ======================
st.set_page_config(page_title="EliteForge v24", layout="wide")
st.title("🔥 EliteForge • 100 to 1M")
status_placeholder = st.empty()
status_placeholder.info("System Initializing...")

# ====================== ALPACA ======================
@st.cache_resource
def connect_alpaca():
    try:
        return TradingClient(
            st.secrets["alpaca"]["api_key"],
            st.secrets["alpaca"]["secret_key"],
            paper=True
        )
    except:
        return None

trade_client = connect_alpaca()
if not trade_client:
    st.error("Missing Alpaca Secrets.")
    st.stop()

# ====================== EMAIL ALERT ======================
def send_goal_alert(current_pnl):
    try:
        msg = EmailMessage()
        msg.set_content(f"EliteForge hit the daily goal! P/L: ${current_pnl:,.2f}. Bot is now paused.")
        msg['Subject'] = "🎯 Daily Profit Goal Reached!"
        
        sender_email = st.secrets["email"]["address"]
        app_password = st.secrets["email"]["app_password"]
        
        msg['From'] = sender_email
        msg['To'] = sender_email
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        st.sidebar.success("✅ Goal alert sent!")
    except Exception as e:
        st.sidebar.error(f"Email Failed: {e}")

# ====================== STRATEGY SELECTOR ======================
strategy = st.selectbox(
    "🎛️ Select Trading Strategy",
    ["Aggressive", "Neutral", "Safe", "Pause"],
    index=0
)

if strategy == "Aggressive":
    trade_freq = 0.78
    risk_per_trade = 0.22
    st.success("🚀 AGGRESSIVE MODE")
elif strategy == "Neutral":
    trade_freq = 0.45
    risk_per_trade = 0.12
    st.info("⚖️ NEUTRAL MODE")
elif strategy == "Safe":
    trade_freq = 0.25
    risk_per_trade = 0.07
    st.warning("🛡️ SAFE MODE")
else:
    trade_freq = 0.0
    st.error("⏸️ BOT PAUSED")

# ====================== FORECASTER ======================
def get_forecaster_data(watchlist):
    forecasts = []
    for t in watchlist:
        try:
            yf_ticker = t.replace("/", "-")
            df = yf.download(yf_ticker, period="5d", interval="60m", progress=False)
            if df.empty: continue
            current_price = float(df['Close'].iloc[-1])
            ma = float(df['Close'].rolling(20).mean().iloc[-1])
            diff = (current_price - ma) / ma
            sentiment_score = random.randint(65, 95)
            
            if diff < -0.02:
                bias = "🔥 STRONGLY BULLISH"
                signal = "BUY"
                proj_price = current_price * 1.06
            elif diff > 0.02:
                bias = "🧊 STRONGLY BEARISH"
                signal = "SELL"
                proj_price = current_price * 0.95
            else:
                bias = "⚖️ NEUTRAL"
                signal = "HOLD"
                proj_price = current_price
                
            forecasts.append({
                "Ticker": t,
                "Current Price": f"${current_price:,.2f}",
                "Market Bias": bias,
                "Target": f"${proj_price:,.2f}",
                "Confidence": f"{sentiment_score}%",
                "Action": signal
            })
        except:
            continue
    return forecasts

# ====================== TRADE CYCLE ======================
def run_trade_cycle():
    tickers = ["BTC/USD", "ETH/USD", "SOL/USD", "NVDA", "TSLA"]
    t = random.choice(tickers)
    status_placeholder.write(f"🔍 Analyzing {t}...")
    try:
        yf_ticker = t.replace("/", "-")
        df = yf.download(yf_ticker, period="1d", interval="1m", progress=False)
        if not df.empty:
            price = float(df['Close'].iloc[-1])
            
            acc = trade_client.get_account()
            buying_power = float(acc.non_marginable_buying_power)
            qty = (buying_power * risk_per_trade) / price
            
            symbol = t.replace("/", "") if "/" not in t else t
            qty = int(qty) if "/" not in t else round(qty, 4)
            
            if qty > 0:
                order = MarketOrderRequest(symbol=symbol, qty=qty, side=OrderSide.BUY, time_in_force=TimeInForce.GTC)
                trade_client.submit_order(order)
                if 'trades' not in st.session_state:
                    st.session_state.trades = []
                st.session_state.trades.append({
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Asset": symbol,
                    "Price": f"${price:,.2f}",
                    "Size": qty,
                    "Strategy": strategy
                })
                return True
    except Exception as e:
        st.sidebar.error(f"Trade Error: {e}")
    return False

# ====================== SESSION STATE ======================
if 'trades' not in st.session_state: 
    st.session_state.trades = []
if 'bot_active' not in st.session_state: 
    st.session_state.bot_active = True
if 'daily_pnl' not in st.session_state: 
    st.session_state.daily_pnl = 0.0
if 'goal_reached_notified' not in st.session_state: 
    st.session_state.goal_reached_notified = False

# ====================== DASHBOARD ======================
tab1, tab2, tab3 = st.tabs(["🏛️ Live Terminal", "🔭 Strategy Forecaster", "📜 Full Ledger"])

with tab1:
    cp1, cp2, cp3 = st.columns([1, 1, 2])
    
    if cp1.button("🛑 STOP BOT" if st.session_state.bot_active else "▶️ START BOT", use_container_width=True):
        st.session_state.bot_active = not st.session_state.bot_active
        st.rerun()
    
    try:
        acc = trade_client.get_account()
        st.session_state.daily_pnl = float(acc.equity) - float(acc.last_equity)
        cp2.metric("Daily PnL", f"${st.session_state.daily_pnl:,.2f}")
        
        pnl_goal = 1000.0
        progress = min(max(st.session_state.daily_pnl / pnl_goal, 0.0), 1.0)
        cp3.write(f"Goal Progress: ${st.session_state.daily_p
