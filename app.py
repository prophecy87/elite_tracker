import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
import pandas_ta as ta  # For high-accuracy technical indicators
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass

# ====================== PAGE SETUP ======================
st.set_page_config(page_title="EliteForge v26 Apex", layout="wide", page_icon="💎")
st.title("💎 EliteForge v26 • Apex Predator")
status_placeholder = st.empty()

# ====================== CORE CONNECTION ======================
@st.cache_resource
def connect_alpaca():
    try:
        return TradingClient(st.secrets["alpaca"]["api_key"], st.secrets["alpaca"]["secret_key"], paper=True)
    except: return None

trade_client = connect_alpaca()
if not trade_client:
    st.error("Critial Failure: Alpaca Credentials Missing.")
    st.stop()

# ====================== SCALPING ALGORITHM (The Apex Engine) ======================
def apex_analysis(ticker):
    """
    Combines RSI, EMA, and Volatility Scalping.
    High Success Rate Logic: 
    - BUY if Price < Lower Band & RSI < 30 (Oversold Scalp)
    - SELL if Price > Upper Band & RSI > 70 (Overbought Scalp)
    """
    try:
        yf_ticker = ticker.replace("/", "-")
        # Scalping needs 1m or 5m data
        df = yf.download(yf_ticker, period="1d", interval="5m", progress=False)
        if df.empty: return None
        
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        # Technical Indicators
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        bbands = ta.bbands(df['Close'], length=20, std=2)
        df = pd.concat([df, bbands], axis=1)

        current_price = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])
        lower_band = float(df['BBL_20_2.0'].iloc[-1])
        upper_band = float(df['BBU_20_2.0'].iloc[-1])
        
        # Logic Gate
        if current_price <= lower_band and rsi < 35:
            return {"side": OrderSide.BUY, "price": current_price, "reason": "Oversold Scalp"}
        elif current_price >= upper_band and rsi > 65:
            return {"side": OrderSide.SELL, "price": current_price, "reason": "Overbought Scalp"}
        
        return {"side": None, "price": current_price, "reason": "Waiting for Setup"}
    except: return None

# ====================== EXECUTION (Bracket Orders) ======================
def execute_apex_trade(ticker, signal, conf):
    try:
        symbol = ticker.replace("/", "")
        acc = trade_client.get_account()
        
        # Aggressive Position Sizing
        cash = float(acc.buying_power)
        qty = (cash * conf['risk']) / signal['price']
        qty = round(qty, 4) if "/" in ticker else int(qty)
        
        if qty <= 0: return False

        # Profit/Loss Ratios
        tp_mult = 1.02 if signal['side'] == OrderSide.BUY else 0.98
        sl_mult = 0.99 if signal['side'] == OrderSide.BUY else 1.01

        # BRACKET ORDER: Entry + TP + SL in one shot
        order_req = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=signal['side'],
            time_in_force=TimeInForce.GTC,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=round(signal['price'] * tp_mult, 2)),
            stop_loss=StopLossRequest(stop_price=round(signal['price'] * sl_mult, 2))
        )
        
        trade_client.submit_order(order_req)
        return True
    except Exception as e:
        st.sidebar.error(f"Apex Execution Error: {e}")
        return False

# ====================== INTERFACE & CONTROL ======================
with st.sidebar:
    st.header("🎮 Bot Controls")
    strategy_mode = st.radio("Strategy Profile", ["Aggressive", "Neutral", "Safe", "Pause"])
    
    profiles = {
        "Aggressive": {"risk": 0.25, "refresh": 15},
        "Neutral": {"risk": 0.12, "refresh": 30},
        "Safe": {"risk": 0.05, "refresh": 60},
        "Pause": {"risk": 0.0, "refresh": 300}
    }
    conf = profiles[strategy_mode]

# ====================== DASHBOARD TABS ======================
tab_live, tab_signals, tab_ledger = st.tabs(["⚡ Live Scalper", "🎯 Apex Signals", "📜 Ledger"])

with tab_live:
    # Top Stats
    try:
        acc = trade_client.get_account()
        c1, c2, c3 = st.columns(3)
        c1.metric("Live Equity", f"${float(acc.equity):,.2f}")
        c2.metric("Buying Power", f"${float(acc.buying_power):,.2f}")
        day_pnl = float(acc.equity) - float(acc.last_equity)
        c3.metric("Daily Return", f"${day_pnl:,.2f}", f"{(day_pnl/float(acc.last_equity))*100:.2f}%")
    except: st.warning("Connecting to exchange...")

    # Active Positions
    st.subheader("💼 Active Positions")
    positions = trade_client.get_all_positions()
    if positions:
        pos_df = pd.DataFrame([{
            "Asset": p.symbol,
            "Qty": p.qty,
            "Entry": p.avg_entry_price,
            "PnL": f"${float(p.unrealized_pl):,.2f}",
            "PnL %": f"{float(p.unrealized_plpc)*100:.2f}%"
        } for p in positions])
        st.dataframe(pos_df, use_container_width=True)
    else: st.info("No active trades. Scanning for Apex setups...")

with tab_signals:
    watchlist = ["BTC/USD", "ETH/USD", "SOL/USD", "NVDA", "TSLA", "AMD", "MSTR"]
    cols = st.columns(len(watchlist))
    
    for i, ticker in enumerate(watchlist):
        with cols[i]:
            signal = apex_analysis(ticker)
            if signal:
                st.metric(ticker, f"${signal['price']:,.2f}")
                if signal['side']:
                    st.success(f"SIGNAL: {signal['side'].name}")
                    st.caption(signal['reason'])
                    # Auto-trade if not paused
                    if strategy_mode != "Pause":
                        if execute_apex_trade(ticker, signal, conf):
                            st.toast(f"Apex Trade Sent: {ticker}")
                else:
                    st.info("NO SIGNAL")

with tab_ledger:
    st.subheader("📜 Recent Orders")
    orders = trade_client.get_orders()
    if orders:
        st.dataframe(pd.DataFrame([{
            "Time": o.created_at.strftime("%H:%M"),
            "Asset": o.symbol,
            "Side": o.side.name,
            "Status": o.status.name
        } for o in orders]), use_container_width=True)

# ====================== AUTO-REFRESH ======================
status_placeholder.write(f"Apex System Pulse: {datetime.now().strftime('%H:%M:%S')}")
time.sleep(conf['refresh'])
st.rerun()
