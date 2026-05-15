import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(page_title="EliteForge • Entry/Exit", layout="wide")

st.markdown("""
<style>
    .stApp { background:#04040a; color:#dde3ff; }
    .stMetricValue { font-size: 1.9rem; color: #00f2ff; }
    .stExpander { border: 1px solid #1e1e2e; background: #090912; }
</style>
""", unsafe_allow_html=True)

st.title("🔥 EliteForge • Strategic Entry & Exit Dashboard")
st.caption("Real indicators + clear reasoning • Auto-refreshes every 60 seconds")

# Elite watchlist
watchlist = {
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana",
    "NVDA": "NVIDIA", "TSLA": "Tesla", "MSTR": "MicroStrategy",
    "AAPL": "Apple", "COIN": "Coinbase"
}

timeframes = {"4 Hour": "90m", "1 Week": "1wk", "1 Month": "1mo"}

@st.cache_data(ttl=60)
def analyze_asset(ticker):
    results = {}
    for name, interval in timeframes.items():
        try:
            period = "60d" if interval == "90m" else "1y"
            df = yf.download(ticker, period=period, interval=interval, progress=False)
            if df.empty or len(df) < 50:
                results[name] = None
                continue

            # Clean columns for pandas_ta
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

            # Indicators
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            bb = ta.bbands(df['Close'], length=20, std=2)
            sma50 = ta.sma(df['Close'], length=50).iloc[-1]
            close = df['Close'].iloc[-1]
            upper = bb['BBU_20_2.0'].iloc[-1]
            lower = bb['BBL_20_2.0'].iloc[-1]

            # Signal logic
            if rsi < 30 and close < lower:
                sig = "🟢 STRONG BUY"
                reason = "Oversold + broke below lower Bollinger Band"
            elif rsi > 70 and close > upper:
                sig = "🔴 STRONG SELL"
                reason = "Overbought + broke above upper Bollinger Band"
            elif close > sma50:
                sig = "🟢 BUY"
                reason = "Price above 50-period SMA (bullish trend)"
            else:
                sig = "🔴 SELL"
                reason = "Price below 50-period SMA (bearish trend)"

            results[name] = {"price": close, "rsi": rsi, "signal": sig, "reason": reason}
        except:
            results[name] = None
    return results

# Build main table
rows = []
for sym, name in watchlist.items():
    data = analyze_asset(sym)
    if data.get("4 Hour") is None:
        continue
    row = {
        "Asset": f"{sym} — {name}",
        "Price": f"${data['4 Hour']['price']:,.4f}" if "USD" in sym else f"${data['4 Hour']['price']:,.2f}",
        "4 Hour": data["4 Hour"]["signal"],
        "1 Week": data["1 Week"]["signal"] if data["1 Week"] else "—",
        "1 Month": data["1 Month"]["signal"] if data["1 Month"] else "—",
    }
    rows.append(row)

st.subheader("🎯 Elite Confluence Table")
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()

# Detailed charts + reasoning
st.subheader("📈 Technical Deep Dive")
for sym, name in watchlist.items():
    data = analyze_asset(sym)
    if data.get("4 Hour") is None:
        continue
    with st.expander(f"{sym} — {name}", expanded=False):
        price = data["4 Hour"]["price"]
        st.metric("Current Price", f"${price:,.4f}" if "USD" in sym else f"${price:,.2f}")
        
        # Chart
        df = yf.download(sym, period="6mo", interval="1d", progress=False)
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'].rolling(20).mean(), name="SMA20", line=dict(color="orange")))
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'].rolling(50).mean(), name="SMA50", line=dict(color="blue")))
        fig.update_layout(height=450, title=f"{sym} Price Chart", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Why the signal?")
        for tf in ["4 Hour", "1 Week", "1 Month"]:
            if data.get(tf):
                st.write(f"**{tf}**: {data[tf]['signal']} → {data[tf]['reason']}")

st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')} • Auto-refreshing every 60 seconds")
time.sleep(60)
st.rerun()
