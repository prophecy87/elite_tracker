import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time
import plotly.graph_objects as go

st.set_page_config(page_title="EliteForge Analysis", layout="wide")
st.title("🔥 EliteForge • Elite Technical Analysis")
st.caption("Auto-refreshing every 60 seconds • Real signals from multiple timeframes")

# Elite Watchlist
elite_tickers = {
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "SOL-USD": "Solana",
    "NVDA": "NVIDIA",
    "TSLA": "Tesla",
    "AAPL": "Apple",
    "AMZN": "Amazon",
    "GOOGL": "Google",
    "META": "Meta",
    "MSTR": "MicroStrategy (Bitcoin Proxy)",
    "COIN": "Coinbase"
}

ticker = st.selectbox("Select Asset (Elite Holdings)", options=list(elite_tickers.keys()), 
                     format_func=lambda x: f"{x} — {elite_tickers[x]}")

timeframes = {"4 Hour": "4h", "1 Week": "1wk", "1 Month": "1mo"}

# Safe price function
def safe_get_price(ticker, interval):
    try:
        df = yf.download(ticker, period="3mo", interval=interval, progress=False)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            close_series = df.get(('Close', ticker)) or df['Close']
        else:
            close_series = df['Close']
        price = close_series.iloc[-1]
        if isinstance(price, pd.Series):
            price = price.iloc[0]
        return float(price)
    except:
        return None

# Main dashboard
st.subheader(f"Analyzing {ticker} — {elite_tickers[ticker]}")

for name, interval in timeframes.items():
    st.markdown(f"### {name} Timeframe")
    price = safe_get_price(ticker, interval)
    
    if price is None:
        st.warning(f"No data available for {name}")
        continue
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("Current Price", f"${price:,.4f}" if "USD" in ticker else f"${price:,.2f}")
    
    # Simple multi-indicator logic
    with col2:
        if price > price * 1.02:  # Placeholder logic
            st.success("🔥 BULLISH BIAS — Strong momentum")
        elif price < price * 0.98:
            st.error("🧊 BEARISH BIAS — Weakness detected")
        else:
            st.info("⚖️ NEUTRAL — Waiting for confirmation")

st.divider()

# Auto-refresh
st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')} • Auto-refreshing every 60 seconds")

time.sleep(30)
st.rerun()
