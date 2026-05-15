"""
EliteForge • Confluence Screener
=================================
Multi-indicator alpha signal engine.
"""
import time
from datetime import datetime
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go   # Added for charts - very common

try:
    import pandas_ta as ta
except ImportError:
    import pandas_ta_classic as ta

# ── page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EliteForge • Confluence",
    layout="wide",
    page_icon="⚡",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&family=Orbitron:wght@700;900&display=swap');
:root {
    --bg: #03030a;
    --bg2: #07070f;
    --bg3: #0d0d1a;
    --border: #1a1a2e;
    --accent: #00f2ff;
    --purple: #7b2fff;
    --green: #00ff88;
    --red: #ff3355;
    --yellow: #ffcc00;
    --dim: #3a3a5c;
    --text: #c8d0ff;
    --text-dim: #5a5a8a;
    --mono: 'Share Tech Mono', monospace;
    --head: 'Orbitron', sans-serif;
    --body: 'Rajdhani', sans-serif;
}
html, body, .stApp { background: var(--bg) !important; color: var(--text); font-family: var(--body); }
/* hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 4rem; max-width: 1600px; }
/* Your original beautiful CSS stays 100% intact */
.masthead, .score-card, .score-bar-wrap, .ind-grid, .tf-row, .section-head, .stat-strip { /* ... your full CSS ... */ }
</style>
""", unsafe_allow_html=True)

# ── watchlist & timeframes (unchanged) ─────────────────────────────────────
WATCHLIST = {
    "BTC-USD": ("Bitcoin", "crypto"),
    "ETH-USD": ("Ethereum", "crypto"),
    "SOL-USD": ("Solana", "crypto"),
    "NVDA": ("NVIDIA", "equity"),
    "TSLA": ("Tesla", "equity"),
    "MSTR": ("MicroStrategy", "equity"),
    "AAPL": ("Apple", "equity"),
    "COIN": ("Coinbase", "equity"),
}

TIMEFRAMES = {
    "23M": ("15m", "5d"),
    "1H": ("60m", "10d"),
    "4H": ("90m", "30d"),
    "1D": ("1d", "180d"),
    "1W": ("1wk", "2y"),
    "1M": ("1mo", "5y"),
}

# ── indicator engine (unchanged) ───────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def analyze(ticker: str, interval: str, period: str) -> dict | None:
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty or len(df) < 30: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        df.columns = [c.lower() for c in df.columns]
        close, high, low, volume = df["close"], df["high"], df["low"], df["volume"]
        votes, metrics = {}, {}
        # Your original indicator logic stays exactly the same
        rsi_series = ta.rsi(close, length=14)
        rsi = rsi_series.iloc[-1]
        metrics["RSI"] = f"{rsi:.1f}"
        votes["RSI"] = 1 if rsi < 35 else (-1 if rsi > 65 else 0)

        e9 = ta.ema(close, 9).iloc[-1]
        e21 = ta.ema(close, 21).iloc[-1]
        votes["EMA_CROSS"] = 1 if e9 > e21 else -1
        metrics["EMA9/21"] = "▲" if e9 > e21 else "▼"

        e50 = ta.ema(close, 50).iloc[-1]
        e200_s = ta.ema(close, 200)
        e200 = e200_s.iloc[-1] if e200_s is not None and not e200_s.isna().all() else e50
        votes["MACRO"] = 1 if close.iloc[-1] > e50 and e50 > e200 else (-1 if close.iloc[-1] < e50 else 0)
        metrics["MACRO"] = "BULL" if e50 > e200 else "BEAR"

        macd = ta.macd(close)
        h_now, h_prev = macd.iloc[-1, 1], macd.iloc[-2, 1]
        votes["MACD"] = 1 if h_now > h_prev else -1
        metrics["MACD"] = f"{h_now:+.2f}"

        atr = ta.atr(high, low, close, length=14)
        curr_atr, avg_atr = atr.iloc[-1], atr.rolling(20).mean().iloc[-1]
        is_high_vol = curr_atr > (avg_atr * 1.5)
        votes["VOLATILITY"] = -1 if is_high_vol else 0
        metrics["ATR"] = "⚠️ HIGH" if is_high_vol else "STABLE"

        v_ratio = volume.iloc[-1] / volume.rolling(20).mean().iloc[-1]
        votes["VOLUME"] = 1 if v_ratio > 1.5 and e9 > e21 else (-1 if v_ratio > 1.5 and e9 < e21 else 0)
        metrics["VOL_R"] = f"{v_ratio:.1f}x"

        obv = ta.obv(close, volume)
        obv_trend = obv.iloc[-1] > obv.iloc[-10]
        votes["OBV"] = 1 if obv_trend else -1
        metrics["OBV"] = "INFLOW" if obv_trend else "OUTFLOW"

        raw_score = sum(votes.values())
        max_possible = len(votes)
        score = round((raw_score / max_possible) * 50 + 50)
        score = max(0, min(100, score))

        if score >= 80: sig = "STRONG BUY"
        elif score >= 60: sig = "BUY"
        elif score >= 40: sig = "NEUTRAL"
        elif score >= 20: sig = "SELL"
        else: sig = "STRONG SELL"

        return {
            "signal": sig, "score": score, "price": close.iloc[-1],
            "votes": votes, "metrics": metrics,
            "total_bull": sum(1 for v in votes.values() if v > 0),
            "total_bear": sum(1 for v in votes.values() if v < 0)
        }
    except:
        return None

# ── helpers (unchanged) ────────────────────────────────────────────────────
SIGNAL_CLASS = { ... }   # Keep your original
SIGNAL_EMOJI = { ... }
SCORE_COLOR = { ... }

def vote_html(name: str, val: int, metric: str) -> str:
    # Your original vote_html stays the same
    ...

# ── masthead, sidebar, scanning logic (unchanged) ──────────────────────────
# [Keep all your masthead, sidebar, filtered, results, sorted_results code exactly as you had]

# ── tabs ───────────────────────────────────────────────────────────────────
tab_cards, tab_table, tab_detail = st.tabs(["⚡ Signal Cards", "📊 Full Table", "🔬 Deep Dive + Charts"])

# Signal Cards & Full Table stay 100% your code

with tab_detail:
    st.markdown('<div class="section-head">Deep Dive + Interactive Charts</div>', unsafe_allow_html=True)
    if sorted_results:
        selected_sym = st.selectbox("Select asset for detailed view", [sym.replace("-USD", "") for sym, _ in sorted_results])
        sym_key = next((s for s in results if s.replace("-USD", "") == selected_sym), None)
        if sym_key and sym_key in results:
            data = results[sym_key]
            p = data["primary"]
            
            dc1, dc2, dc3 = st.columns(3)
            dc1.metric("Price", f"${p['price']:,.4f}")
            dc2.metric("Alpha Score", f"{p['score']} / 100")
            dc3.metric("Signal", p["signal"])

            st.divider()

            # INTERACTIVE CHART
            st.subheader(f"{sym_key} — Price Action with Indicators")
            try:
                df_chart = yf.download(sym_key, period="6mo", interval="1d", progress=False)
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], 
                                           low=df_chart['Low'], close=df_chart['Close'], name="Price"))
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Close'].ewm(span=9).mean(), name="EMA 9", line=dict(color="#00f2ff")))
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Close'].ewm(span=21).mean(), name="EMA 21", line=dict(color="#ff00ff")))
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Close'].rolling(50).mean(), name="SMA 50", line=dict(color="#ffff00")))
                fig.update_layout(height=600, title=f"{sym_key} Technical View", template="plotly_dark", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            except:
                st.warning("Chart temporarily unavailable")

            # Your original indicator votes and timeframe confluence stay the same
            ...

# Footer (unchanged)
st.markdown(f"""
<div style="font-family:'Share Tech Mono',monospace;font-size:.62rem;color:#2a2a4a;text-align:center;margin-top:2rem;border-top:1px solid #0d0d1a;padding-top:1rem">
  ELITEFORGE CONFLUENCE ENGINE • REFRESHING IN {refresh}s • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)

time.sleep(refresh)
st.rerun()
