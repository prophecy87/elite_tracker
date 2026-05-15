import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(page_title="EliteForge • Entry/Exit", layout="wide")

# Custom CSS to match your Dark Command Center aesthetic
st.markdown("""
<style>
    .stApp { background:#04040a; color:#dde3ff; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #00f2ff; }
    .stExpander { border: 1px solid #1e1e2e; background: #090912; }
</style>
""", unsafe_allow_html=True)

st.title("🔥 EliteForge • Strategic Screener")
st.caption("Strategic Multi-Timeframe Analysis • Data via Yahoo Finance")

watchlist = {
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana",
    "NVDA": "NVIDIA", "TSLA": "Tesla", "MSTR": "MicroStrategy",
    "AAPL": "Apple", "COIN": "Coinbase"
}

timeframes = {"4H": "90m", "1W": "1wk", "1M": "1mo"}

@st.cache_data(ttl=60)
def fetch_and_analyze(ticker, name, interval):
    try:
        period = "1mo" if interval == "90m" else "2y"
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty or len(df) < 50: 
            return None

        # Clean column names for pandas_ta
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

        # Indicators
        rsi = df.ta.rsi(length=14).iloc[-1]
        bb = df.ta.bbands(length=20, std=2)
        ma50 = df.ta.sma(length=50).iloc[-1]
        
        close = df['Close'].iloc[-1]
        upper = bb['BBU_20_2.0'].iloc[-1]
        lower = bb['BBL_20_2.0'].iloc[-1]

        # Logic
        if rsi < 30 and close < lower: 
            sig = "🟢 STRONG BUY"
        elif rsi > 70 and close > upper: 
            sig = "🔴 STRONG SELL"
        elif close > ma50: 
            sig = "🟢 BUY"
        else: 
            sig = "🔴 SELL"

        return {"signal": sig, "price": close, "rsi": rsi, "ma50": ma50}
    except:
        return None

# Process Data safely
rows = []
for sym, name in watchlist.items():
    results = {}
    for tf_name, tf_interval in timeframes.items():
        results[tf_name] = fetch_and_analyze(sym, name, tf_interval)
    
    # Safe access - never crash on None
    row = {
        "Asset": sym,
        "Name": name,
        "Price": f"${results['4H']['price']:,.2f}" if results.get('4H') else "—",
        "4H": results["4H"]["signal"] if results.get("4H") else "—",
        "1W": results["1W"]["signal"] if results.get("1W") else "—",
        "1M": results["1M"]["signal"] if results.get("1M") else "—",
    }
    
    # Overall trend (safe)
    buy_count = sum(1 for v in results.values() if v and "BUY" in v.get("signal", ""))
    row["Trend"] = "🟢 ACCUMULATE" if buy_count >= 2 else "🔴 DISTRIBUTION"
    
    rows.append(row)

# --- UI Display ---
st.subheader("🎯 Live Confluence Tracker")
df_display = pd.DataFrame(rows)
st.dataframe(df_display, width='stretch', hide_index=True)

st.divider()

# Detailed Drilldown
st.subheader("📈 Technical Deep Dive")
cols = st.columns(3)
for idx, (sym, name) in enumerate(watchlist.items()):
    with cols[idx % 3]:
        with st.expander(f"{sym} Details"):
            data = fetch_and_analyze(sym, name, "90m")
            if data:
                st.metric("Price", f"${data['price']:,.2f}")
                st.write(f"**RSI:** {data['rsi']:.2f}")
                st.write(f"**Trend:** {'Bullish' if data['price'] > data['ma50'] else 'Bearish'}")
                if data['rsi'] < 30:
                    st.success("Reasoning: Major oversold condition identified.")
                elif data['rsi'] > 70:
                    st.error("Reasoning: Price is overextended/exhausted.")
            else:
                st.warning("No data available for this asset")

st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')} • Auto-refreshing every 60 seconds")
time.sleep(60)
st.rerun()
