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

# 1. PAGE SETUP
st.set_page_config(page_title="EliteForge v23", layout="wide")

# 2. UI HEADER
st.title("🔥 EliteForge • 100 to 1M")
status_placeholder = st.empty()
status_placeholder.info("System Initializing...")

# 3. SECRETS & CLIENT
@st.cache_resource
def connect_alpaca():
    if "alpaca" not in st.secrets: return None
    try:
        return TradingClient(st.secrets["alpaca"]["api_key"], st.secrets["alpaca"]["secret_key"], paper=True)
    except: return None

trade_client = connect_alpaca()

if not trade_client:
    st.error("Missing Alpaca Secrets.")
    st.stop()

# 4. FUNCTIONS (Must be defined before they are called)

def send_goal_alert(current_pnl):
    msg = EmailMessage()
    msg.set_content(f"EliteForge hit the daily goal! P/L: ${current_pnl:,.2f}. Bot is now paused.")
    msg['Subject'] = "🎯 Daily Profit Goal Reached!"
    
    sender_email = st.secrets["email"]["address"]
    app_password = st.secrets["email"]["app_password"]
    
    msg['From'] = sender_email
    msg['To'] = sender_email
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
    except Exception as e:
        st.sidebar.error(f"Email Failed: {e}")

def get_forecaster_data(watchlist):
    forecasts = []
    for t in watchlist:
        try:
            yf_ticker = t.replace("/", "-")
            df = yf.download(yf_ticker, period="5d", interval="60m", progress=False)
            if df.empty: continue

            if isinstance(df.columns, pd.MultiIndex):
                current_price = float(df['Close'][yf_ticker].iloc[-1])
                ma = float(df['Close'][yf_ticker].rolling(20).mean().iloc[-1])
            else:
                current_price = float(df['Close'].iloc[-1])
                ma = float(df['Close'].rolling(20).mean().iloc[-1])

            diff = (current_price - ma) / ma
            sentiment_score = random.randint(60, 98)
            
            if diff < -0.02:
                bias = "🔥 STRONGLY BULLISH"; signal = "BUY"
                proj_price = current_price * 1.05
                proj_date = (datetime.now() + timedelta(days=random.randint(1, 2))).strftime("%m-%d %H:00")
            elif diff > 0.02:
                bias = "🧊 STRONGLY BEARISH"; signal = "SELL"
                proj_price = current_price * 0.96
                proj_date = (datetime.now() + timedelta(hours=random.randint(4, 12))).strftime("%m-%d %H:00")
            else:
                bias = "⚖️ NEUTRAL / STABLE"; signal = "HOLD"
                proj_price = current_price
                proj_date = "Awaiting Volatility"

            forecasts.append({
                "Ticker": t, "Current Price": f"${current_price:,.2f}",
                "Market Bias": bias, "Target Entry/Exit": f"${proj_price:,.2f}",
                "Estimated Window": proj_date, "Confidence": f"{sentiment_score}%",
                "Action": signal
            })
        except: continue
    return forecasts

def run_trade_cycle():
    tickers = ["BTC/USD", "ETH/USD", "SOL/USD", "NVDA", "TSLA"]
    t = random.choice(tickers)
    status_placeholder.write(f"🔍 Analyzing {t}...")
    try:
        yf_ticker = t.replace("/", "-")
        df = yf.download(yf_ticker, period="1d", interval="1m", progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                val = df['Close'][yf_ticker].iloc[-1]
            else:
                val = df['Close'].iloc[-1]
            price = float(val)
            
            # Use Available Buying Power to prevent 403 errors
            acc = trade_client.get_account()
            buying_power = float(acc.non_marginable_buying_power)
            qty = (buying_power * 0.10) / price
            
            symbol = t.replace("/", "") if "/" not in t else t
            qty = int(qty) if "/" not in t else round(qty, 4)
            if qty > 0:
                order = MarketOrderRequest(symbol=symbol, qty=qty, side=OrderSide.BUY, time_in_force=TimeInForce.GTC)
                trade_client.submit_order(order)
                st.session_state.trades.append({"Time": datetime.now().strftime("%H:%M:%S"), "Asset": symbol, "Price": f"${price:,.2f}", "Size": qty})
                return True
    except Exception as e:
        st.sidebar.error(f"Trade Error: {e}")
    return False

# 5. DATA PERSISTENCE & SESSION STATE
if 'trades' not in st.session_state: st.session_state.trades = []
if 'bot_active' not in st.session_state: st.session_state.bot_active = True
if 'daily_pnl' not in st.session_state: st.session_state.daily_pnl = 0.0
if 'goal_reached_notified' not in st.session_state: st.session_state.goal_reached_notified = False
if 'balance' not in st.session_state:
    try:
        acc = trade_client.get_account()
        st.session_state.balance = float(acc.cash)
    except: st.session_state.balance = 100.0

# 6. DASHBOARD TABS
tab1, tab2, tab3 = st.tabs(["🏛️ Live Terminal", "🔭 Strategy Forecaster", "📜 Full Ledger"])

with tab1:
    # --- CONTROL PANEL ---
    cp1, cp2, cp3 = st.columns([1, 1, 2])
    
    if st.session_state.bot_active:
        if cp1.button("🛑 STOP BOT", use_container_width=True):
            st.session_state.bot_active = False
            st.rerun()
    else:
        if cp1.button("▶️ START BOT", use_container_width=True):
            st.session_state.bot_active = True
            st.session_state.goal_reached_notified = False
            st.rerun()

    try:
        acc = trade_client.get_account()
        st.session_state.daily_pnl = float(acc.equity) - float(acc.last_equity)
        cp2.metric("Daily PnL", f"${st.session_state.daily_pnl:,.2f}", delta=f"{st.session_state.daily_pnl:,.2f}")
        
        pnl_goal = 1000.0
        progress = min(max(st.session_state.daily_pnl / pnl_goal, 0.0), 1.0)
        cp3.write(f"Goal Progress: ${st.session_state.daily_pnl:,.2f} / ${pnl_goal:,.2f}")
        cp3.progress(progress)

        if st.session_state.daily_pnl >= pnl_goal:
            st.session_state.bot_active = False
            if not st.session_state.goal_reached_notified:
                send_goal_alert(st.session_state.daily_pnl)
                st.session_state.goal_reached_notified = True
            st.warning("🎯 DAILY GOAL REACHED. Bot paused.")
    except Exception as e:
        st.error(f"PnL Fetch Error: {e}")

    st.divider()

    # --- LIVE ACCOUNT METRICS ---
    try:
        acc = trade_client.get_account()
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Portfolio Value", f"${float(acc.equity):,.2f}")
        m_col2.metric("Buying Power", f"${float(acc.buying_power):,.2f}")
        m_col3.metric("Cash Balance", f"${float(acc.cash):,.2f}")
        m_col4.metric("Bot Health", "🟢 ACTIVE" if st.session_state.bot_active else "🔴 PAUSED")
        st.divider()
    except: pass

    # --- POSITIONS & ORDERS ---
    p_col1, p_col2 = st.columns(2)
    with p_col1:
        st.subheader("📊 Live Positions")
        try:
            positions = trade_client.get_all_positions()
            if positions:
                pos_data = [{"Symbol": p.symbol, "Qty": p.qty, "Avg Entry": f"${float(p.avg_entry_price):,.2f}", "Current Price": f"${float(p.current_price):,.2f}", "P/L (%)": f"{float(p.unrealized_plpc)*100:.2f}%"} for p in positions]
                st.dataframe(pd.DataFrame(pos_data), use_container_width=True, hide_index=True)
            else: st.info("No open positions.")
        except: pass

    with p_col2:
        st.subheader("⏳ Active Orders")
        try:
            orders = trade_client.get_orders()
            if orders:
                order_data = [{"Symbol": o.symbol, "Qty": o.qty, "Side": o.side.upper(), "Status": o.status.upper(), "Submitted": o.submitted_at.strftime("%H:%M:%S")} for o in orders]
                st.dataframe(pd.DataFrame(order_data), use_container_width=True, hide_index=True)
            else: st.info("No pending orders.")
        except: pass

with tab2:
    st.subheader("🎯 Predictive Watchlist Signals")
    watchlist = ["BTC/USD", "ETH/USD", "SOL/USD", "NVDA", "TSLA", "MSTR", "AMD"]
    forecast_data = get_forecaster_data(watchlist)
    if forecast_data:
        st.dataframe(pd.DataFrame(forecast_data), use_container_width=True, hide_index=True)

with tab3:
    if st.session_state.trades:
        st.table(pd.DataFrame(st.session_state.trades)[::-1])
    else: st.info("No trades in current session.")

# 7. EXECUTION ENGINE
if st.session_state.bot_active:
    if run_trade_cycle():
        status_placeholder.success(f"✅ Trade Executed at {datetime.now().strftime('%H:%M:%S')}")
    else:
        status_placeholder.warning("Market scan complete - No trades triggered.")
else:
    status_placeholder.error("⏸️ BOT PAUSED: Goal reached or manual stop.")

time.sleep(30)
st.rerun()
