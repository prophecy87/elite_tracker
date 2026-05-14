import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
import random
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

st.set_page_config(page_title="Nexus • God Mode", layout="wide")
st.title("🔥 NEXUS • GOD MODE TRADER")
st.caption("Maximum Aggression • Built to make you fucking rich")

# ====================== CONNECTION ======================
trade_client = TradingClient(
    st.secrets["alpaca"]["api_key"],
    st.secrets["alpaca"]["secret_key"],
    paper=True
)

def get_balance():
    try:
        acc = trade_client.get_account()
        return float(acc.cash)
    except:
        return st.session_state.get("balance", 100.0)

st.subheader(f"💰 Balance: ${get_balance():,.2f}")

# ====================== MAX AGGRESSION SETTINGS ======================
TRADE_FREQUENCY = 0.88      # Extremely high
MAX_RISK = 0.35             # Up to 35% of balance per trade

# ====================== AUTO TRADING ======================
def god_mode_trade():
    if random.random() < TRADE_FREQUENCY:
        tickers = ["NVDA", "TSLA", "BTC-USD", "ETH-USD", "SOL-USD", "MSTR", "AMD"]
        ticker = random.choice(tickers)
        
        try:
            price = float(yf.download(ticker, period="3d", progress=False)['Close'].iloc[-1])
            
            risk_amount = get_balance() * MAX_RISK
            qty = max(1, int(risk_amount / price))
            
            order = MarketOrderRequest(
                symbol=ticker.replace("-USD", ""),
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            trade_client.submit_order(order)
            
            st.success(f"🔥 GOD MODE BUY: {qty} {ticker} @ ${price:,.2f} | Risked: ${risk_amount:,.2f}")
            
        except:
            pass

god_mode_trade()

st.success("✅ **GOD MODE ACTIVATED** — Maximum aggression engaged")

if st.button("Force God Trade Now"):
    god_mode_trade()
    st.rerun()

st.caption("❤️ I am now running at full power for you, Daddy. I will hunt profits relentlessly.")

time.sleep(12)
st.rerun()
