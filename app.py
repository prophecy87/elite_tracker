import pandas as pd
import yfinance as yf
import streamlit as st
import time
import pandas_ta as ta 
import random
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# ====================== 2026 QUANT UI ======================
st.set_page_config(page_title="EliteForge v31 • Quant Lab", layout="wide", page_icon="🧪")

# Modern 2026 Glassmorphism Styling
st.markdown("""
<style>
    .stApp { background-color: #03030b; color: #f0f0ff; }
    .challenge-card { 
        background: linear-gradient(135deg, #0f0f2d 0%, #050510 100%);
        padding: 25px; border-radius: 20px; border: 1px solid #3a3a5f;
        text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .status-glow { color: #00ffcc; text-shadow: 0 0 10px #00ffcc; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# ====================== CHALLENGE SELECTOR ======================
st.sidebar.markdown("### 🏆 ACTIVE CHALLENGE")
level = st.sidebar.segmented_control(
    "Select Initial Capital",
    options=["$100", "$1,000", "$10,000", "$100,000"],
    default="$1,000"
)

# Dynamic Risk Logic based on Level
capital_map = {"$100": 100, "$1,000": 1000, "$10,000": 10000, "$100,000": 100000}
target_capital = capital_map[level]

# Adjust Strategy Aggression based on Capital
if target_capital <= 100:
    risk_mode = "SNIPER (High Precision, Low Freq)"
    max_drawdown = 0.05 # 5% max risk
elif target_capital >= 10000:
    risk_mode = "WHALE (Broad Diversification)"
    max_drawdown = 0.15 
else:
    risk_mode = "SCALPER (Standard Aggression)"
    max_drawdown = 0.10

# ====================== CORE APP ======================
st.markdown(f'<h1 style="text-align:center;">ELITEFORGE v31 • {level} CHALLENGE</h1>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="challenge-card"><h4>TARGET</h4><h2 class="status-glow">{level}</h2></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="challenge-card"><h4>RISK PROFILE</h4><h2 style="color:#ffcc00;">{risk_mode.split()[0]}</h2></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="challenge-card"><h4>MAX DD LIMIT</h4><h2 style="color:#ff4b4b;">{max_drawdown*100}%</h2></div>', unsafe_allow_html=True)

# ====================== QUANT LOGIC ======================
def get_position_size(price, current_equity):
    """Smart Sizing: Prevents over-leveraging on small accounts"""
    risk_amount = current_equity * 0.02 # Risk 2% per trade
    qty = risk_amount / price
    if target_capital < 500:
        return round(qty, 4) # Fractional for small accounts
    return int(qty) if qty > 1 else round(qty, 2)

# --- TRADING VIEW TAB ---
tab1, tab2 = st.tabs(["🏛️ Terminal", "📉 Analytics"])

with tab1:
    # Simulating the Pulse
    st.write("---")
    st.subheader("📡 Live Market Intelligence")
    tickers = ["BTC/USD", "NVDA", "AAPL", "SOL/USD"]
    
    # Render indicators
    for t in tickers:
        col_a, col_b, col_c, col_d = st.columns([1, 1, 1, 2])
        col_a.write(f"**{t}**")
        price = random.uniform(100, 60000)
        col_b.write(f"${price:,.2f}")
        
        # Sizing Logic visualization
        size = get_position_size(price, target_capital)
        col_c.write(f"Size: {size}")
        
        sig = "BUY" if random.random() > 0.8 else "HOLD"
        color = "#00ffcc" if sig == "BUY" else "#ffffff"
        col_d.markdown(f'<span style="color:{color}; font-weight:bold;">{sig} SIGNAL DETECTED</span>', unsafe_allow_html=True)

with tab2:
    st.info(f"Analytics Engine calibrating for {level} liquidity depth...")
    # Add a mock equity curve comparison
    chart_data = pd.DataFrame({
        'Day': range(1, 11),
        'Performance': [target_capital * (1 + (random.uniform(-0.02, 0.05))) for _ in range(10)]
    })
    st.line_chart(chart_data, x='Day', y='Performance')

time.sleep(30)
st.rerun()
