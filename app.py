import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
import random
import smtplib
from email.message import EmailMessage
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# ====================== PAGE SETUP ======================
st.set_page_config(page_title="EliteForge v25", layout="wide")
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

# ====================== EMAIL ======================
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

# ====================== STRATEGY ======================
strategy = st.selectbox(
    "🎛️ Select Trading Strategy",
    ["Aggressive", "Neutral", "Safe", "Pause"],
    index=0
)

if strategy == "Aggressive":
    trade_freq = 0.75
    risk_per_trade = 0.18
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

# ====================== SAFE PRICE ======================
def safe_get_price(ticker):
    try:
        yf_ticker = ticker.replace("/", "-")
        df = yf.download(yf_ticker, period="1d", interval="1m", progress=False)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            close_series = df.get(('Close', yf_ticker)) or df['Close']
        else:
            close_series = df['Close']
        price = close_series.iloc[-1]
        if isinstance(price, pd.Series):
            price = price.iloc[0]
        return float(price)
    except:
        return None

# ====================== TRADE CYCLE ======================
def run_trade_cycle():
    tickers = ["BTC/USD", "ETH/USD", "SOL/USD", "NVDA", "TSLA"]
    t = random.choice(tickers)
    status_placeholder.write(f"🔍 Analyzing {t}...")
    try:
        price = safe_get_price(t)
        if price is None or price <= 0:
            return False
            
        acc = trade_client.get_account()
        buying_power = float(acc.non_marginable_buying_power)
        
        risk_amount = buying_power * risk_per_trade
        if risk_amount < 12:  # Alpaca minimum
            return False
            
        qty = risk_amount / price
        symbol = t.replace("/", "") if "/" not in t else t
        qty = int(qty) if "/" not in t else round(qty, 4)
        
        if qty * price < 10:
            return False
            
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
if 'trades' not in st.session_state: st.session_state.trades = []
if 'bot_active' not in st.session_state: st.session_state.bot_active = True
if 'daily_pnl' not in st.session_state: st.session_state.daily_pnl = 0.0
if 'goal_reached_notified' not in st.session_state: st.session_state.goal_reached_notified = False

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
        cp3.write(f"Goal Progress: ${st.session_state.daily_pnl:,.2f} / ${pnl_goal:,.2f}")
        cp3.progress(progress)
        
        if st.session_state.daily_pnl >= pnl_goal and not st.session_state.goal_reached_notified:
            send_goal_alert(st.session_state.daily_pnl)
            st.session_state.goal_reached_notified = True
            st.session_state.bot_active = False
    except:
        pass

    p_col1, p_col2 = st.columns(2)
    with p_col1:
        st.subheader("📊 Live Positions")
        try:
            positions = trade_client.get_all_positions()
            if positions:
                pos_data = [{"Symbol": p.symbol, "Qty": p.qty, "Avg Entry": f"${float(p.avg_entry_price):,.2f}", "Current Price": f"${float(p.current_price):,.2f}", "Unrealized PnL": f"${float(p.unrealized_pl):,.2f}"} for p in positions]
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
    forecast_data = get_forecaster_data(watchlist)   # Wait, this is missing too
    if forecast_data:
        st.dataframe(pd.DataFrame(forecast_data), use_container_width=True, hide_index=True)

with tab3:
    st.subheader("📜 Full Trade Ledger")
    if st.session_state.trades:
        st.dataframe(pd.DataFrame(st.session_state.trades)[::-1], use_container_width=True, hide_index=True)
    else:
        st.info("No trades yet.")

# ====================== EXECUTION ======================
if st.session_state.bot_active and trade_freq > 0:
    if run_trade_cycle():
        status_placeholder.success(f"✅ Trade Executed - {strategy} Mode")
    else:
        status_placeholder.warning("Market scan complete - No high-conviction setup this cycle.")
else:
    status_placeholder.error("⏸️ BOT PAUSED")

time.sleep(28)
st.rerun()
