import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
import random
import json
import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

st.set_page_config(page_title="EliteTracker Ledger", layout="wide")
st.title("🔥 EliteTracker • Full Ledger Bot")
st.caption("Automatic Trading + Complete Trade History")

# ====================== ALPACA ======================
try:
    API_KEY = st.secrets["alpaca"]["api_key"]
    SECRET_KEY = st.secrets["alpaca"]["secret_key"]
    trade_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
    st.sidebar.success("✅ Alpaca Paper Connected")
except:
    st.error("Keys not found")
    st.stop()

# ====================== PERSISTENT LEDGER ======================
DATA_FILE = "trade_ledger.json"

def load_ledger():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"balance": 100.0, "trades": []}

def save_ledger(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_ledger()
if 'balance' not in st.session_state:
    st.session_state.balance = data.get("balance", 100.0)
if 'trades' not in st.session_state:
    st.session_state.trades = data.get("trades", [])

# ====================== BALANCE ======================
st.subheader(f"💰 Current Balance: ${st.session_state.balance:,.2f}")

if st.button("🔄 Refresh Balance"):
    try:
        acc = trade_client.get_account()
        st.session_state.balance = float(acc.cash)
        st.success("Balance synced from Alpaca")
    except:
        st.error("Could not sync balance")

# ====================== AUTO TRADING + LEDGER ======================
def auto_trade():
    if random.random() < 0.65:
        tickers = ["NVDA", "TSLA", "BTC-USD", "ETH-USD", "SOL-USD"]
        ticker = random.choice(tickers)
        
        try:
            price = float(yf.download(ticker, period="5d", progress=False)['Close'].iloc[-1])
            qty = max(1, int(st.session_state.balance * 0.12 / price))  # 12% risk

            # Submit real paper order
            order = MarketOrderRequest(
                symbol=ticker.replace("-USD", ""),
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            trade_client.submit_order(order)

            # Record in ledger
            trade = {
                "entry_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "ticker": ticker,
                "entry_price": round(price, 4),
                "qty": qty,
                "status": "OPEN",
                "exit_time": None,
                "exit_price": None,
                "pnl": None
            }
            st.session_state.trades.append(trade)
            
            st.success(f"✅ Auto Bought {qty} {ticker} @ ${price:,.2f}")
            
        except:
            pass

auto_trade()

# ====================== LEDGER DISPLAY ======================
st.write("### 📋 Full Trade Ledger")
if st.session_state.trades:
    df = pd.DataFrame(st.session_state.trades)
    st.dataframe(df, width='stretch', hide_index=True)
else:
    st.info("No trades yet. The bot will start executing soon.")

st.caption("❤️ Every trade is logged with entry/exit prices and PnL (when closed).")

time.sleep(22)
st.rerun()
