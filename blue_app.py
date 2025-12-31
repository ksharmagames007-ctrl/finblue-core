import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="FinBlue Sovereign AI", layout="wide", page_icon="ew")

# --- SMART TRANSLATOR (Human -> Robot) ---
def get_symbol_and_currency(query):
    # 1. CLEAN THE INPUT
    query = query.upper().strip()
    
    # 2. DICTIONARY OF COMMON STOCKS (Add more here!)
    mapping = {
        "RELIANCE": "RELIANCE.NS",
        "TATA": "TATAMOTORS.NS",
        "TRENT": "TRENT.NS",
        "ZOMATO": "ZOMATO.NS",
        "ADANI": "ADANIENT.NS",
        "HDFC": "HDFCBANK.NS",
        "APPLE": "AAPL",
        "MICROSOFT": "MSFT",
        "TESLA": "TSLA",
        "GOOGLE": "GOOGL",
        "NVIDIA": "NVDA",
        "INTEL": "INTC"
    }
    
    # 3. GET TICKER
    ticker = mapping.get(query, query) # If not in map, use what user typed
    
    # 4. AUTO-DETECT CURRENCY
    if ticker.endswith(".NS") or ticker == "^NSEI":
        currency = "₹"
    else:
        currency = "$" # Default to USD for global
        
    return ticker, currency

# --- SIDEBAR (THE CONTROLS) ---
st.sidebar.title("FinBlue Command")

# INPUT BOX IS BACK AT THE TOP (Global)
user_query = st.sidebar.text_input("Search Company (e.g. Zomato, Apple, Tata)", "Zomato")
ticker, curr = get_symbol_and_currency(user_query)

st.sidebar.caption(f"Active Ticker: **{ticker}**")
st.sidebar.divider()

mode = st.sidebar.radio("Select Mode", [
    "Live Dashboard", 
    "Backtest Engine (Time Machine)",
    "AI Prophet (Smart Entry)",
    "Market Scanner (Watchtower)"
])

# --- CORE FUNCTION: FETCH DATA ---
def get_data(ticker, period="5y"):
    try:
        data = yf.download(ticker, period=period, interval="1d", progress=False)
        if data.empty: return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        # INDICATORS
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['SMA_200'] = data['Close'].rolling(window=200).mean()
        
        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        return data
    except:
        return None

# --- MODE 1: LIVE DASHBOARD (RESTORED) ---
if mode == "Live Dashboard":
    st.title(f"🔵 FinBlue Live: {ticker}")
    data = get_data(ticker)
    
    if data is None or data.empty:
        st.error(f"⚠️ Could not find data for **{ticker}**. Check spelling.")
    else:
        latest = data.iloc[-1]
        
        # METRICS
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Price", f"{curr}{round(latest['Close'], 2)}")
        
        rsi = round(latest['RSI'], 1)
        col2.metric("RSI", rsi)
        
        trend = "UP 🚀" if latest['SMA_50'] > latest['SMA_200'] else "DOWN 🔻"
        col3.metric("Trend", trend)
        
        vol = f"{int(latest['Volume']/1000000)}M" if latest['Volume'] > 1000000 else f"{int(latest['Volume'])}"
        col4.metric("Volume", vol)

        # CHART
        st.area_chart(data['Close'], color="#0068c9")

# --- MODE 2: BACKTEST ENGINE ---
elif mode == "Backtest Engine (Time Machine)":
    st.title(f"⏳ Time Machine: {ticker}")
    
    col_a, col_b = st.columns(2)
    initial_capital = col_a.number_input(f"Initial Capital ({curr})", value=100000)
    stop_loss_pct = col_b.slider("Stop Loss (%)", 1, 20, 10)
    
    if st.button("Run Simulation"):
        data = get_data(ticker)
        if data is not None:
            data = data.dropna()
            balance = initial_capital
            shares = 0
            position = 0
            peak_price = 0
            portfolio_values = []
            
            for index, row in data.iterrows():
                price = row['Close']
                # STOP LOSS
                if position == 1:
                    if price > peak_price: peak_price = price
                    drop = (peak_price - price) / peak_price
                    if drop > (stop_loss_pct/100):
                        balance = shares * price
                        shares = 0
                        position = 0
                
                # BUY (Golden Cross)
                if position == 0 and row['SMA_50'] > row['SMA_200']:
                    shares = balance / price
                    balance = 0
                    position = 1
                    peak_price = price
                
                # SELL (Death Cross)
                elif position == 1 and row['SMA_50'] < row['SMA_200']:
                    balance = shares * price
                    shares = 0
                    position = 0
                
                val = shares * price if position == 1 else balance
                portfolio_values.append(val)
            
            # RESULTS
            final_val = portfolio_values[-1]
            profit = final_val - initial_capital
            roi = (profit/initial_capital)*100
            
            # FEES (Sovereign Model)
            mgmt_fee = initial_capital * 0.02
            perf_fee = profit * 0.20 if profit > 0 else 0
            my_earnings = mgmt_fee + perf_fee
            
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Client Final Value", f"{curr}{int(final_val):,}", delta=f"{round(roi,2)}%")
            c2.metric("FinBlue Earnings (You)", f"{curr}{int(my_earnings):,}")
            c3.metric("Net Client Profit", f"{curr}{int(final_val - my_earnings):,}")
            
            st.line_chart(portfolio_values)

# --- MODE 3: AI SNIPER ---
elif mode == "AI Prophet (Smart Entry)":
    st.title(f"🎯 AI Sniper: {ticker}")
    
    if st.button("Analyze Trade"):
        data = get_data(ticker)
        if data is not None:
            data = data.dropna().reset_index()
            
            # AI PREDICTION
            data['Date_Ordinal'] = data['Date'].map(pd.Timestamp.toordinal)
            X = data[['Date_Ordinal']]
            y = data['Close']
            model = LinearRegression()
            model.fit(X, y)
            
            future_date = data['Date'].iloc[-1] + datetime.timedelta(days=30)
            pred_price = model.predict([[future_date.toordinal()]])[0]
            curr_price = data['Close'].iloc[-1]
            ai_upside = ((pred_price - curr_price) / curr_price) * 100
            
            rsi = data['RSI'].iloc[-1]
            
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Current Price", f"{curr}{round(curr_price, 2)}")
            c2.metric("AI Prediction (30 Days)", f"{curr}{round(pred_price, 2)}", delta=f"{round(ai_upside, 1)}%")
            c3.metric("RSI Level", f"{round(rsi, 1)}")
            
            # VERDICT LOGIC
            st.subheader("🤖 Sovereign Verdict")
            if ai_upside > 5:
                if rsi < 45: st.success(f"✅ BUY {ticker} NOW! (Trend UP + Dip)")
                elif rsi > 70: st.warning(f"✋ WAIT. {ticker} is too expensive right now.")
                else: st.info(f"🔹 ACCUMULATE. {ticker} is fair value.")
            else:
                st.error(f"❌ AVOID {ticker}. Trend is Weak.")
            
            st.line_chart(data['Close'])

# --- MODE 4: WATCHTOWER (SCANNER) ---
elif mode == "Market Scanner (Watchtower)":
    st.title("📡 FinBlue Watchtower")
    
    # HARDCODED WATCHLIST (Mix of India & USA)
    watchlist = ["RELIANCE.NS", "ZOMATO.NS", "TRENT.NS", "AAPL", "TSLA", "NVDA"]
    
    if st.button("Scan Global Market"):
        results = []
        progress = st.progress(0)
        
        for i, t in enumerate(watchlist):
            # Detect Currency for Watchlist
            sym = "₹" if ".NS" in t else "$"
            
            with st.spinner(f"Scanning {t}..."):
                d = get_data(t, period="5y") # USE 5Y FOR ACCURACY
                if d is not None:
                    d = d.dropna().reset_index()
                    
                    # AI Logic
                    d['Date_Ordinal'] = d['Date'].map(pd.Timestamp.toordinal)
                    model = LinearRegression()
                    model.fit(d[['Date_Ordinal']], d['Close'])
                    
                    fut = d['Date'].iloc[-1] + datetime.timedelta(days=30)
                    pred = model.predict([[fut.toordinal()]])[0]
                    curr_p = d['Close'].iloc[-1]
                    upside = ((pred - curr_p) / curr_p) * 100
                    rsi_val = d['RSI'].iloc[-1]
                    
                    # Verdict
                    verdict = "HOLD 🔵"
                    if upside > 5 and rsi_val < 45: verdict = "BUY NOW 🟢"
                    elif upside > 5 and rsi_val > 70: verdict = "WAIT (High) 🟡"
                    elif upside < 0: verdict = "AVOID 🔴"
                    
                    results.append({
                        "Ticker": t,
                        "Price": f"{sym}{round(curr_p, 0)}",
                        "RSI": round(rsi_val, 0),
                        "AI Upside": f"{round(upside, 1)}%",
                        "Verdict": verdict
                    })
            progress.progress((i + 1) / len(watchlist))
            
        st.dataframe(pd.DataFrame(results), use_container_width=True)