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
    "Backtest Engine (Time Machine)",
    "AI Prophet (Future Prediction)"
])
ticker = st.sidebar.text_input("Enter Ticker (e.g., TRENT.NS, ZOMATO.NS)", "TRENT.NS")

# --- FUNCTION: FETCH DATA ---
def get_data(ticker):
    try:
        # Download 5 years for better AI training
        data = yf.download(ticker, period="5y", interval="1d", progress=False)
        if data.empty: return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        # Technical Indicators
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['SMA_200'] = data['Close'].rolling(window=200).mean()
        
        return data
    except:
        return None

# --- MODE 1: LIVE DASHBOARD ---
if mode == "Live Dashboard":
    st.title(f"🔵 FinBlue Live: {ticker}")
    st.caption("⚠️ DATA DELAYED: Do not use for high-frequency trading.")
    
    data = get_data(ticker)
    
    if data is None or data.empty:
        st.error("⚠️ Ticker not found. Check spelling.")
    else:
        latest = data.iloc[-1]
        col1, col2 = st.columns(2)
        col1.metric("Current Price", f"₹{round(latest['Close'], 2)}")
        
        trend = "BULLISH 🚀" if latest['SMA_50'] > latest['SMA_200'] else "BEARISH 🔻"
        col2.metric("Market Trend", trend)
        
        st.line_chart(data['Close'])

# --- MODE 2: BACKTEST ENGINE ---
elif mode == "Backtest Engine (Time Machine)":
    st.title("⏳ FinBlue Time Machine")
    initial_capital = st.number_input("Initial Capital (₹)", value=100000)
    
    if st.button("Run Simulation"):
        data = get_data(ticker)
        if data is not None:
            data = data.dropna()
            
            # Logic: Golden Cross
            data['Signal'] = 0
            data.loc[data['SMA_50'] > data['SMA_200'], 'Signal'] = 1
            data['Position'] = data['Signal'].diff()
            
            # Simple Backtest Loop
            balance = initial_capital
            shares = 0
            portfolio_values = []
            
            for index, row in data.iterrows():
                if row['Position'] == 1: # Buy
                    shares = balance / row['Close']
                    balance = 0
                elif row['Position'] == -1 and shares > 0: # Sell
                    balance = shares * row['Close']
                    shares = 0
                
                curr_val = (shares * row['Close']) if shares > 0 else balance
                portfolio_values.append(curr_val)
            
            # Results
            final_val = portfolio_values[-1]
            profit = final_val - initial_capital
            roi = (profit/initial_capital)*100
            
            # Fees
            mgmt_fee = initial_capital * 0.02
            perf_fee = profit * 0.20 if profit > 0 else 0
            total_fees = mgmt_fee + perf_fee
            client_net = final_val - total_fees
            
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("💰 Client Profit", f"₹{int(profit):,}", delta=f"{round(roi,2)}%")
            c2.metric("🏦 FinBlue Earnings (You)", f"₹{int(total_fees):,}")
            c3.metric("NET Client Value", f"₹{int(client_net):,}")
            
            st.line_chart(portfolio_values)

# --- MODE 3: AI PROPHET (NEW) ---
elif mode == "AI Prophet (Future Prediction)":
    st.title(f"🔮 AI Prophet: Predicting {ticker}")
    st.warning("⚠️ EXPERIMENTAL: This uses Linear Regression. It assumes trends continue forever. Real markets change.")
    
    if st.button("Generate Prediction"):
        data = get_data(ticker)
        if data is not None:
            data = data.dropna()
            data = data.reset_index()
            
            # Prepare Data for AI (Dates to Numbers)
            data['Date_Ordinal'] = data['Date'].map(pd.Timestamp.toordinal)
            
            X = data[['Date_Ordinal']] # Input (Time)
            y = data['Close']          # Output (Price)
            
            # Train the Brain
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict Next 30 Days
            last_date = data['Date'].iloc[-1]
            future_dates = [last_date + datetime.timedelta(days=x) for x in range(1, 31)]
            future_ordinals = [[d.toordinal()] for d in future_dates]
            
            future_prices = model.predict(future_ordinals)
            
            # Display Prediction
            predicted_price = future_prices[-1]
            current_price = data['Close'].iloc[-1]
            change = ((predicted_price - current_price) / current_price) * 100
            
            st.divider()
            col1, col2 = st.columns(2)
            col1.metric("Current Price", f"₹{round(current_price, 2)}")
            
            if change > 0:
                col2.metric("Predicted Price (30 Days)", f"₹{round(predicted_price, 2)}", delta=f"+{round(change, 2)}%")
                st.success("🚀 AI Prediction: BULLISH Trend Detected.")
            else:
                col2.metric("Predicted Price (30 Days)", f"₹{round(predicted_price, 2)}", delta=f"{round(change, 2)}%")
                st.error("📉 AI Prediction: BEARISH Trend Detected.")
            
            # Plotting
            st.subheader("Visualizing the AI Trend Line")
            
            # Add predictions to chart data
            future_df = pd.DataFrame({
                'Date': future_dates,
                'Predicted_Close': future_prices
            })
            
            # Combine historical and future for chart
            st.line_chart(pd.concat([data.set_index('Date')['Close'], future_df.set_index('Date')['Predicted_Close']]))
            
        else:
            st.error("Could not fetch data.")