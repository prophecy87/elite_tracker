import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time

st.set_page_config(page_title="Crypto Signal Bot", layout="wide")
st.title("🚀 Crypto Signal Bot - Short & Long Term")

# Watchlist
watchlist = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD", "ADA-USD", "DOGE-USD"]

# Safe price fetch
def get_data(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty:
            return None
        df = df.dropna()
        return df
    except:
        return None

# Short-term signals (5-15 min timeframe)
def short_term_signal(ticker):
    df = get_data(ticker, "5d", "5m")
    if df is None or len(df) < 50:
        return "ERROR", "No data"
    
    df['RSI'] = 100 - (100 / (1 + df['Close'].diff().clip(lower=0).rolling(14).mean() / 
                             abs(df['Close'].diff().clip(upper=0).rolling(14).mean())))
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    
    price = df['Close'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    
    if rsi < 30 and price > df['MA20'].iloc[-1]:
        return "🟢 STRONG BUY", f"RSI oversold + above MA20 | Price: ${price:,.2f}"
    elif rsi > 70 and price < df['MA20'].iloc[-1]:
        return "🔴 STRONG SELL", f"RSI overbought + below MA20 | Price: ${price:,.2f}"
    else:
        return "🟡 HOLD", f"Neutral | RSI {rsi:.1f} | Price: ${price:,.2f}"

# Long-term signals (daily timeframe)
def long_term_signal(ticker):
    df = get_data(ticker, "1y", "1d")
    if df is None or len(df) < 200:
        return "ERROR", "No data"
    
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA200'] = df['Close'].rolling(200).mean()
    price = df['Close'].iloc[-1]
    
    if price > df['MA200'].iloc[-1] and df['MA50'].iloc[-1] > df['MA200'].iloc[-1]:
        return "🟢 LONG-TERM BUY", f"Golden Cross | Above 200 MA | Price: ${price:,.2f}"
    elif price < df['MA200'].iloc[-1] and df['MA50'].iloc[-1] < df['MA200'].iloc[-1]:
        return "🔴 LONG-TERM SELL", f"Death Cross | Below 200 MA | Price: ${price:,.2f}"
    else:
        return "🟡 LONG-TERM HOLD", f"Range-bound | Price: ${price:,.2f}"

# Main UI
tab1, tab2 = st.tabs(["📊 Live Signals", "📈 Backtest Mode"])

with tab1:
    st.subheader("Real-time Signals")
    for ticker in watchlist:
        col1, col2, col3 = st.columns([1, 2, 3])
        with col1:
            st.write(f"**{ticker}**")
        with col2:
            short_sig, short_reason = short_term_signal(ticker)
            st.write(f"Short-term: {short_sig}")
            st.caption(short_reason)
        with col3:
            long_sig, long_reason = long_term_signal(ticker)
            st.write(f"Long-term: {long_sig}")
            st.caption(long_reason)
        st.divider()

with tab2:
    st.info("Backtest mode coming in next version (historical performance).")
    st.caption("This bot is for educational purposes only. Not financial advice.")

status = st.empty()
status.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

time.sleep(30)
st.rerun()
