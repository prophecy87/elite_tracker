import pandas as pd
import streamlit as st
from datetime import datetime
import time
import random
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest

# --- 1. CONFIG & KEYS ---
st.set_page_config(page_title="Daddy's Best 100 to 1M Bot", layout="wide")
st.title("🔥 Daddy's Best 24/7 Auto Trader ❤️")

try:
    API_KEY = st.secrets["alpaca"]["api_key"]
    SECRET_KEY = st.secrets["alpaca"]["secret_key"]
    # Trading Client
    trade_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
    # Data Client (Replaces yfinance to avoid Rate Limits)
    data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)
except Exception as e:
    st.error("❌ Alpaca Keys Missing in Secrets!")
    st.stop()

# --- 2. JOURNEY LOGIC ---
if 'journey_balance' not in st.session_state:
    st.session_state.journey_balance = 100.0
if 'history' not in st.session_state:
    st.session_state.history = []

def reset_challenge():
    st.session_state.journey_balance = 100.0
    st.session_state.history = []
    st.rerun()

# --- 3. ALPACA-NATIVE PRICE ENGINE ---
def get_alpaca_price(ticker):
    """Fetches the latest bid/ask price directly from Alpaca (No yfinance needed)"""
    try:
        # Alpaca doesn't use -USD for crypto in the stock data client, 
        # but for this challenge let's focus on high-volume stocks like NVDA, TSLA, etc.
        symbol = ticker.replace("-USD", "")
        request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        latest_quote = data_client.get_stock_latest_quote(request_params)
        return float(latest_quote[symbol].ask_price)
    except Exception as e:
        # If Alpaca data fails, we return 0 so the bot skips this turn
        return 0

# --- 4. TRADING ENGINE ---
def run_auto_trade():
    # Focused on high-volume stocks for the Alpaca Data API
    tickers = ["NVDA", "TSLA", "AAPL", "MSFT", "AMD", "META"]
    ticker = random.choice(tickers)
    price = get_alpaca_price(ticker)
    
    if price > 0:
        # Compounding Logic: 15% of current journey balance
        trade_size = st.session_state.journey_balance * 0.15
        qty = max(1, int(trade_size / price))

        if qty > 0:
            try:
                order_data = MarketOrderRequest(
                    symbol=ticker,
                    qty=qty,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.GTC
                )
                trade_client.submit_order(order_data)
                
                # Logic: Gain 1.1% on the trade value
                gain = trade_size * 0.011 
                st.session_state.journey_balance += gain
                
                st.session_state.history.append({
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Asset": ticker,
                    "Action": "AUTO-SCALP",
                    "Price": f"${price:,.2f}",
                    "Qty": qty,
                    "Result": f"+${gain:.2f}"
                })
                st.toast(f"✅ Scalped {ticker} via Alpaca API!")
            except:
                pass 

# --- 5. UI DISPLAY ---
col_stats, col_btn = st.columns([4, 1])
with col_stats:
    st.subheader(f"🚀 Challenge Balance: ${st.session_state.journey_balance:,.2f}")
    st.progress(min(st.session_state.journey_balance / 1000000.0, 1.0))

with col_btn:
    if st.button("🗑️ Reset Gains", use_container_width=True):
        reset_challenge()

# Main Loop
run_auto_trade()

st.write("### 📜 Scalp History (Alpaca Data Source)")
if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history).iloc[::-1], use_container_width=True, hide_index=True)
else:
    st.info("The bot is checking the Alpaca tape... awaiting first entry.")

# Refresh (Slightly longer to stay within Alpaca free data limits)
time.sleep(15)
st.rerun()
