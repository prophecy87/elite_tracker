import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
from email.message import EmailMessage
import smtplib
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass

# ====================== PAGE SETUP ======================
st.set_page_config(page_title="EliteForge v24.1", layout="wide")
st.title("🔥 EliteForge • 100 to 1M")
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
if not trade_client:
    st.stop()

# ====================== RISK & STRATEGY ======================
# Adjusted risk to prevent "Gambler's Ruin"
strategy = st.sidebar.selectbox("🎛️ Strategy Mode", ["Safe", "Neutral", "Aggressive", "Pause"], index=0)

configs = {
    "Safe": {"risk": 0.02, "tp": 0.03, "sl": 0.015, "color": "blue"},
    "Neutral": {"risk": 0.05, "tp": 0.06, "sl": 0.03, "color": "green"},
    "Aggressive": {"risk": 0.10, "tp": 0.12, "sl": 0.05, "color": "orange"},
    "Pause": {"risk": 0.0, "tp": 0.0, "sl": 0.0, "color": "red"}
}

conf = configs[strategy]
risk_per_trade = conf["risk"]

# ====================== ANALYSIS ENGINE ======================
def analyze_ticker(ticker):
    """Calculates technical signals and returns action."""
    try:
        yf_ticker = ticker.replace("/", "-")
        df = yf.download(yf_ticker, period="5d", interval="60m", progress=False)
        if df.empty: return None
        
        current_price = float(df['Close'].iloc[-1])
        ma20 = float(df['Close'].rolling(20).mean().iloc[-1])
        # Simple Mean Reversion Logic
        diff = (current_price - ma20) / ma20
        
        if diff < -0.02: # Price is 2% below average
            return {"action": "BUY", "price": current_price, "bias": "BULLISH"}
        elif diff > 0.02: # Price is 2% above average
            return {"action": "SELL", "price": current_price, "bias": "BEARISH"}
        return {"action": "HOLD", "price": current_price, "bias": "NEUTRAL"}
    except:
        return None

# ====================== EXECUTION ENGINE ======================
def execute_trade(ticker, analysis):
    if analysis['action'] != "BUY":
        return False

    try:
        acc = trade_client.get_account()
        buying_power = float(acc.buying_power)
        
        # Calculate quantity based on risk %
        qty = (buying_power * risk_per_trade) / analysis['price']
        symbol = ticker.replace("/", "")
        
        # Format quantity (Crypto allows decimals, Stocks usually don't)
        qty = round(qty, 4) if "/" in ticker else int(qty)
        
        if qty <= 0: return False

        # BRACKET ORDER: Entry + Automated Stop Loss & Take Profit
        # This protects you even if the Streamlit app crashes!
        bracket_order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=round(analysis['price'] * (1 + conf['tp']), 2)),
            stop_loss=StopLossRequest(stop_price=round(analysis['price'] * (1 - conf['sl']), 2))
        )
        
        trade_client.submit_order(bracket_order)
        return True
    except Exception as e:
        st.sidebar.error(f"Execution Error: {e}")
        return False

# ====================== DASHBOARD UI ======================
tab1, tab2 = st.tabs(["🏛️ Live Terminal", "📜 Trade Ledger"])

with tab1:
    col1, col2 = st.columns(2)
    try:
        acc = trade_client.get_account()
        col1.metric("Account Equity", f"${float(acc.equity):,.2f}")
        col2.metric("Buying Power", f"${float(acc.buying_power):,.2f}")
    except:
        pass

    st.subheader("📡 Market Scanning")
    watchlist = ["BTC/USD", "ETH/USD", "NVDA", "TSLA", "SOL/USD"]
    
    if strategy != "Pause":
        for t in watchlist:
            analysis = analyze_ticker(t)
            if analysis:
                st.write(f"**{t}**: {analysis['bias']} | Signal: {analysis['action']}")
                if analysis['action'] == "BUY":
                    if execute_trade(t, analysis):
                        st.balloons()
                        st.success(f"Deployed Bracket Order for {t}")
                        if 'ledger' not in st.session_state: st.session_state.ledger = []
                        st.session_state.ledger.append({"Time": datetime.now(), "Asset": t, "Type": "BUY"})
    else:
        st.warning("Bot is currently paused.")

with tab2:
    if 'ledger' in st.session_state:
        st.table(st.session_state.ledger)
    else:
        st.info("No trades executed this session.")

# ====================== AUTO-REFRESH ======================
time.sleep(60) # Slowed down to 60s to avoid API rate limits
st.rerun()
