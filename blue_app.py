import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime
import requests # <--- The Tool to talk to the Internet

# --- PAGE CONFIG ---
st.set_page_config(page_title="FinBlue Sovereign AI", layout="wide", page_icon="ew")

# --- THE LIVE SEARCH ENGINE (The New Brain) ---
def get_symbol_from_yahoo(query):
    query = query.strip().upper()
    
    # 1. OPTIONAL: Fast Track for common Indian names (Keeps it fast)
    common_map = {
        "RELIANCE": "RELIANCE.NS", "TATA": "TATAMOTORS.NS", "ZOMATO": "ZOMATO.NS",
        "ICICI": "ICICIBANK.NS", "HDFC": "HDFCBANK.NS", "SBI": "SBIN.NS"
    }
    if query in common_map:
        return common_map[query], "₹"

    # 2. ASK THE INTERNET (Yahoo Search API)
    try:
        user_agent = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        response = requests.get(url, headers=user_agent, timeout=5)
        data = response.json()
        
        if 'quotes' in data and len(data['quotes']) > 0:
            # Get the #1 Best Match
            best_match = data['quotes'][0]
            symbol = best_match['symbol']
            
            # Detect Currency based on Symbol
            if ".NS" in symbol or ".BO" in symbol:
                currency = "₹"
            else:
                currency = "$"
                
            return symbol, currency
    except Exception as e:
        print(f"Search Error: {e}")
    
    # 3. FALLBACK (If Internet Fails, guess it's Indian)
    return f"{query}.NS", "₹"

# --- SIDEBAR CONTROL ---
st.sidebar.title("FinBlue Command")
st.sidebar.caption("🌍 Global Search Active")

# INPUT BOX
user_query = st.sidebar.text_input("Search Company (Any Name)", "Zomato")

# RUN THE SEARCH
with st.spinner(f"Searching global database for '{user_query}'..."):
    ticker, curr = get_symbol_from_yahoo(user_query)

st.sidebar.success(f"**Found:** {ticker}")
st.sidebar.divider()

mode = st.sidebar.radio("Select Mode", [
    "Live Dashboard", 
    "Backtest Engine (Time Machine)",
    "AI Prophet (Smart Entry)",
    "Market Scanner (Watchtower)"
])

# --- FETCH DATA FUNCTION ---
def get_data(ticker, period="5y"):
    try:
        data = yf.download(ticker, period=period, interval="1d", progress=False)
        if data.empty: return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['SMA_200'] = data['Close'].rolling(window=200).mean()
        
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

# --- MODE 1: LIVE DASHBOARD ---
if mode == "Live Dashboard":
    st.title(f"🔵 FinBlue Live: {ticker}")
    data = get_data(ticker)
    
    if data is None or data.empty:
        st.error(f"❌ Could not load data for **{ticker}**.")
        st.write("Try typing the full name, e.g., 'ICICI Bank' instead of 'ICICI'.")
    else:
        latest = data.iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Price", f"{curr}{round(latest['Close'], 2)}")
        c2.metric("RSI", f"{round(latest['RSI'], 1)}")
        trend = "UP 🚀" if latest['SMA_50'] > latest['SMA_200'] else "DOWN 🔻"
        c3.metric("Trend", trend)
        c4.metric("Volume", f"{int(latest['Volume']/1000000)}M")
        
        st.area_chart(data['Close'], color="#0068c9")

# --- MODE 2: BACKTEST ENGINE ---
elif mode == "Backtest Engine (Time Machine)":
    st.title(f"⏳ Time Machine: {ticker}")
    col_a, col_b = st.columns(2)
    capital = col_a.number_input(f"Capital ({curr})", value=100000)
    stop_loss = col_b.slider("Stop Loss (%)", 1, 20, 10)
    
    if st.button("Run Simulation"):
        data = get_data(ticker)
        if data is not None:
            data = data.dropna()
            balance = capital; shares = 0; position = 0; peak = 0; history = []
            
            for index, row in data.iterrows():
                price = row['Close']
                if position == 1:
                    if price > peak: peak = price
                    if (peak - price)/peak > (stop_loss/100):
                        balance = shares * price; shares = 0; position = 0
                if position == 0 and row['SMA_50'] > row['SMA_200']:
                    shares = balance / price; balance = 0; position = 1; peak = price
                elif position == 1 and row['SMA_50'] < row['SMA_200']:
                    balance = shares * price; shares = 0; position = 0
                history.append(shares * price if position == 1 else balance)
            
            final = history[-1]
            profit = final - capital
            fees = (capital * 0.02) + (profit * 0.20 if profit > 0 else 0)
            
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Client Profit", f"{curr}{int(profit):,}")
            c2.metric("Your Fees", f"{curr}{int(fees):,}")
            c3.metric("Net Client Value", f"{curr}{int(final - fees):,}")
            st.line_chart(history)

# --- MODE 3: AI SNIPER ---
elif mode == "AI Prophet (Smart Entry)":
    st.title(f"🎯 AI Sniper: {ticker}")
    if st.button("Analyze Trade"):
        data = get_data(ticker)
        if data is not None:
            data = data.dropna().reset_index()
            data['Time'] = data['Date'].map(pd.Timestamp.toordinal)
            model = LinearRegression()
            model.fit(data[['Time']], data['Close'])
            future = data['Date'].iloc[-1] + datetime.timedelta(days=30)
            pred = model.predict([[future.toordinal()]])[0]
            curr_p = data['Close'].iloc[-1]
            upside = ((pred - curr_p)/curr_p)*100
            rsi = data['RSI'].iloc[-1]
            
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Current", f"{curr}{round(curr_p,2)}")
            c2.metric("AI Forecast", f"{round(upside,1)}%")
            c3.metric("RSI", f"{round(rsi,1)}")
            
            if upside > 5:
                if rsi < 45: st.success("✅ BUY NOW (Trend Up + Cheap)")
                elif rsi > 70: st.warning("✋ WAIT (Trend Up but Expensive)")
                else: st.info("🔹 ACCUMULATE (Fair Price)")
            else:
                st.error("❌ AVOID (Trend Weak)")
            st.line_chart(data['Close'])

# --- MODE 4: WATCHTOWER ---
elif mode == "Market Scanner (Watchtower)":
    st.title("📡 FinBlue Watchtower")
    # This list is still useful to keep your favorites
    watchlist = ["RELIANCE.NS", "ZOMATO.NS", "TATAMOTORS.NS", "AAPL", "NVDA", "ICICIBANK.NS"]
    
    if st.button("Scan Market"):
        res = []
        for t in watchlist:
            d = get_data(t)
            if d is not None:
                curr_p = d['Close'].iloc[-1]
                rsi = d['RSI'].iloc[-1]
                trend = "UP" if d['SMA_50'].iloc[-1] > d['SMA_200'].iloc[-1] else "DOWN"
                verdict = "BUY" if trend == "UP" and rsi < 45 else ("AVOID" if trend == "DOWN" else "HOLD")
                sym = "₹" if ".NS" in t else "$"
                res.append({"Ticker": t, "Price": f"{sym}{int(curr_p)}", "RSI": int(rsi), "Verdict": verdict})
        st.dataframe(pd.DataFrame(res), use_container_width=True)