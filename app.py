import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass

# ====================== PAGE SETUP ======================
st.set_page_config(page_title="EliteForge v24.2", layout="wide")
st.title("🔥 EliteForge • Hybrid Engine")
status_placeholder = st.empty()

# ====================== ALPACA CONNECT ======================
@st.cache_resource
def connect_alpaca():
    try:
        return TradingClient(
            st.secrets["alpaca"]["api_key"],
            st.secrets["alpaca"]["secret_key"],
            paper=True
        )
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

trade_client = connect_alpaca()

# ====================== HYBRID SETTINGS ======================
strategy = st.sidebar.selectbox("🎛️ Strategy Mode", ["Safe", "Neutral", "Aggressive", "Pause"], index=1)

configs = {
    "Safe": {"risk": 0.02, "tp": 0.02, "sl": 0.01},
    "Neutral": {"risk": 0.04, "tp": 0.05, "sl": 0.02},
    "Aggressive": {"risk": 0.08, "tp": 0.10, "sl": 0.04},
    "Pause": {"risk": 0.0, "tp": 0.0, "sl": 0.0}
}
conf = configs[strategy]

# ====================== MARKET LOGIC ======================
def is_market_open(ticker):
    """Checks if the asset can currently be traded."""
    if "/" in ticker:  # Crypto is always open
        return True
    
    # Stock Market Check (Alpaca API check)
    try:
        clock = trade_client.get_clock()
        return clock.is_open
    except:
        return False

def analyze_ticker(ticker):
    try:
        yf_ticker = ticker.replace("/", "-")
        # Fetching enough data for a 20-period MA
        df = yf.download(yf_ticker, period="5d", interval="60m", progress=False)
        if df.empty or len(df) < 20: return None
        
        current_price = float(df['Close'].iloc[-1])
        ma20 = float(df['Close'].rolling(20).mean().iloc[-1])
        diff = (current_price - ma20) / ma20
        
        # Logic: If price is >2% below average, it's a "Buy the Dip" signal
        if diff < -0.02:
            return {"action": "BUY", "price": current_price, "bias": "OVERSOLD"}
        return {"action": "HOLD", "price": current_price, "bias": "STABLE"}
    except:
        return None

# ====================== EXECUTION ======================
def execute_trade(ticker, analysis):
    if not is_market_open(ticker):
        st.sidebar.warning(f"Market Closed for {ticker}. Skipping...")
        return False

    try:
        acc = trade_client.get_account()
        # Use 'cash' for calculation to avoid over-leveraging
        available_cap = float(acc.cash)
        
        pos_size_dollars = available_cap * conf['risk']
        qty = pos_size_dollars / analysis['price']
        
        # Formatting for Alpaca: Crypto handles 4 decimals, Stocks handle 0 (usually)
        symbol = ticker.replace("/", "")
        qty = round(qty, 4) if "/" in ticker else int(qty)
        
        if qty <= 0: return False

        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=round(analysis['price'] * (1 + conf['tp']), 2)),
            stop_loss=StopLossRequest(stop_price=round(analysis['price'] * (1 - conf['sl']), 2))
        )
        
        trade_client.submit_order(order_data)
        return True
    except Exception as e:
        st.sidebar.error(f"Order failed for {ticker}: {e}")
        return False

# ====================== DASHBOARD UI ======================
tab1, tab2 = st.tabs(["🏛️ Terminal", "📜 History"])

with tab1:
    col1, col2 = st.columns(2)
    try:
        acc = trade_client.get_account()
        col1.metric("Paper Balance", f"${float(acc.equity):,.2f}")
        col2.metric("Strategy", strategy)
    except:
        st.error("Could not fetch account data. Check API keys.")

    watchlist = ["BTC/USD", "ETH/USD", "SOL/USD", "NVDA", "TSLA", "AMD"]
    
    if strategy != "Pause":
        st.write("### 📡 Real-Time Analysis")
        for t in watchlist:
            analysis = analyze_ticker(t)
            if analysis:
                status_color = "green" if analysis['action'] == "BUY" else "white"
                st.markdown(f"**{t}**: {analysis['bias']} | Price: ${analysis['price']:,.2f}")
                
                if analysis['action'] == "BUY":
                    if execute_trade(t, analysis):
                        st.success(f"🚀 Trade placed for {t}")
    else:
        st.info("Bot is paused. No active scanning.")

# Refresh every minute
time.sleep(60)
st.rerun()
