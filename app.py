import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
import pandas_ta as ta 
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# ====================== 2026 APEX UI ======================
st.set_page_config(page_title="EliteForge v28.1 • Singularity", layout="wide", page_icon="⚡")

st.markdown("""
<style>
    .stApp { background-color: #020205; color: #e0e0ff; }
    .title-glow { font-size: 3.5rem; font-weight: 900; color: #00f2ff; text-shadow: 0 0 20px #00f2ff; text-align: center; margin-bottom: 20px; }
    .metric-card { background: #0a0a1a; border: 1px solid #1e1e3f; padding: 15px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="title-glow">ELITEFORGE v28.1 • SINGULARITY</h1>', unsafe_allow_html=True)

# ====================== ALPACA CONNECTION ======================
@st.cache_resource
def connect_alpaca():
    try:
        return TradingClient(st.secrets["alpaca"]["api_key"], st.secrets["alpaca"]["secret_key"], paper=True)
    except: return None

trade_client = connect_alpaca()

# ====================== QUANT ORACLE (Real Logic) ======================
def get_institutional_forecast(watchlist):
    forecasts = []
    for ticker in watchlist:
        try:
            yf_ticker = ticker.replace("/", "-")
            df = yf.download(yf_ticker, period="2d", interval="5m", progress=False)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # Technicals
            df['RSI'] = ta.rsi(df['Close'], length=14)
            bb = ta.bbands(df['Close'], length=20, std=2)
            df = pd.concat([df, bb], axis=1)
            
            last = df.iloc[-1]
            price, rsi = last['Close'], last['RSI']
            lower, upper = last.filter(like='BBL').iloc[0], last.filter(like='BBU').iloc[0]
            
            # Confidence based on volatility stretch
            volatility_score = (abs(price - ((upper+lower)/2)) / ((upper-lower)/2)) * 100
            confidence = min(98, max(65, int(volatility_score)))
            
            signal = "HOLD"
            if price <= lower and rsi < 35: signal = "BUY"
            elif price >= upper and rsi > 65: signal = "SELL"
                
            forecasts.append({
                "Asset": ticker, "Price": f"${price:,.2f}",
                "Signal": signal, "Confidence": f"{confidence}%",
                "RSI": f"{rsi:.1f}", "Target": f"${(price * 1.05 if signal == 'BUY' else price * 0.95):,.2f}"
            })
        except: continue
    return forecasts

# ====================== MAIN TERMINAL ======================
tab1, tab2, tab3 = st.tabs(["🏛️ Institutional Terminal", "🔮 Singularity Forecast", "📜 Full Ledger"])

with tab1:
    try:
        acc = trade_client.get_account()
        m1, m2, m3 = st.columns(3)
        m1.metric("Portfolio Equity", f"${float(acc.equity):,.2f}")
        m2.metric("Buying Power", f"${float(acc.buying_power):,.2f}")
        m3.metric("Day PnL", f"${float(acc.equity) - float(acc.last_equity):,.2f}")
    except: st.error("Connection Error")

    st.subheader("📊 Live Portfolio (Detailed)")
    try:
        positions = trade_client.get_all_positions()
        if positions:
            # ALL COLUMNS REQUESTED
            pos_list = []
            for p in positions:
                mkt_val = float(p.market_value)
                cost = float(p.cost_basis)
                unrealized_pnl = float(p.unrealized_pl)
                pnl_pct = (unrealized_pnl / cost) * 100 if cost != 0 else 0
                
                pos_list.append({
                    "Symbol": p.symbol,
                    "Qty": p.qty,
                    "Avg Entry": f"${float(p.avg_entry_price):,.2f}",
                    "Current Price": f"${float(p.current_price):,.2f}",
                    "Market Value": f"${mkt_val:,.2f}",
                    "Unrealized PnL": f"${unrealized_pnl:,.2f}",
                    "Total Change %": f"{pnl_pct:+.2f}%",
                    "Today's Change %": f"{float(p.change_today)*100:+.2f}%"
                })
            st.dataframe(pd.DataFrame(pos_list), width='stretch', hide_index=True)
        else:
            st.info("No active positions.")
    except Exception as e:
        st.write("Waiting for data...")

with tab2:
    st.subheader("🎯 High-Conviction Signals")
    watchlist = ["BTC/USD", "ETH/USD", "SOL/USD", "NVDA", "TSLA", "MSTR", "AMD"]
    data = get_institutional_forecast(watchlist)
    if data:
        st.dataframe(pd.DataFrame(data), width='stretch', hide_index=True)

with tab3:
    st.subheader("📜 System Ledger")
    if 'trades' not in st.session_state:
        st.info("No trades executed in this session.")
    else:
        st.dataframe(pd.DataFrame(st.session_state.trades)[::-1], width='stretch', hide_index=True)

# ====================== SYSTEM CONTROL ======================
status = st.empty()
status.caption(f"Orbital Sync: {datetime.now().strftime('%H:%M:%S')} | Logic: Multi-Factor")

time.sleep(30)
st.rerun()
