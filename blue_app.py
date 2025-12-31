import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="FinBlue Sovereign AI", layout="wide", page_icon="ew")

# --- SIDEBAR ---
st.sidebar.title("FinBlue Command")
mode = st.sidebar.radio("Select Mode", [
    "Live Dashboard", 
    "Backtest Engine (Risk Managed)",
    "AI Prophet (Smart Entry)"
])
ticker = st.sidebar.text_input("Enter Ticker (e.g., TRENT.NS, ADANIENT.NS)", "TRENT.NS")

# --- FUNCTION: FETCH DATA ---
def get_data(ticker):
    try:
        data = yf.download(ticker, period="5y", interval="1d", progress=False)
        if data.empty: return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        # INDICATORS
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['SMA_200'] = data['Close'].rolling(window=200).mean()
        
        # RSI CALCULATION (The "Cheap vs Expensive" meter)
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
        st.error("⚠️ Ticker not found.")
    else:
        latest = data.iloc[-1]
        col1, col2, col3 = st.columns(3)
        col1.metric("Current Price", f"₹{round(latest['Close'], 2)}")
        
        rsi = latest['RSI']
        col2.metric("RSI (Price Heat)", f"{round(rsi, 1)}")
        
        trend = "UP 🚀" if latest['SMA_50'] > latest['SMA_200'] else "DOWN 🔻"
        col3.metric("Trend", trend)
        st.line_chart(data['Close'])

# --- MODE 2: BACKTEST ENGINE (WITH STOP LOSS) ---
elif mode == "Backtest Engine (Risk Managed)":
    st.title("⏳ FinBlue Time Machine")
    col_a, col_b = st.columns(2)
    initial_capital = col_a.number_input("Initial Capital (₹)", value=100000)
    stop_loss_pct = col_b.slider("Stop Loss (%) - Sell if drops by:", 1, 20, 10)
    
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
                # STOP LOSS LOGIC
                if position == 1:
                    if price > peak_price: peak_price = price
                    drop = (peak_price - price) / peak_price
                    if drop > (stop_loss_pct/100):
                        balance = shares * price
                        shares = 0
                        position = 0
                
                # BUY LOGIC (Golden Cross)
                if position == 0 and row['SMA_50'] > row['SMA_200']:
                    shares = balance / price
                    balance = 0
                    position = 1
                    peak_price = price
                
                # SELL LOGIC (Death Cross)
                elif position == 1 and row['SMA_50'] < row['SMA_200']:
                    balance = shares * price
                    shares = 0
                    position = 0
                
                val = shares * price if position == 1 else balance
                portfolio_values.append(val)
            
            profit = portfolio_values[-1] - initial_capital
            st.metric("Final Value", f"₹{int(portfolio_values[-1]):,}", delta=f"{int(profit)}")
            st.line_chart(portfolio_values)

# --- MODE 3: AI SNIPER (THE NEW LOGIC) ---
elif mode == "AI Prophet (Smart Entry)":
    st.title(f"🎯 AI Sniper: {ticker}")
    st.write("Combining **Long Term AI Prediction** with **Short Term RSI**.")
    
    if st.button("Analyze Trade"):
        data = get_data(ticker)
        if data is not None:
            data = data.dropna().reset_index()
            
            # 1. ASK THE AI (Long Term)
            data['Date_Ordinal'] = data['Date'].map(pd.Timestamp.toordinal)
            X = data[['Date_Ordinal']]
            y = data['Close']
            model = LinearRegression()
            model.fit(X, y)
            
            future_date = data['Date'].iloc[-1] + datetime.timedelta(days=30)
            pred_price = model.predict([[future_date.toordinal()]])[0]
            curr_price = data['Close'].iloc[-1]
            ai_upside = ((pred_price - curr_price) / curr_price) * 100
            
            # 2. CHECK THE RSI (Short Term)
            rsi = data['RSI'].iloc[-1]
            
            # 3. THE VERDICT
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Current Price", f"₹{round(curr_price, 2)}")
            c2.metric("AI Prediction (30 Days)", f"₹{round(pred_price, 2)}", delta=f"{round(ai_upside, 1)}%")
            c3.metric("RSI Level", f"{round(rsi, 1)}")
            
            st.subheader("🤖 The Sovereign Verdict:")
            
            if ai_upside > 5: # AI says UP
                if rsi < 40:
                    st.success("✅ **BUY NOW!** The trend is UP and the price is CHEAP (Dip). Perfect Entry.")
                elif rsi > 70:
                    st.warning("✋ **WAIT.** The trend is UP, but the price is too HIGH right now. Wait for it to drop below RSI 60.")
                else:
                    st.info("🔹 **HOLD/ACCUMULATE.** The price is fair. You can buy small amounts.")
            else:
                st.error("❌ **DO NOT BUY.** The AI predicts the trend is Down or Flat.")
            
            # Visuals
            st.line_chart(data['Close'])