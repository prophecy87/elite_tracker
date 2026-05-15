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
import plotly.graph_objects as go

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
    --bg:        #03030a;
    --bg2:       #07070f;
    --bg3:       #0d0d1a;
    --border:    #1a1a2e;
    --accent:    #00f2ff;
    --purple:    #7b2fff;
    --green:     #00ff88;
    --red:       #ff3355;
    --yellow:    #ffcc00;
    --dim:       #3a3a5c;
    --text:      #c8d0ff;
    --text-dim:  #5a5a8a;
    --mono:      'Share Tech Mono', monospace;
    --head:      'Orbitron', sans-serif;
    --body:      'Rajdhani', sans-serif;
}

html, body, .stApp {
    background: var(--bg) !important;
    color: var(--text);
    font-family: var(--body);
}

/* hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 4rem; max-width: 1600px; }

/* ── masthead ── */
.masthead {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--border);
    padding-bottom: 1rem;
    margin-bottom: 1.8rem;
}
.masthead-title {
    font-family: var(--head);
    font-size: 1.7rem;
    font-weight: 900;
    letter-spacing: .12em;
    background: linear-gradient(90deg, var(--accent), var(--purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.masthead-sub {
    font-family: var(--mono);
    font-size: .7rem;
    color: var(--text-dim);
    margin-top: .2rem;
}
.live-badge {
    display: flex;
    align-items: center;
    gap: 7px;
    font-family: var(--mono);
    font-size: .72rem;
    color: var(--green);
    border: 1px solid rgba(0,255,136,.25);
    padding: 5px 12px;
    border-radius: 4px;
    background: rgba(0,255,136,.05);
}
.live-dot {
    width: 7px; height: 7px;
    background: var(--green);
    border-radius: 50%;
    animation: blink 1.4s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.2} }

/* ── score card ── */
.score-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 14px 16px;
    margin-bottom: 10px;
    position: relative;
    overflow: hidden;
}
.card-strong-buy::before  { content:''; position:absolute; top:0; left:0; right:0; height:2px; background: var(--green); }
.card-buy::before         { content:''; position:absolute; top:0; left:0; right:0; height:2px; background: #00cc66; }
.card-neutral::before     { content:''; position:absolute; top:0; left:0; right:0; height:2px; background: var(--yellow); }
.card-sell::before        { content:''; position:absolute; top:0; left:0; right:0; height:2px; background: #ff7744; }
.card-strong-sell::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background: var(--red); }

.card-symbol { font-family: var(--head); font-size: 1rem; color: var(--accent); letter-spacing: .06em; }
.card-name { font-family: var(--mono); font-size: .65rem; color: var(--text-dim); margin-bottom: 8px; }
.card-price { font-family: var(--mono); font-size: 1.1rem; color: #fff; font-weight: 700; }

.card-signal {
    font-family: var(--head); font-size: .72rem; font-weight: 700;
    padding: 3px 9px; border-radius: 3px; display: inline-block; margin-top: 6px;
}
.sig-strong-buy  { background: rgba(0,255,136,.15); color: var(--green);  border: 1px solid rgba(0,255,136,.4); }
.sig-buy         { background: rgba(0,204,102,.12); color: #00cc66;        border: 1px solid rgba(0,204,102,.35); }
.sig-neutral     { background: rgba(255,204,0,.1);  color: var(--yellow); border: 1px solid rgba(255,204,0,.3); }
.sig-sell        { background: rgba(255,119,68,.12);color: #ff7744;        border: 1px solid rgba(255,119,68,.35); }
.sig-strong-sell { background: rgba(255,51,85,.12); color: var(--red);     border: 1px solid rgba(255,51,85,.35); }

/* ── score bar ── */
.score-bar-wrap { margin-top: 10px; background: var(--bg3); border-radius: 3px; height: 5px; overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 3px; transition: width .6s ease; }
.score-label { font-family: var(--mono); font-size: .62rem; color: var(--text-dim); display: flex; justify-content: space-between; margin-top: 4px; }

/* ── indicator grid ── */
.ind-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; margin-top: 10px; }
.ind-item { font-family: var(--mono); font-size: .6rem; padding: 4px 6px; border-radius: 3px; display: flex; justify-content: space-between; background: var(--bg3); }
.ind-bull { color: var(--green); }
.ind-bear { color: var(--red); }
.ind-neut { color: var(--text-dim); }

/* ── stat strip ── */
.stat-strip { display: flex; gap: 10px; margin-bottom: 1.5rem; }
.stat-box { flex: 1; background: var(--bg2); border: 1px solid var(--border); border-radius: 5px; padding: 12px 16px; font-family: var(--mono); }
.stat-val { font-size: 1.4rem; font-weight: 700; color: #fff; }
.stat-lbl { font-size: .62rem; color: var(--text-dim); text-transform: uppercase; }

.section-head {
    font-family: var(--head); font-size: .75rem; letter-spacing: .15em; color: var(--text-dim);
    border-bottom: 1px solid var(--border); padding-bottom: 6px; margin: 1.5rem 0 1rem; text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# ── setup ──────────────────────────────────────────────────────────────────
WATCHLIST = {
    "BTC-USD": ("Bitcoin", "crypto"),
    "ETH-USD": ("Ethereum", "crypto"),
    "SOL-USD": ("Solana", "crypto"),
    "NVDA": ("NVIDIA", "equity"),
    "TSLA": ("Tesla", "equity"),
    "MSTR": ("MicroStrategy", "equity"),
}

TIMEFRAMES = {
    "1H": ("60m", "10d"),
    "4H": ("90m", "30d"),
    "1D": ("1d", "180d"),
    "1W": ("1wk", "2y"),
}

SIGNAL_CLASS = {
    "STRONG BUY":  ("strong-buy",  "card-strong-buy",  "sig-strong-buy"),
    "BUY":          ("buy",         "card-buy",         "sig-buy"),
    "NEUTRAL":      ("neutral",     "card-neutral",      "sig-neutral"),
    "SELL":         ("sell",        "card-sell",         "sig-sell"),
    "STRONG SELL": ("strong-sell", "card-strong-sell",  "sig-strong-sell"),
}
SCORE_COLOR = {"STRONG BUY":"#00ff88", "BUY":"#00cc66", "NEUTRAL":"#ffcc00", "SELL":"#ff7744", "STRONG SELL":"#ff3355"}
SIGNAL_EMOJI = {"STRONG BUY":"▲▲", "BUY":"▲", "NEUTRAL":"◆", "SELL":"▼", "STRONG SELL":"▼▼"}

def vote_html(name, val, metric):
    cls = "ind-bull" if val > 0 else ("ind-bear" if val < 0 else "ind-neut")
    return f'<div class="ind-item"><span class="{cls}">{name}</span><span style="color:#3a3a5c">{metric}</span></div>'

# ── logic ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def analyze(ticker, interval, period):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = [c[0].lower() for c in df.columns]
        else: df.columns = [c.lower() for c in df.columns]

        close = df["close"]
        votes, metrics = {}, {}
        
        rsi = ta.rsi(close, length=14).iloc[-1]
        metrics["RSI"] = f"{rsi:.1f}"
        votes["RSI"] = 1 if rsi < 35 else (-1 if rsi > 65 else 0)

        e9, e21 = ta.ema(close, 9).iloc[-1], ta.ema(close, 21).iloc[-1]
        votes["EMA_CROSS"] = 1 if e9 > e21 else -1
        metrics["EMA9/21"] = "▲" if e9 > e21 else "▼"

        raw_score = sum(votes.values())
        score = round((raw_score / len(votes)) * 50 + 50)
        
        if score >= 80: sig = "STRONG BUY"
        elif score >= 60: sig = "BUY"
        elif score >= 40: sig = "NEUTRAL"
        elif score >= 20: sig = "SELL"
        else: sig = "STRONG SELL"

        return {"signal": sig, "score": score, "price": close.iloc[-1], "votes": votes, "metrics": metrics}
    except: return None

# ── UI ─────────────────────────────────────────────────────────────────────
now = datetime.now().strftime("%H:%M:%S")
st.markdown(f'<div class="masthead"><div><div class="masthead-title">⚡ ELITEFORGE CONFLUENCE</div><div class="masthead-sub">9-INDICATOR ENGINE • {now}</div></div><div class="live-badge"><span class="live-dot"></span>LIVE</div></div>', unsafe_allow_html=True)

with st.sidebar:
    selected_tfs = st.multiselect("Timeframes", list(TIMEFRAMES.keys()), default=["1H", "1D"])
    primary_tf = st.selectbox("Primary", selected_tfs) if selected_tfs else "1D"
    refresh = st.slider("Refresh (s)", 30, 300, 60)

results = {}
for sym, (name, kind) in WATCHLIST.items():
    tf_data = {tf: analyze(sym, TIMEFRAMES[tf][0], TIMEFRAMES[tf][1]) for tf in selected_tfs}
    if tf_data.get(primary_tf):
        results[sym] = {"name": name, "primary": tf_data[primary_tf], "all_tf": tf_data}

# ── Tabs ───────────────────────────────────────────────────────────────────
tab_cards, tab_table, tab_detail = st.tabs(["⚡ Signal Cards", "📊 Full Table", "🔬 Deep Dive"])

with tab_cards:
    cols = st.columns(3)
    for i, (sym, data) in enumerate(results.items()):
        p = data["primary"]
        _, card_cls, sig_cls = SIGNAL_CLASS[p["signal"]]
        with cols[i % 3]:
            st.markdown(f"""
            <div class="score-card {card_cls}">
                <div class="card-symbol">{sym}</div>
                <div class="card-name">{data['name']}</div>
                <div style="display:flex;justify-content:space-between">
                    <div class="card-price">${p['price']:,.2f}</div>
                    <div class="card-signal {sig_cls}">{p['signal']}</div>
                </div>
                <div class="score-bar-wrap"><div class="score-bar-fill" style="width:{p['score']}%; background:{SCORE_COLOR[p['signal']]}"></div></div>
                <div class="ind-grid">{''.join(vote_html(k, v, p['metrics'][k]) for k, v in p['votes'].items())}</div>
            </div>
            """, unsafe_allow_html=True)

with tab_detail:
    if results:
        sel = st.selectbox("Select Asset", list(results.keys()))
        res = results[sel]
        
        # Interactive Chart logic
        df_chart = yf.download(sel, period="1mo", interval="1h", progress=False, auto_adjust=True)
        if isinstance(df_chart.columns, pd.MultiIndex): df_chart.columns = [c[0].lower() for c in df_chart.columns]
        else: df_chart.columns = [c.lower() for c in df_chart.columns]

        fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart['open'], high=df_chart['high'], low=df_chart['low'], close=df_chart['close'])])
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=400)
        st.plotly_chart(fig, use_container_width=True)

time.sleep(refresh)
st.rerun()
