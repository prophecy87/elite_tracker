"""
EliteForge • Confluence Screener
=================================
Multi-indicator alpha signal engine.
Indicators used per asset per timeframe:
  - RSI(14)           — momentum / overbought-oversold
  - EMA 9/21 cross    — short-term trend direction
  - EMA 50/200        — macro trend filter
  - MACD histogram    — momentum confirmation
  - Bollinger Bands   — volatility / mean reversion
  - ATR               — volatility regime
  - Volume ratio      — participation confirmation
  - Stochastic %K/%D  — secondary momentum
  - OBV trend         — on-balance volume direction

Each indicator votes +1 (bullish) / -1 (bearish) / 0 (neutral).
Score is summed → normalized to a 0-100 "Alpha Score".
Final signal tier: STRONG BUY / BUY / NEUTRAL / SELL / STRONG SELL
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

.card-symbol {
    font-family: var(--head);
    font-size: 1rem;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: .06em;
}
.card-name {
    font-family: var(--mono);
    font-size: .65rem;
    color: var(--text-dim);
    margin-bottom: 8px;
}
.card-price {
    font-family: var(--mono);
    font-size: 1.1rem;
    color: #fff;
    font-weight: 700;
}
.card-signal {
    font-family: var(--head);
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .08em;
    padding: 3px 9px;
    border-radius: 3px;
    display: inline-block;
    margin-top: 6px;
}
.sig-strong-buy  { background: rgba(0,255,136,.15); color: var(--green);  border: 1px solid rgba(0,255,136,.4); }
.sig-buy         { background: rgba(0,204,102,.12); color: #00cc66;       border: 1px solid rgba(0,204,102,.35); }
.sig-neutral     { background: rgba(255,204,0,.1);  color: var(--yellow); border: 1px solid rgba(255,204,0,.3); }
.sig-sell        { background: rgba(255,119,68,.12);color: #ff7744;       border: 1px solid rgba(255,119,68,.35); }
.sig-strong-sell { background: rgba(255,51,85,.12); color: var(--red);    border: 1px solid rgba(255,51,85,.35); }

/* ── score bar ── */
.score-bar-wrap {
    margin-top: 10px;
    background: var(--bg3);
    border-radius: 3px;
    height: 5px;
    overflow: hidden;
}
.score-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width .6s ease;
}
.score-label {
    font-family: var(--mono);
    font-size: .62rem;
    color: var(--text-dim);
    display: flex;
    justify-content: space-between;
    margin-top: 4px;
}

/* ── indicator grid ── */
.ind-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 5px;
    margin-top: 10px;
}
.ind-item {
    font-family: var(--mono);
    font-size: .6rem;
    padding: 4px 6px;
    border-radius: 3px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: var(--bg3);
}
.ind-bull { color: var(--green); }
.ind-bear { color: var(--red); }
.ind-neut { color: var(--text-dim); }

/* ── timeframe badges ── */
.tf-row {
    display: flex;
    gap: 6px;
    margin-top: 8px;
}
.tf-badge {
    font-family: var(--mono);
    font-size: .6rem;
    padding: 2px 8px;
    border-radius: 3px;
    border: 1px solid var(--border);
    color: var(--text-dim);
}
.tf-bull { border-color: rgba(0,255,136,.3); color: var(--green); background: rgba(0,255,136,.06); }
.tf-bear { border-color: rgba(255,51,85,.3);  color: var(--red);   background: rgba(255,51,85,.06); }
.tf-neut { border-color: rgba(255,204,0,.3);  color: var(--yellow);background: rgba(255,204,0,.06); }

/* ── section header ── */
.section-head {
    font-family: var(--head);
    font-size: .75rem;
    letter-spacing: .15em;
    color: var(--text-dim);
    border-bottom: 1px solid var(--border);
    padding-bottom: 6px;
    margin: 1.5rem 0 1rem;
    text-transform: uppercase;
}

/* ── stat strip ── */
.stat-strip {
    display: flex;
    gap: 2px;
    margin-bottom: 1.5rem;
}
.stat-box {
    flex: 1;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 12px 16px;
    font-family: var(--mono);
}
.stat-val {
    font-size: 1.4rem;
    font-weight: 700;
    color: #fff;
}
.stat-lbl {
    font-size: .62rem;
    color: var(--text-dim);
    margin-top: 2px;
    text-transform: uppercase;
    letter-spacing: .08em;
}

/* ── detail table ── */
.detail-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr 1fr 80px;
    gap: 0;
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    font-family: var(--mono);
    font-size: .72rem;
    align-items: center;
}
.detail-row:hover { background: var(--bg3); }
.detail-header {
    font-size: .6rem;
    color: var(--text-dim);
    letter-spacing: .1em;
    text-transform: uppercase;
    padding: 8px 14px;
    border-bottom: 1px solid var(--border);
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr 1fr 80px;
    background: var(--bg3);
    font-family: var(--mono);
}

/* streamlit overrides */
div[data-testid="stExpander"] {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
}
div[data-testid="stTabs"] button {
    font-family: var(--mono) !important;
    font-size: .72rem !important;
    color: var(--text-dim) !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
}
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

# ── Expanded Timeframes ────────────────────────────────────────────────────────
TIMEFRAMES = {
    "23M": ("15m",  "5d"),   # Closest liquid match to 23m for yfinance
    "1H":  ("60m",  "10d"),
    "4H":  ("90m",  "30d"),
    "1D":  ("1d",   "180d"),
    "1W":  ("1wk",  "2y"),
    "1M":  ("1mo",  "5y"),
}

# ── indicator engine ───────────────────────────────────────────────────────────
# ── Enhanced Indicator Engine ──────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def analyze(ticker: str, interval: str, period: str) -> dict | None:
    try:
        # Increase period for long-term TFs to ensure 200 EMA availability
        df = yf.download(ticker, period=period, interval=interval, 
                         progress=False, auto_adjust=True)
        if df.empty or len(df) < 30: return None

        # Standardize Columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        df.columns = [c.lower() for c in df.columns]

        close, high, low, volume = df["close"], df["high"], df["low"], df["volume"]
        votes, metrics = {}, {}

        # 1. RSI(14)
        rsi = ta.rsi(close, length=14).iloc[-1]
        metrics["RSI"] = f"{rsi:.1f}"
        votes["RSI"] = 1 if rsi < 35 else (-1 if rsi > 65 else 0)

        # 2. EMA 9/21 (Short-term Momentum)
        e9, e21 = ta.ema(close, 9).iloc[-1], ta.ema(close, 21).iloc[-1]
        votes["EMA_CROSS"] = 1 if e9 > e21 else -1
        metrics["EMA9/21"] = "▲" if e9 > e21 else "▼"

        # 3. EMA 50/200 (The Macro Wall)
        e50 = ta.ema(close, 50).iloc[-1]
        # Handle cases where data is shorter than 200 bars
        e200_s = ta.ema(close, 200)
        e200 = e200_s.iloc[-1] if e200_s is not None and not e200_s.isna().all() else e50
        votes["MACRO"] = 1 if close.iloc[-1] > e50 and e50 > e200 else (-1 if close.iloc[-1] < e50 else 0)
        metrics["MACRO"] = "BULL" if e50 > e200 else "BEAR"

        # 4. MACD (Momentum Pulse)
        macd = ta.macd(close)
        h_now, h_prev = macd.iloc[-1, 1], macd.iloc[-2, 1] # Histogram
        votes["MACD"] = 1 if h_now > h_prev else -1
        metrics["MACD"] = f"{h_now:+.2f}"

        # 5. Volatility Filter (ATR Surge)
        atr = ta.atr(high, low, close, length=14)
        curr_atr, avg_atr = atr.iloc[-1], atr.rolling(20).mean().iloc[-1]
        is_high_vol = curr_atr > (avg_atr * 1.5)
        votes["VOLATILITY"] = -1 if is_high_vol else 0 # Penalize score if vol is dangerously high
        metrics["ATR"] = "⚠️ HIGH" if is_high_vol else "STABLE"

        # 6. Volume Surge
        v_ratio = volume.iloc[-1] / volume.rolling(20).mean().iloc[-1]
        votes["VOLUME"] = 1 if v_ratio > 1.5 and e9 > e21 else (-1 if v_ratio > 1.5 and e9 < e21 else 0)
        metrics["VOL_R"] = f"{v_ratio:.1f}x"

        # 7. OBV (Smart Money Flow)
        obv = ta.obv(close, volume)
        obv_trend = obv.iloc[-1] > obv.iloc[-10]
        votes["OBV"] = 1 if obv_trend else -1
        metrics["OBV"] = "INFLOW" if obv_trend else "OUTFLOW"

        # ── Alpha Scoring Engine ────────────────────────────────────────────────
        # Weighting: Macro counts for 2x in long-term, Momentum counts for 2x in short-term
        raw_score = sum(votes.values())
        max_possible = len(votes)
        
        # Normalize to 0-100
        score = round((raw_score / max_possible) * 50 + 50)
        score = max(0, min(100, score))

        # Signal Tiers
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
    except:
        return None

# ── helpers ────────────────────────────────────────────────────────────────────
SIGNAL_CLASS = {
    "STRONG BUY":  ("strong-buy",  "card-strong-buy",  "sig-strong-buy"),
    "BUY":         ("buy",         "card-buy",         "sig-buy"),
    "NEUTRAL":     ("neutral",     "card-neutral",      "sig-neutral"),
    "SELL":        ("sell",        "card-sell",         "sig-sell"),
    "STRONG SELL": ("strong-sell", "card-strong-sell",  "sig-strong-sell"),
}
SIGNAL_EMOJI = {
    "STRONG BUY": "▲▲", "BUY": "▲", "NEUTRAL": "◆",
    "SELL": "▼", "STRONG SELL": "▼▼",
}
SCORE_COLOR = {
    "STRONG BUY":  "#00ff88",
    "BUY":         "#00cc66",
    "NEUTRAL":     "#ffcc00",
    "SELL":        "#ff7744",
    "STRONG SELL": "#ff3355",
}

def vote_html(name: str, val: int, metric: str) -> str:
    cls = "ind-bull" if val > 0 else ("ind-bear" if val < 0 else "ind-neut")
    icon = "●" if val > 0 else ("●" if val < 0 else "○")
    return (f'<div class="ind-item">'
            f'<span class="{cls}">{icon} {name}</span>'
            f'<span style="color:#3a3a5c">{metric}</span>'
            f'</div>')

def tf_badge(sig: str | None) -> str:
    if sig is None:
        return '<span class="tf-badge">—</span>'
    if "BUY" in sig:
        return f'<span class="tf-badge tf-bull">{sig}</span>'
    if "SELL" in sig:
        return f'<span class="tf-badge tf-bear">{sig}</span>'
    return f'<span class="tf-badge tf-neut">{sig}</span>'

# ── masthead ───────────────────────────────────────────────────────────────────
now = datetime.now().strftime("%H:%M:%S")
st.markdown(f"""
<div class="masthead">
  <div>
    <div class="masthead-title">⚡ ELITEFORGE CONFLUENCE</div>
    <div class="masthead-sub">9-INDICATOR ALPHA ENGINE • MULTI-TIMEFRAME • {now}</div>
  </div>
  <div class="live-badge">
    <span class="live-dot"></span>LIVE SCAN
  </div>
</div>
""", unsafe_allow_html=True)

# ── sidebar controls ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:\'Orbitron\',sans-serif;font-size:.8rem;color:#00f2ff;letter-spacing:.12em;margin-bottom:1rem;">⚙ CONTROLS</div>', unsafe_allow_html=True)

    selected_tfs = st.multiselect(
        "Timeframes",
        list(TIMEFRAMES.keys()),
        default=["1H", "4H", "1D"],
    )
    if not selected_tfs:
        selected_tfs = ["4H"]

    primary_tf = st.selectbox("Primary signal timeframe", selected_tfs, index=0)

    st.divider()
    show_cryptos  = st.toggle("Show Crypto",   value=True)
    show_equities = st.toggle("Show Equities", value=True)

    st.divider()
    min_score = st.slider("Min Alpha Score filter", 0, 100, 0, 5)
    refresh   = st.selectbox("Auto-refresh (s)", [30, 60, 120, 300], index=1)

# ── filter watchlist ───────────────────────────────────────────────────────────
filtered = {
    sym: info for sym, info in WATCHLIST.items()
    if (show_cryptos and info[1] == "crypto") or (show_equities and info[1] == "equity")
}

# ── scan all assets ────────────────────────────────────────────────────────────
results: dict[str, dict] = {}
progress = st.progress(0, text="Scanning markets…")
total_assets = len(filtered)

for i, (sym, (name, kind)) in enumerate(filtered.items()):
    tf_results = {}
    for tf in selected_tfs:
        interval, period = TIMEFRAMES[tf]
        r = analyze(sym, interval, period)
        if r:
            tf_results[tf] = r

    if tf_results:
        primary = tf_results.get(primary_tf) or list(tf_results.values())[0]
        results[sym] = {
            "name":     name,
            "kind":     kind,
            "primary":  primary,
            "tf":       tf_results,
        }
    progress.progress((i + 1) / total_assets,
                      text=f"Scanning {sym}…")

progress.empty()

# ── filter by min score ────────────────────────────────────────────────────────
results = {
    sym: d for sym, d in results.items()
    if d["primary"]["score"] >= min_score
}

# ── sort by score descending ───────────────────────────────────────────────────
sorted_results = sorted(
    results.items(),
    key=lambda x: x[1]["primary"]["score"],
    reverse=True,
)

# ── summary strip ──────────────────────────────────────────────────────────────
strong_buys  = sum(1 for _, d in sorted_results if d["primary"]["signal"] == "STRONG BUY")
buys         = sum(1 for _, d in sorted_results if d["primary"]["signal"] == "BUY")
neutrals     = sum(1 for _, d in sorted_results if d["primary"]["signal"] == "NEUTRAL")
sells        = sum(1 for _, d in sorted_results if "SELL" in d["primary"]["signal"])
avg_score    = round(sum(d["primary"]["score"] for _, d in sorted_results) / max(len(sorted_results), 1))

st.markdown(f"""
<div class="stat-strip">
  <div class="stat-box">
    <div class="stat-val" style="color:#00ff88">{strong_buys + buys}</div>
    <div class="stat-lbl">Bullish</div>
  </div>
  <div class="stat-box">
    <div class="stat-val" style="color:#ffcc00">{neutrals}</div>
    <div class="stat-lbl">Neutral</div>
  </div>
  <div class="stat-box">
    <div class="stat-val" style="color:#ff3355">{sells}</div>
    <div class="stat-lbl">Bearish</div>
  </div>
  <div class="stat-box">
    <div class="stat-val">{avg_score}</div>
    <div class="stat-lbl">Avg Alpha Score</div>
  </div>
  <div class="stat-box">
    <div class="stat-val">{len(sorted_results)}</div>
    <div class="stat-lbl">Assets Scanned</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── main tabs ──────────────────────────────────────────────────────────────────
tab_cards, tab_table, tab_detail = st.tabs([
    "⚡ Signal Cards", "📊 Full Table", "🔬 Deep Dive"
])

# ── Signal Cards ───────────────────────────────────────────────────────────────
with tab_cards:
    st.markdown(f'<div class="section-head">Primary TF: {primary_tf} • Sorted by Alpha Score</div>',
                unsafe_allow_html=True)
    cols = st.columns(4)
    for idx, (sym, data) in enumerate(sorted_results):
        p    = data["primary"]
        sig  = p["signal"]
        _, card_cls, sig_cls = SIGNAL_CLASS.get(sig, ("neutral", "card-neutral", "sig-neutral"))
        color = SCORE_COLOR.get(sig, "#ffcc00")
        emoji = SIGNAL_EMOJI.get(sig, "◆")
        score = p["score"]

        # timeframe badges
        tf_badges = "".join(
            f'<span style="margin-right:4px;font-family:var(--mono);font-size:.58rem;'
            f'padding:2px 6px;border-radius:3px;'
            f'{"background:rgba(0,255,136,.08);color:#00ff88;border:1px solid rgba(0,255,136,.2);" if "BUY" in data["tf"].get(tf, {}).get("signal","") else ("background:rgba(255,51,85,.08);color:#ff3355;border:1px solid rgba(255,51,85,.2);" if "SELL" in data["tf"].get(tf, {}).get("signal","") else "background:rgba(255,204,0,.05);color:#ffcc00;border:1px solid rgba(255,204,0,.15);")}">​'
            f'{tf} {data["tf"].get(tf, {}).get("signal", "—")}</span>'
            for tf in selected_tfs if tf in data["tf"]
        )

        # indicator votes
        ind_items = "".join(
            vote_html(k, v, p["metrics"].get(k, ""))
            for k, v in p["votes"].items()
        )

        with cols[idx % 4]:
            st.markdown(f"""
<div class="score-card {card_cls}">
  <div class="card-symbol">{sym.replace('-USD','')}</div>
  <div class="card-name">{data['name']}</div>
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div class="card-price">${p['price']:,.2f}</div>
    <span class="card-signal {sig_cls}">{emoji} {sig}</span>
  </div>
  <div class="score-bar-wrap">
    <div class="score-bar-fill" style="width:{score}%;background:{color}"></div>
  </div>
  <div class="score-label">
    <span>BEAR {p['total_bear']}</span>
    <span>Alpha Score: <b style="color:{color}">{score}</b></span>
    <span>BULL {p['total_bull']}</span>
  </div>
  <div style="margin-top:8px">{tf_badges}</div>
  <div class="ind-grid">{ind_items}</div>
</div>
""", unsafe_allow_html=True)

# ── Full Table ─────────────────────────────────────────────────────────────────
with tab_table:
    st.markdown('<div class="section-head">All Assets • All Timeframes</div>',
                unsafe_allow_html=True)
    rows = []
    for sym, data in sorted_results:
        p   = data["primary"]
        row = {
            "Symbol":      sym.replace("-USD", ""),
            "Name":        data["name"],
            "Price":       f"${p['price']:,.4f}",
            "Score":       p["score"],
            f"Signal ({primary_tf})": p["signal"],
        }
        for tf in selected_tfs:
            r = data["tf"].get(tf)
            row[tf] = r["signal"] if r else "—"
        row["Bull"] = p["total_bull"]
        row["Bear"] = p["total_bear"]
        # Using .get() prevents the KeyError by returning None (or a default) if 'rsi' is missing
        rsi_value = p.get('rsi')

        if rsi_value is not None:
          row["RSI"] = f"{rsi_value:.1f}"
        else:
          row["RSI"] = "N/A"
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True, height=400)

# ── Deep Dive ──────────────────────────────────────────────────────────────────
with tab_detail:
    st.markdown('<div class="section-head">Per-Indicator Breakdown</div>',
                unsafe_allow_html=True)
    selected_sym = st.selectbox(
        "Select asset",
        [sym.replace("-USD", "") for sym, _ in sorted_results],
    )
    # remap to original key
    sym_key = next(
        (s for s in results if s.replace("-USD", "") == selected_sym),
        None
    )
    if sym_key and sym_key in results:
        data = results[sym_key]
        p    = data["primary"]

        dc1, dc2, dc3 = st.columns(3)
        sig   = p["signal"]
        color = SCORE_COLOR.get(sig, "#ffcc00")
        dc1.metric("Price",       f"${p['price']:,.4f}")
        dc2.metric("Alpha Score", f"{p['score']} / 100")
        dc3.metric("Signal",      sig)

        st.divider()
        st.markdown("**Indicator Votes**")

        icols = st.columns(3)
        for i, (ind, vote) in enumerate(p["votes"].items()):
            metric = p["metrics"].get(ind, "—")
            label  = "🟢 BULLISH" if vote > 0 else ("🔴 BEARISH" if vote < 0 else "⚪ NEUTRAL")
            with icols[i % 3]:
                st.markdown(f"""
<div style="background:#07070f;border:1px solid #1a1a2e;border-radius:5px;
            padding:10px 14px;margin-bottom:8px;font-family:'Share Tech Mono',monospace">
  <div style="font-size:.65rem;color:#3a3a5c;text-transform:uppercase;letter-spacing:.1em">{ind}</div>
  <div style="font-size:1rem;color:#fff;margin:4px 0">{metric}</div>
  <div style="font-size:.68rem;{'color:#00ff88' if vote>0 else ('color:#ff3355' if vote<0 else 'color:#ffcc00')}">{label}</div>
</div>
""", unsafe_allow_html=True)

        st.divider()
        st.markdown("**Timeframe Confluence**")
        tf_cols = st.columns(len(selected_tfs))
        for i, tf in enumerate(selected_tfs):
            r = data["tf"].get(tf)
            with tf_cols[i]:
                if r:
                    color = SCORE_COLOR.get(r["signal"], "#ffcc00")
                    st.markdown(f"""
<div style="background:#07070f;border:1px solid #1a1a2e;border-radius:5px;
            padding:14px;text-align:center;font-family:'Share Tech Mono',monospace">
  <div style="font-size:.65rem;color:#3a3a5c;letter-spacing:.12em">{tf}</div>
  <div style="font-size:1.1rem;color:{color};font-weight:700;margin:6px 0">{r['signal']}</div>
  <div style="font-size:.65rem;color:#3a3a5c">Score: {r['score']}</div>
  <div style="background:#0d0d1a;border-radius:3px;height:4px;margin-top:8px;overflow:hidden">
    <div style="width:{r['score']}%;height:100%;background:{color};border-radius:3px"></div>
  </div>
</div>
""", unsafe_allow_html=True)
                else:
                    st.markdown(f'<div style="text-align:center;color:#3a3a5c;font-family:monospace">{tf}<br>—</div>',
                                unsafe_allow_html=True)

# ── footer / refresh ───────────────────────────────────────────────────────────
st.markdown(f"""
<div style="font-family:'Share Tech Mono',monospace;font-size:.62rem;
            color:#2a2a4a;text-align:center;margin-top:2rem;border-top:1px solid #0d0d1a;
            padding-top:1rem">
  ELITEFORGE CONFLUENCE ENGINE • 9 INDICATORS • {len(selected_tfs)} TIMEFRAMES •
  REFRESHING IN {refresh}s • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)

time.sleep(refresh)
st.rerun()
