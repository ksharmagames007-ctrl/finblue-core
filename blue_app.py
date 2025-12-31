import streamlit as st
import yfinance as yf
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="FinBlue Sovereign", layout="wide", page_icon="ew")

# --- SIDEBAR ---
st.sidebar.title("FinBlue Command")
mode = st.sidebar.radio("Select Mode", ["Live Dashboard", "Backtest Engine (Time Machine)"])
# DEFAULT TO A WINNER
ticker = st.sidebar.text_input("Enter Ticker (e.g., TRENT.NS, ZOMATO.NS)", "TRENT.NS")

# --- FUNCTION: FETCH DATA ---
def get_data(ticker):
    try:
        # Download 5 years to ensure we have enough data for 200 SMA
        data = yf.download(ticker, period="5y", interval="1d", progress=False)
        
        if data.empty: return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        # --- THE GOLDEN CROSS CALCULATION ---
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['SMA_200'] = data['Close'].rolling(window=200).mean()
        data['RSI'] = 50 # Placeholder so dashboard doesn't break
        
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
        col1.metric("Price", f"₹{round(latest['Close'], 2)}")
        
        # TREND SIGNAL
        trend = "BULLISH (UP)" if latest['SMA_50'] > latest['SMA_200'] else "BEARISH (DOWN)"
        col2.metric("Market Trend", trend)
        col3.metric("50-Day Avg", f"₹{round(latest['SMA_50'], 2)}")
        st.line_chart(data['Close'])

# --- MODE 2: BACKTEST ENGINE (GOLDEN CROSS) ---
elif mode == "Backtest Engine (Time Machine)":
    st.title("⏳ FinBlue Time Machine (Golden Cross)")
    st.write(f"Testing **Trend Following** Strategy on **{ticker}**...")
    
    initial_capital = st.number_input("Initial Capital (₹)", value=100000)
    
    if st.button("Run Simulation"):
        data = get_data(ticker)
        
        if data is None or data.empty:
            st.error("No data found.")
        else:
            # Drop NaN values created by SMAs
            data = data.dropna()
            
            position = 0
            balance = initial_capital
            shares = 0
            portfolio_values = []
            
            for index, row in data.iterrows():
                price = row['Close']
                sma_50 = row['SMA_50']
                sma_200 = row['SMA_200']
                
                # BUY: When 50 crosses ABOVE 200 (Golden Cross)
                if sma_50 > sma_200 and position == 0:
                    shares = balance / price
                    balance = 0
                    position = 1
                
                # SELL: When 50 crosses BELOW 200 (Death Cross)
                elif sma_50 < sma_200 and position == 1:
                    balance = shares * price
                    shares = 0
                    position = 0
                
                # TRACK VALUE
                if position == 1:
                    curr_val = shares * price
                else:
                    curr_val = balance
                portfolio_values.append(curr_val)
            
            # --- RESULTS & FEES CALCULATION ---
            final_value = portfolio_values[-1]
            total_profit = final_value - initial_capital
            roi = (total_profit / initial_capital) * 100
            
            # THE SOVEREIGN FEE MODEL
            mgmt_fee = initial_capital * 0.02  # 2% Flat Fee
            perf_fee = 0
            if total_profit > 0:
                perf_fee = total_profit * 0.20 # 20% of Profit
            
            total_fees = mgmt_fee + perf_fee
            client_take_home = final_value - total_fees
            
            # --- DISPLAY THE SCOREBOARD ---
            st.divider()
            st.subheader("🏆 The Scoreboard")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("💰 Client Profit", f"₹{int(total_profit):,}", delta=f"{round(roi, 2)}%")
            c2.metric("🏦 FinBlue Earnings (You)", f"₹{int(total_fees):,}", delta="Your Income")
            c3.metric("NET Client Value", f"₹{int(client_take_home):,}")
            
            if total_profit > 0:
                st.balloons()
                st.success(f"🚀 BOOM! You just earned ₹{int(total_fees):,} from this single client.")
            
            st.line_chart(portfolio_values)
            
            