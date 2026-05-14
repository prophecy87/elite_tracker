def auto_trade():
    # Assets - Removed -USD for Alpaca compatibility
    tickers = ["NVDA", "TSLA", "BTC/USD", "ETH/USD", "SOL/USD", "MSTR"]
    
    if random.random() < 0.72:  
        ticker = random.choice(tickers)
        
        try:
            # yfinance needs the '-' format, Alpaca needs the '/' format
            yf_ticker = ticker.replace("/", "-")
            data = yf.download(yf_ticker, period="1d", interval="1m", progress=False)
            
            if data.empty:
                st.warning(f"⚠️ No price data for {yf_ticker}")
                return

            price = float(data['Close'].iloc[-1])
            
            # 1. Calculate Sizing
            max_risk = st.session_state.balance * 0.15 # Risk 15%
            qty = max_risk / price
            
            # Crypto allows decimals, Stocks do not (usually)
            if "/" not in ticker:
                qty = int(qty)
            else:
                qty = round(qty, 4) # Standard for BTC/ETH

            if qty <= 0:
                return

            # 2. Execution logic
            # Clean ticker for Alpaca (Remove the / if it's a stock)
            alpaca_symbol = ticker.replace("/", "") if "/" not in ticker else ticker
            
            order_details = MarketOrderRequest(
                symbol=alpaca_symbol,
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.GTC # Good 'Til Cancelled
            )
            
            # SUBMIT
            submitted_order = trade_client.submit_order(order_details)
            
            # 3. Log to ledger
            trade = {
                "entry_time": datetime.now().strftime("%H:%M:%S"),
                "ticker": alpaca_symbol,
                "entry_price": round(price, 2),
                "qty": qty,
                "status": "FILLED",
                "pnl": "OPEN",
                "order_id": str(submitted_order.id)[:8]
            }
            st.session_state.trades.append(trade)
            save_ledger()
            st.toast(f"🚀 ORDER FILLED: {qty} {alpaca_symbol}", icon="💰")

        except Exception as e:
            # THIS WILL TELL YOU WHY IT'S ZERO
            st.error(f"❌ Trade Failed: {str(e)}")
