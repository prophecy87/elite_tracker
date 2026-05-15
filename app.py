import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="EliteForge Analysis", layout="wide")
st.title("🔥 EliteForge • Pure Technical Analysis")
st.caption("Clean multi-timeframe signals — no trading, no Alpaca, just the data")

# Sidebar
ticker = st.sidebar.text_input("Ticker (e.g. BTC-USD, NVDA, TSLA, ETH-USD)", value="BTC-USD")
timeframes = {"4hr": "4h", "1 Week": "1wk", "1 Month": "1mo"}

# Aggressiveness ranking of indicators (most → least aggressive)
indicators_rank = [
    ("RSI (14)", "Short-term momentum — very aggressive"),
    ("Stochastic", "Fast oscillator — aggressive"),
    ("Bollinger Bands", "Volatility squeeze — aggressive"),
    ("MACD", "Momentum crossover — medium"),
    ("EMA (12/26)", "Short-term trend — medium"),
    ("SMA (50/200)", "Long-term trend — conservative"),
    ("Ichimoku Cloud", "Trend & support — conservative"),
    ("Volume", "Confirmation — conservative")
]

# Fetch data and calculate signals
def get_signals(ticker, interval):
    try:
        df = yf.download(ticker, period="3mo", interval=interval, progress=False)
        if df.empty:
            return None, None
        
        # Basic indicators
        close = df['Close']
        df['RSI'] = 100 - (100 / (1 + (close.diff(1).where(close.diff(1) > 0, 0).rolling(14).mean() / 
                                  abs(close.diff(1).where(close.diff(1) < 0, 0).rolling(14).mean()))))
        df['SMA50'] = close.rolling(50).mean()
        df['SMA200'] = close.rolling(200).mean()
        df['EMA12'] = close.ewm(span=12).mean()
        df['EMA26'] = close.ewm(span=26).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['UpperBB'] = close.rolling(20).mean() + 2 * close.rolling(20).std()
        df['LowerBB'] = close.rolling(20).mean() - 2 * close.rolling(20).std()
        
        current = df.iloc[-1]
        price = current['Close']
        
        signals = []
        # RSI
        if current['RSI'] < 30: signals.append(("RSI", "Strong BUY", "Oversold"))
        elif current['RSI'] > 70: signals.append(("RSI", "Strong SELL", "Overbought"))
        else: signals.append(("RSI", "Neutral", "-"))
        
        # Bollinger
        if price < current['LowerBB']: signals.append(("Bollinger", "Strong BUY", "Below lower band"))
        elif price > current['UpperBB']: signals.append(("Bollinger", "Strong SELL", "Above upper band"))
        else: signals.append(("Bollinger", "Neutral", "-"))
        
        # MACD
        if current['MACD'] > 0: signals.append(("MACD", "BUY", "Bullish crossover"))
        else: signals.append(("MACD", "SELL", "Bearish"))
        
        # Moving Averages
        if price > current['SMA50'] > current['SMA200']: signals.append(("SMA", "Strong BUY", "Golden cross"))
        elif price < current['SMA50'] < current['SMA200']: signals.append(("SMA", "Strong SELL", "Death cross"))
        else: signals.append(("SMA", "Neutral", "-"))
        
        return price, signals, df
    except:
        return None, None, None

# Main dashboard
st.subheader(f"Analyzing {ticker}")

for name, interval in timeframes.items():
    st.markdown(f"### {name} Timeframe")
    price, signals, df = get_signals(ticker, interval)
    
    if price is None:
        st.warning(f"No data for {name}")
        continue
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("Current Price", f"${price:,.2f}")
    with col2:
        for ind, sig, reason in signals:
            color = "🟢" if "BUY" in sig else "🔴" if "SELL" in sig else "🟡"
            st.write(f"{color} **{ind}**: {sig} — {reason}")
    
    # Simple chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name="SMA50", line=dict(color="orange")))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], name="SMA200", line=dict(color="blue")))
    fig.update_layout(height=400, title=f"{ticker} — {name}")
    st.plotly_chart(fig, use_container_width=True)
    st.divider()

# Aggressiveness ranking table
st.subheader("Indicator Aggressiveness Ranking")
df_rank = pd.DataFrame(indicators_rank, columns=["Indicator", "Description"])
st.dataframe(df_rank, use_container_width=True, hide_index=True)

st.caption("Most aggressive (top) = short-term, high sensitivity • Least aggressive (bottom) = long-term, smoother")
