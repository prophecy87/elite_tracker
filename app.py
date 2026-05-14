import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
import pandas_ta as ta 
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass

# ====================== PAGE SETUP ======================
st.set_page_config(page_title="EliteForge v26.1", layout="wide", page_icon="💎")
st.title("💎 EliteForge v26.1 • Apex Predator")
status_placeholder = st.empty()

# ====================== CORE CONNECTION ======================
@st.cache_resource
def connect_alpaca():
    try:
        return TradingClient(st.secrets["alpaca"]["api_key"], st.secrets["alpaca"]["secret_key"], paper=True)
    except: return None

trade_client = connect_alpaca()
if not trade_client:
    st.error("Critical Failure: Alpaca Credentials Missing.")
    st.stop()

# ====================== SCALPING ALGORITHM ======================
def apex_analysis(ticker):
    try:
        yf_ticker = ticker.replace("/", "-")
        df = yf.download(yf_ticker, period="1d", interval="5m", progress=False)
        if df.empty: return None
        
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        df['EMA_20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        bbands = ta.bbands(df['Close'], length=20, std=2)
        df = pd.concat([df, bbands], axis=1)

        current_price = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])
        # Note: pandas_ta column names vary; using standard BBL/BBU
        lower_band = float(df.filter(like='BBL').iloc[-1])
        upper_band = float(df.filter(like='BBU').iloc[-1])
        
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
        cash = float(acc.buying_power)
        qty = (cash * conf['risk']) / signal['price']
        qty = round(qty, 4) if "/" in ticker else int(qty)
        
        if qty <= 0: return False

        tp_mult = 1.02 if signal['side'] == OrderSide.BUY else 0.98
        sl_mult = 0.99 if signal['side'] == OrderSide.BUY else 1.01

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
    except: return False

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
    try:
        acc = trade_client.get_account()
        c1, c2, c3 = st.columns(3)
        c1.metric("Live Equity", f"${float(acc.equity):,.2f}")
        c2.metric("Buying Power", f"${float(acc.buying_power):,.2f}")
        day_pnl = float(acc.equity) - float(acc.last_equity)
        c3.metric("Daily Return", f"${day_pnl:,.2f}")
    except: pass

    st.subheader("💼 Active Positions")
    positions = trade_client.get_all_positions()
    if positions:
        pos_df = pd.DataFrame([{
            "Asset": p.symbol, "Qty": p.qty, "Entry": p.avg_entry_price,
            "PnL": f"${float(p.unrealized_pl):,.2f}",
            "PnL %": f"{float(p.unrealized_plpc)*100:.2f}%"
        } for p in positions])
        # FIXED: Replacing use_container_width with width='stretch'
        st.dataframe(pos_df, width='stretch')
    else: st.info("Scanning for Apex setups...")

with tab_signals:
    watchlist = ["BTC/USD", "ETH/USD", "SOL/USD", "NVDA", "TSLA", "MSTR"]
    cols = st.columns(len(watchlist))
    for i, ticker in enumerate(watchlist):
        with cols[i]:
            signal = apex_analysis(ticker)
            if signal:
                st.metric(ticker, f"${signal['price']:,.2f}")
                if signal['side']:
                    st.success(f"SIGNAL: {signal['side'].name}")
                    if strategy_mode != "Pause":
                        if execute_apex_trade(ticker, signal, conf):
                            st.toast(f"Apex Trade Sent: {ticker}")
                else: st.info("WAITING")

with tab_ledger:
    orders = trade_client.get_orders()
    if orders:
        ledger_df = pd.DataFrame([{
            "Time": o.created_at.strftime("%H:%M"), "Asset": o.symbol,
            "Side": o.side.name, "Status": o.status.name
        } for o in orders])
        # FIXED: Replacing use_container_width with width='stretch'
        st.dataframe(ledger_df, width='stretch')

# ====================== AUTO-REFRESH ======================
status_placeholder.write(f"Apex Pulse: {datetime.now().strftime('%H:%M:%S')}")
time.sleep(conf['refresh'])
st.rerun()
