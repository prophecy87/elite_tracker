import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime
import time
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass, QueryOrderStatus

# ====================== PAGE SETUP ======================
st.set_page_config(page_title="EliteForge v25", layout="wide", page_icon="🔥")
st.title("🔥 EliteForge • Hybrid Engine")

# ====================== SESSION STATE (Persistence) ======================
if 'bot_active' not in st.session_state:
    st.session_state.bot_active = False
if 'last_trade_time' not in st.session_state:
    st.session_state.last_trade_time = {}

# ====================== ALPACA CONNECT ======================
@st.cache_resource
def connect_alpaca():
    try:
        return TradingClient(st.secrets["alpaca"]["api_key"], st.secrets["alpaca"]["secret_key"], paper=True)
    except Exception as e:
        st.error(f"Alpaca Connection Error: {e}")
        return None

trade_client = connect_alpaca()

# ====================== SIDEBAR CONTROLS ======================
with st.sidebar:
    st.header("🕹️ Control Panel")
    
    # THE MASTER PAUSE SWITCH
    if st.session_state.bot_active:
        if st.button("🛑 STOP TRADING BOT", use_container_width=True, type="primary"):
            st.session_state.bot_active = False
            st.rerun()
    else:
        if st.button("▶️ START TRADING BOT", use_container_width=True):
            st.session_state.bot_active = True
            st.rerun()

    status_color = "green" if st.session_state.bot_active else "red"
    st.markdown(f"Status: :{status_color}[{'RUNNING' if st.session_state.bot_active else 'PAUSED'}]")
    
    st.divider()
    strategy_mode = st.selectbox("🎛️ Risk Profile", ["Safe", "Neutral", "Aggressive"], index=1)
    
    configs = {
        "Safe": {"risk": 0.02, "tp": 0.02, "sl": 0.01},
        "Neutral": {"risk": 0.04, "tp": 0.05, "sl": 0.02},
        "Aggressive": {"risk": 0.08, "tp": 0.10, "sl": 0.04}
    }
    conf = configs[strategy_mode]

# ====================== LOGIC & ANALYSIS ======================
def analyze_ticker(ticker):
    try:
        yf_ticker = ticker.replace("/", "-")
        df = yf.download(yf_ticker, period="5d", interval="15m", progress=False)
        if df.empty: return {"error": "No Data"}
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        close_series = df['Close'].squeeze()
        current_price = float(close_series.values[-1])
        ma20 = float(close_series.rolling(20).mean().values[-1])
        diff = (current_price - ma20) / ma20
        
        # Entry Logic
        action = "BUY" if diff < -0.015 else "HOLD"
        return {"action": action, "price": current_price, "diff": diff, "ma": ma20, "error": None}
    except Exception as e:
        return {"error": str(e)}

def execute_trade(ticker, analysis):
    if not st.session_state.bot_active:
        return False
    
    try:
        symbol = ticker.replace("/", "")
        acc = trade_client.get_account()
        qty = (float(acc.cash) * conf['risk']) / analysis['price']
        qty = round(qty, 4) if "/" in ticker else int(qty)
        
        if qty > 0:
            order = MarketOrderRequest(
                symbol=symbol, qty=qty, side=OrderSide.BUY,
                time_in_force=TimeInForce.GTC, order_class=OrderClass.BRACKET,
                take_profit=TakeProfitRequest(limit_price=round(analysis['price'] * (1 + conf['tp']), 2)),
                stop_loss=StopLossRequest(stop_price=round(analysis['price'] * (1 - conf['sl']), 2))
            )
            trade_client.submit_order(order)
            return True
    except Exception as e:
        st.sidebar.error(f"Trade Failed: {e}")
    return False

# ====================== UI TABS ======================
tab_monitor, tab_positions, tab_history = st.tabs(["📊 Live Scanner", "💼 Active Positions", "📜 Order Ledger"])

with tab_monitor:
    st.subheader(f"📡 Market Scan • {datetime.now().strftime('%H:%M:%S')}")
    watchlist = ["BTC/USD", "ETH/USD", "SOL/USD", "NVDA", "TSLA", "AAPL"]
    cols = st.columns(3)
    
    for i, ticker in enumerate(watchlist):
        with cols[i % 3]:
            res = analyze_ticker(ticker)
            if res.get("error"):
                st.error(f"{ticker}: {res['error']}")
            else:
                # Color code based on signal
                delta_color = "inverse" if res['action'] == "BUY" else "normal"
                st.metric(ticker, f"${res['price']:,.2f}", f"{res['diff']:.2%}", delta_color=delta_color)
                
                # Logic for Trade Execution
                if res['action'] == "BUY" and st.session_state.bot_active:
                    if execute_trade(ticker, res):
                        st.toast(f"✅ Executed Buy for {ticker}", icon="🚀")
                
                # Potential Entry Insight
                st.caption(f"Target Entry: < ${res['ma'] * 0.985:,.2f}")

with tab_positions:
    st.subheader("💼 Real-Time Portfolio")
    try:
        positions = trade_client.get_all_positions()
        if positions:
            pos_df = pd.DataFrame([{
                "Symbol": p.symbol,
                "Qty": p.qty,
                "Entry": f"${float(p.avg_entry_price):,.2f}",
                "Current": f"${float(p.current_price):,.2f}",
                "PnL (%)": f"{(float(p.unrealized_plpc) * 100):.2f}%",
                "Unrealized PnL ($)": f"${float(p.unrealized_pl):,.2f}"
            } for p in positions])
            st.table(pos_df)
        else:
            st.info("No active positions.")
    except:
        st.warning("Could not sync positions.")

with tab_history:
    st.subheader("📜 Recent Activity")
    try:
        orders = trade_client.get_orders(GetOrdersRequest(status=QueryOrderStatus.ALL, limit=10))
        if orders:
            order_list = []
            for o in orders:
                order_list.append({
                    "Date": o.created_at.strftime("%m-%d %H:%M"),
                    "Asset": o.symbol,
                    "Side": o.side,
                    "Qty": o.qty,
                    "Status": o.status
                })
            st.dataframe(pd.DataFrame(order_list), use_container_width=True)
    except:
        st.write("Order history temporarily unavailable.")

# ====================== GLOBAL METRICS BAR ======================
st.divider()
try:
    acc = trade_client.get_account()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Equity", f"${float(acc.equity):,.2f}")
    m2.metric("Buying Power", f"${float(acc.buying_power):,.2f}")
    
    # Calculate Day's PnL
    day_pnl = float(acc.equity) - float(acc.last_equity)
    pnl_color = "normal" if day_pnl >= 0 else "inverse"
    m3.metric("Daily PnL", f"${day_pnl:,.2f}", f"{(day_pnl/float(acc.last_equity)*100):.2f}%", delta_color=pnl_color)
    m4.metric("Market Status", "OPEN" if trade_client.get_clock().is_open else "CLOSED")
except:
    pass

# ====================== REFRESH ======================
time.sleep(30)
st.rerun()
