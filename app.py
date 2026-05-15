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
html, body, .stApp {
    background: var(--bg) !important;
    color: var(--text);
    font-family: var(--body);
}
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
/* Rest of your beautiful CSS stays exactly the same */
.score-card, .score-bar-wrap, .ind-grid, .tf-row, .section-head, .stat-strip { /* ... your existing styles ... */ }
</style>
""", unsafe_allow_html=True)

# ── watchlist & timeframes (unchanged) ─────────────────────────────────────
WATCHLIST = { ... }  # Keep your exact WATCHLIST
TIMEFRAMES = { ... } # Keep your exact TIMEFRAMES

# ── indicator engine (unchanged) ───────────────────────────────────────────
# [Your entire analyze() function stays 100% the same]

# ── helpers (unchanged) ────────────────────────────────────────────────────
# [SIGNAL_CLASS, SIGNAL_EMOJI, SCORE_COLOR, vote_html stay the same]

# ── masthead (unchanged) ───────────────────────────────────────────────────
# [Your masthead code stays the same]

# ── sidebar (unchanged) ────────────────────────────────────────────────────
# [Your sidebar stays exactly the same]

# ── scan all assets (unchanged) ────────────────────────────────────────────
# [Your scanning logic stays the same]

# ── summary strip (unchanged) ──────────────────────────────────────────────
# [Your summary strip stays the same]

# ── main tabs ──────────────────────────────────────────────────────────────
tab_cards, tab_table, tab_detail = st.tabs([
    "⚡ Signal Cards", "📊 Full Table", "🔬 Deep Dive + Charts"
])

# ── Signal Cards (unchanged) ───────────────────────────────────────────────
with tab_cards:
    # Your existing card code stays exactly the same
    ...

# ── Full Table (unchanged) ─────────────────────────────────────────────────
with tab_table:
    # Your existing table code stays exactly the same
    ...

# ── DEEP DIVE WITH CHARTS (Enhanced) ───────────────────────────────────────
with tab_detail:
    st.markdown('<div class="section-head">Deep Dive + Interactive Charts</div>', unsafe_allow_html=True)
    
    if sorted_results:
        selected_sym = st.selectbox("Select asset for detailed view", 
                                   [sym.replace("-USD", "") for sym, _ in sorted_results])
        sym_key = next((s for s in results if s.replace("-USD", "") == selected_sym), None)
        
        if sym_key and sym_key in results:
            data = results[sym_key]
            p = data["primary"]
            
            # Metrics row
            dc1, dc2, dc3 = st.columns(3)
            dc1.metric("Current Price", f"${p['price']:,.4f}" if "USD" in sym_key else f"${p['price']:,.2f}")
            dc2.metric("Alpha Score", f"{p['score']}/100", delta=None)
            dc3.metric("Primary Signal", p["signal"])
            
            st.divider()
            
            # INTERACTIVE CHART
            st.subheader("Price Action + Key Indicators")
            try:
                df = yf.download(sym_key, period="6mo", interval="1d", progress=False)
                fig = go.Figure()
                
                # Candlestick
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                           low=df['Low'], close=df['Close'], name="Price"))
                
                # EMAs
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'].ewm(span=9).mean(), 
                                       name="EMA 9", line=dict(color="#00f2ff", width=2)))
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'].ewm(span=21).mean(), 
                                       name="EMA 21", line=dict(color="#ff00ff", width=2)))
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'].rolling(50).mean(), 
                                       name="SMA 50", line=dict(color="#ffff00", width=2)))
                
                # Bollinger Bands
                bb_mid = df['Close'].rolling(20).mean()
                bb_std = df['Close'].rolling(20).std()
                fig.add_trace(go.Scatter(x=df.index, y=bb_mid + 2*bb_std, 
                                       name="BB Upper", line=dict(color="#ff3355", dash="dash")))
                fig.add_trace(go.Scatter(x=df.index, y=bb_mid - 2*bb_std, 
                                       name="BB Lower", line=dict(color="#00ff88", dash="dash")))
                
                fig.update_layout(height=600, title=f"{sym_key} — Multi-Timeframe View", 
                                xaxis_rangeslider_visible=False, template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            except:
                st.warning("Chart data temporarily unavailable")
            
            st.divider()
            st.markdown("**Indicator Votes**")
            # Your existing indicator grid code stays the same
            ...

# Footer (unchanged)
st.markdown(f"""
<div style="font-family:'Share Tech Mono',monospace;font-size:.62rem;color:#2a2a4a;
            text-align:center;margin-top:2rem;border-top:1px solid #0d0d1a;padding-top:1rem">
  ELITEFORGE CONFLUENCE ENGINE • REFRESHING IN {refresh}s • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)

time.sleep(refresh)
st.rerun()
