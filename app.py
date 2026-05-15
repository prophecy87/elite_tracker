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

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 4rem; max-width: 1600px; }

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

.score-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 14px 16px;
    margin-bottom: 10px;
    position: relative;
    overflow: hidden;
    transition: border-color .2s;
}
.score-card:hover { border-color: var(--dim); }
.score-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.card-strong-buy::before  { background: var(--green); }
.card-buy::before         { background: #00cc66; }
.card-neutral::before     { background: var(--yellow); }
.card-sell::before        { background: #ff7744; }
.card-strong-sell::before { background: var(--red); }

.card-symbol { font-family: var(--head); font-size: 1rem; font-weight: 700; color: var(--accent); letter-spacing: .06em; }
.card-name { font-family: var(--mono); font-size: .65rem; color: var(--text-dim); margin-bottom: 8px; }
.card-price { font-family: var(--mono); font-size: 1.1rem; color: #fff; font-weight: 700; }
.card-signal { font-family: var(--head); font-size: .72rem; font-weight: 700; padding: 3px 9px; border-radius: 3px; display: inline-block; margin-top: 6px; }

.sig-strong-buy  { background: rgba(0,255,136,.15); color: var(--green);  border: 1px solid rgba(0,255,136,.4); }
.sig-buy         { background: rgba(0,204,102,.12); color: #00cc66;       border: 1px solid rgba(0,204,102,.35); }
.sig-neutral     { background: rgba(255,204,0,.1);  color: var(--yellow); border: 1px solid rgba(255,204,0,.3); }
.sig-sell        { background: rgba(255,119,68,.12);color: #ff7744;       border: 1px solid rgba(255,119,68,.35); }
.sig-strong-sell { background: rgba(255,51,85,.12); color: var(--red);    border: 1px solid rgba(255,51,85,.35); }

.score-bar-wrap { margin-top: 10px; background: var(--bg3); border-radius: 3px; height: 5px; overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 3px; transition: width .6s ease; }
.score-label { font-family: var(--mono); font-size: .62rem; color: var(--text-dim); display: flex; justify-content: space-between; margin-top: 4px; }

.ind-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; margin-top: 10px; }
.ind-item { font-family: var(--mono); font-size: .6rem; padding: 4px 6px; border-radius: 3px; display: flex; justify-content: space-between; align-items: center; background: var(--bg3); }
.ind-bull { color: var(--green); }
.ind-bear { color: var(--red); }
.ind-neut { color: var(--text-dim); }

.section-head { font-family: var(--head); font-size: .75rem; letter-spacing: .15em; color: var(--text-dim); border-bottom: 1px solid var(--border); padding-bottom: 6px; margin: 1.5rem 0 1rem; text-transform: uppercase; }

.stat-strip { display: flex; gap: 2px; margin-bottom: 1.5rem; }
.stat-box { flex: 1; background: var(--bg2); border: 1px solid var(--border); border-radius: 5px; padding: 12px 16px; font-family: var(--mono); }
.stat-val { font-size: 1.4rem; font-weight: 700; color: #fff; }
.stat-lbl { font-size: .62rem; color: var(--text-dim); margin-top: 2px; text-transform: uppercase; }

div[data-testid="stExpander"] { background: var(--bg2) !important; border: 1px solid var(--border) !important; border-radius: 6px !important; }
</style>
""", unsafe_allow_html=True)

# ── watchlist ──────────────────────────────────────────────────────────────────
WATCHLIST = {
    "BTC-USD":  ("Bitcoin",       "crypto"),
    "ETH-USD":  ("Ethereum",      "crypto"),
    "SOL-USD":  ("Solana",        "crypto"),
    "NVDA":     ("NVIDIA",        "equity"),
    "TSLA":     ("Tesla",         "equity"),
    "MSTR":     ("MicroStrategy", "equity"),
    "AAPL":     ("Apple",         "equity"),
    "COIN":     ("Coinbase",      "equity"),
}

# ── Timeframes (Updated to include Weekly and Monthly) ─────────────────────────
TIMEFRAMES = {
    "23M": ("15m",  "5d"),
    "1H":  ("60m",  "10d"),
    "4H":  ("90m",  "30d"),
    "1D":  ("1d",   "180d"),
    "1W":  ("1wk",  "2y"),
    "1M":  ("1mo",  "5y"),
}

# ── indicator engine ───────────────────────────────────────────────────────────
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

        # 1. RSI(14)
        rsi_series = ta.rsi(close, length=14)
        rsi = rsi_series.iloc[-1]
        metrics["RSI"] = f"{rsi:.1f}"
        votes["RSI"] = 1 if rsi < 35 else (-1 if rsi > 65 else 0)

        # 2. EMA 9/21
        e9, e21 = ta.ema(close, 9).iloc[-1], ta.ema(close, 21).iloc[-1]
        votes["EMA_CROSS"] = 1 if e9 > e21 else -1
        metrics["EMA9/21"] = "▲" if e9 > e21 else "▼"

        # 3. EMA 50/200
        e50 = ta.ema(close, 50).iloc[-1]
        e200_s = ta.ema(close, 200)
        e200 = e200_s.iloc[-1] if e200_s is not None and not e200_s.isna().all() else e50
        votes["MACRO"] = 1 if close.iloc[-1] > e50 and e50 > e200 else (-1 if close.iloc[-1] < e50 else 0)
        metrics["MACRO"] = "BULL" if e50 > e200 else "BEAR"

        # 4. MACD
        macd = ta.macd(close)
        h_now, h_prev = macd.iloc[-1, 1], macd.iloc[-2, 1]
        votes["MACD"] = 1 if h_now > h_prev else -1
        metrics["MACD"] = f"{h_now:+.2f}"

        # 5. Volatility (ATR)
        atr = ta.atr(high, low, close, length=14)
        curr_atr, avg_atr = atr.iloc[-1], atr.rolling(20).mean().iloc[-1]
        is_high_vol = curr_atr > (avg_atr * 1.5)
        votes["VOLATILITY"] = -1 if is_high_vol else 0
        metrics["ATR"] = "⚠️ HIGH" if is_high_vol else "STABLE"

        # 6. Volume
        v_ratio = volume.iloc[-1] / volume.rolling(20).mean().iloc[-1]
        votes["VOLUME"] = 1 if v_ratio > 1.5 and e9 > e21 else (-1 if v_ratio > 1.5 and e9 < e21 else 0)
        metrics["VOL_R"] = f"{v_ratio:.1f}x"

        # 7. OBV
        obv = ta.obv(close, volume)
        obv_trend = obv.iloc[-1] > obv.iloc[-10]
        votes["OBV"] = 1 if obv_trend else -1
        metrics["OBV"] = "INFLOW" if obv_trend else "OUTFLOW"

        # ── Scoring ──
        raw_score = sum(votes.values())
        max_possible = len(votes)
        score = round((raw_score / max_possible) * 50 + 50)
        score = max(0, min(100, score))

        if score >= 80:   sig = "STRONG BUY"
        elif score >= 60: sig = "BUY"
        elif score >= 40: sig = "NEUTRAL"
        elif score >= 20: sig = "SELL"
        else:             sig = "STRONG SELL"

        return {
            "signal": sig, "score": score, "price": close.iloc[-1],
            "votes": votes, "metrics": metrics,
            "total_bull": sum(1 for v in votes.values() if v > 0),
            "total_bear": sum(1 for v in votes.values() if v < 0)
        }
    except Exception:
        return None

# ── UI Helpers ──
SIGNAL_CLASS = {
    "STRONG BUY":  ("strong-buy",  "card-strong-buy",  "sig-strong-buy"),
    "BUY":          ("buy",         "card-buy",         "sig-buy"),
    "NEUTRAL":      ("neutral",     "card-neutral",      "sig-neutral"),
    "SELL":         ("sell",        "card-sell",         "sig-sell"),
    "STRONG SELL": ("strong-sell", "card-strong-sell",  "sig-strong-sell"),
}
SIGNAL_EMOJI = {"STRONG BUY": "▲▲", "BUY": "▲", "NEUTRAL": "◆", "SELL": "▼", "STRONG SELL": "▼▼"}
SCORE_COLOR = {"STRONG BUY": "#00ff88", "BUY": "#00cc66", "NEUTRAL": "#ffcc00", "SELL": "#ff7744", "STRONG SELL": "#ff3355"}

def vote_html(name: str, val: int, metric: str) -> str:
    cls = "ind-bull" if val > 0 else ("ind-bear" if val < 0 else "ind-neut")
    icon = "●" if val != 0 else "○"
    return (f'<div class="ind-item">'
            f'<span class="{cls}">{icon} {name}</span>'
            f'<span style="color:#3a3a5c">{metric}</span>'
            f'</div>')

# ── Main UI Logic ──
now = datetime.now().strftime("%H:%M:%S")
st.markdown(f"""
<div class="masthead">
  <div>
    <div class="masthead-title">⚡ ELITEFORGE CONFLUENCE</div>
    <div class="masthead-sub">ALPHA ENGINE • WEEKLY/MONTHLY ACTIVE • {now}</div>
  </div>
  <div class="live-badge"><span class="live-dot"></span>LIVE SCAN</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div style="font-family:\'Orbitron\',sans-serif;font-size:.8rem;color:#00f2ff;margin-bottom:1rem;">⚙ CONTROLS</div>', unsafe_allow_html=True)
    selected_tfs = st.multiselect("Timeframes", list(TIMEFRAMES.keys()), default=["1D", "1W", "1M"])
    primary_tf = st.selectbox("Primary Signal", selected_tfs, index=0)
    show_cryptos = st.toggle("Crypto", value=True)
    show_equities = st.toggle("Equities", value=True)
    refresh = st.selectbox("Refresh (s)", [30, 60, 300], index=1)

filtered = {s: i for s, i in WATCHLIST.items() if (show_cryptos and i[1] == "crypto") or (show_equities and i[1] == "equity")}

results = {}
progress = st.progress(0, text="Scanning...")
for i, (sym, (name, kind)) in enumerate(filtered.items()):
    tf_results = {tf: analyze(sym, *TIMEFRAMES[tf]) for tf in selected_tfs}
    tf_results = {k: v for k, v in tf_results.items() if v}
    if tf_results:
        results[sym] = {"name": name, "kind": kind, "primary": tf_results.get(primary_tf) or list(tf_results.values())[0], "tf": tf_results}
    progress.progress((i + 1) / len(filtered))
progress.empty()

sorted_results = sorted(results.items(), key=lambda x: x[1]["primary"]["score"], reverse=True)

# ── Summary ──
if sorted_results:
    avg_score = round(sum(d["primary"]["score"] for _, d in sorted_results) / len(sorted_results))
    st.markdown(f"""
    <div class="stat-strip">
      <div class="stat-box"><div class="stat-val">{avg_score}</div><div class="stat-lbl">Avg Alpha</div></div>
      <div class="stat-box"><div class="stat-val">{len(sorted_results)}</div><div class="stat-lbl">Assets</div></div>
    </div>
    """, unsafe_allow_html=True)

tab_cards, tab_table = st.tabs(["⚡ Cards", "📊 Table"])

with tab_cards:
    cols = st.columns(4)
    for idx, (sym, data) in enumerate(sorted_results):
        p = data["primary"]
        sig = p["signal"]
        color = SCORE_COLOR.get(sig, "#ffcc00")
        ind_items = "".join(vote_html(k, v, p["metrics"].get(k, "")) for k, v in p["votes"].items())
        
        with cols[idx % 4]:
            st.markdown(f"""
            <div class="score-card {SIGNAL_CLASS.get(sig)[1]}">
              <div class="card-symbol">{sym.replace('-USD','')}</div>
              <div class="card-price">${p['price']:,.2f}</div>
              <div class="score-bar-wrap"><div class="score-bar-fill" style="width:{p['score']}%;background:{color}"></div></div>
              <div class="score-label"><span>Alpha: {p['score']}</span><span>{sig}</span></div>
              <div class="ind-grid">{ind_items}</div>
            </div>
            """, unsafe_allow_html=True)

with tab_table:
    table_data = []
    for sym, data in sorted_results:
        p = data["primary"]
        row = {
            "Symbol": sym.replace("-USD", ""),
            "Price": f"${p['price']:,.2f}",
            "Alpha": p["score"],
            "RSI": p["metrics"].get("RSI", "N/A"),  # Corrected RSI access
            "Primary Signal": p["signal"]
        }
        for tf in selected_tfs:
            row[tf] = data["tf"].get(tf, {}).get("signal", "—")
        table_data.append(row)
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

time.sleep(refresh)
st.rerun()
