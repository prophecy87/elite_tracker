import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass

# ====================== PAGE SETUP ======================
st.set_page_config(page_title="EliteForge v24.3", layout="wide")
st.title("🔥 EliteForge • Hybrid Engine")

# Sidebar for status and settings
st.sidebar.header("System Status")
log_container = st.sidebar.container()

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
        st.error(f"Alpaca Connection Error: {e}")
        return None

trade_client = connect_alpaca()

# ====================== STRATEGY SETTINGS ======================
strategy = st.sidebar.selectbox("🎛️ Strategy Mode", ["Safe", "Neutral", "Aggressive", "Pause"], index=1)
configs = {
    "Safe": {"risk": 0.02, "tp": 0.02, "sl": 0.01},
    "Neutral": {"risk": 0.04, "tp": 0.05, "sl": 0.02},
    "Aggressive": {"risk": 0.08, "tp": 0.10, "sl": 0.04},
    "Pause": {"risk": 0.0, "tp": 0.0, "sl": 0.0}
}
conf = configs[strategy]

# ====================== RE-ENGINEERED ANALYSIS ======================
def analyze_ticker(ticker):
    """Fetches data and calculates signals. Now with error reporting."""
    try:
        # Format for yFinance: Crypto uses '-' (BTC-USD), Stocks use '.' (BRK.B)
        yf_ticker = ticker.replace("/", "-")
        
        # Use 15m intervals for more 'Real-Time' feel than 60m
        df = yf.download(yf_ticker, period="2d", interval="15m", progress=False)
        
        if df.empty:
            return {"error": "No data found (Market might be closed or Ticker invalid)"}
        
        if len(df) < 20:
            return {"error": f"Insufficient data (Need 20 periods, got {len(df)})"}
            
        current_price = float(df['Close'].iloc[-1])
        ma20 = float(df['Close'].rolling(20).mean().iloc[-1])
        diff = (current_price - ma20) / ma20
        
        # Determine Signal
        if diff < -0.015: # 1.5% dip
            action = "BUY"
            bias = "OVERSOLD"
        elif diff > 0.015:
            action = "SELL_SIGNAL" # Just a warning for now
            bias = "OVERBOUGHT"
        else:
            action = "HOLD"
            bias = "NEUTRAL"
            
        return {
            "action": action, 
            "price": current_price, 
            "ma": ma20,
            "diff": diff,
            "bias": bias,
            "error": None
        }
    except Exception as e:
        return {"error": str(e)}

# ====================== EXECUTION ======================
def execute_trade(ticker, analysis):
    # (Same logic as before, but ensure symbol formatting is correct for Alpaca)
    try:
        symbol = ticker.replace("/", "") # Alpaca wants BTCUSD
        acc = trade_client.get_account()
        cash = float(acc.cash)
        qty = (cash * conf['risk']) / analysis['price']
        qty = round(qty, 4) if "/" in ticker else int(qty)
        
        if qty > 0:
            order = MarketOrderRequest(
                symbol=symbol, qty=qty, side=OrderSide.BUY,
                time_in_force=TimeInForce.GTC, order_class=OrderClass.BRACKET,
                take_profit=TakeProfitRequest(limit_price=round(analysis['price'] * (1 + conf['tp']), 2)),
                stop_loss=StopLossRequest(stop_price=round(analysis['price'] * (1 - conf['sl']), 2))
            )
            trade_client.submit_order(order)
            return True
    except Exception as e:
        st.sidebar.error(f"Execution Error: {e}")
    return False

# ====================== DASHBOARD UI ======================
tab1, tab2 = st.tabs(["🏛️ Live Terminal", "📜 Account Info"])

with tab1:
    st.subheader(f"📡 System Scan: {datetime.now().strftime('%H:%M:%S')}")
    
    # Grid for assets
    watchlist = ["BTC/USD", "ETH/USD", "SOL/USD", "NVDA", "TSLA", "AAPL"]
    cols = st.columns(3)
    
    for i, ticker in enumerate(watchlist):
        with cols[i % 3]:
            with st.status(f"Analyzing {ticker}...", expanded=True) as s:
                result = analyze_ticker(ticker)
                
                if result.get("error"):
                    st.error(f"Error: {result['error']}")
                else:
                    st.metric(ticker, f"${result['price']:,.2f}", f"{result['diff']:.2%}")
                    st.write(f"**Bias:** {result['bias']}")
                    
                    if result['action'] == "BUY" and strategy != "Pause":
                        if execute_trade(ticker, result):
                            st.success("TRADE PLACED")
                    elif result['action'] == "HOLD":
                        st.info("Signal: HOLD")
                s.update(label=f"{ticker} Analysis Complete", state="complete")

with tab2:
    try:
        acc = trade_client.get_account()
        st.json({
            "Equity": f"${float(acc.equity):,.2f}",
            "Cash": f"${float(acc.cash):,.2f}",
            "Buying Power": f"${float(acc.buying_power):,.2f}",
            "Initial Margin": acc.initial_margin
        })
    except:
        st.warning("Could not load account details.")

# ====================== REFRESH ======================
st.sidebar.write("---")
st.sidebar.write(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
time.sleep(30) # Refresh more frequently for testing
st.rerun()
