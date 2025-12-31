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
    "Market Scanner (Command Center)",
    "AI Sniper (Deep Analysis)"
])

# --- FUNCTION: FETCH & ANALYZE ---
def analyze_stock(ticker):
    try:
        data = yf.download(ticker, period="2y", interval="1d", progress=False)
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
        
        # AI PREDICTION
        data = data.dropna().reset_index()
        data['Date_Ordinal'] = data['Date'].map(pd.Timestamp.toordinal)
        X = data[['Date_Ordinal']]
        y = data['Close']
        model = LinearRegression()
        model.fit(X, y)
        
        future_date = data['Date'].iloc[-1] + datetime.timedelta(days=30)
        pred_price = model.predict([[future_date.toordinal()]])[0]
        curr_price = data['Close'].iloc[-1]
        ai_upside = ((pred_price - curr_price) / curr_price) * 100
        
        return {
            "Ticker": ticker,
            "Price": round(curr_price, 2),
            "RSI": round(data['RSI'].iloc[-1], 1),
            "Trend": "UP 🚀" if data['SMA_50'].iloc[-1] > data['SMA_200'].iloc[-1] else "DOWN 🔻",
            "AI_Upside": round(ai_upside, 1)
        }
    except:
        return None

# --- MODE 1: LIVE DASHBOARD ---
if mode == "Live Dashboard":
    st.title("FinBlue Live Dashboard")
    st.write("Select a specific tool from the sidebar to begin.")

# --- MODE 2: MARKET SCANNER (NEW) ---
elif mode == "Market Scanner (Command Center)":
    st.title("📡 FinBlue Watchtower")
    st.write("Scanning the Sovereign Watchlist...")
    
    # THE WATCHLIST (You can add more here)
    watchlist = ["RELIANCE.NS", "TRENT.NS", "ZOMATO.NS", "ADANIENT.NS", "HDFCBANK.NS", "TATAMOTORS.NS"]
    
    if st.button("Scan Market Now"):
        results = []
        progress = st.progress(0)
        
        for i, ticker in enumerate(watchlist):
            with st.spinner(f"Analyzing {ticker}..."):
                stats = analyze_stock(ticker)
                if stats:
                    # LOGIC: VERDICT
                    if stats['AI_Upside'] > 5 and stats['RSI'] < 45:
                        stats['Verdict'] = "BUY NOW 🟢"
                    elif stats['AI_Upside'] > 5 and stats['RSI'] > 70:
                        stats['Verdict'] = "WAIT (High) 🟡"
                    elif stats['AI_Upside'] < 0:
                        stats['Verdict'] = "AVOID 🔴"
                    else:
                        stats['Verdict'] = "HOLD 🔵"
                    results.append(stats)
            progress.progress((i + 1) / len(watchlist))
            
        # DISPLAY AS A DATAFRAME
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        
        # HIGHLIGHT THE WINNER
        best_pick = df[df['Verdict'] == "BUY NOW 🟢"]
        if not best_pick.empty:
            st.success(f"💎 **Top Pick:** {best_pick.iloc[0]['Ticker']} is in the BUY ZONE!")
        else:
            st.info("No perfect entries found right now. Patience pays.")

# --- MODE 3: AI SNIPER ---
elif mode == "AI Sniper (Deep Analysis)":
    ticker = st.sidebar.text_input("Enter Ticker", "TRENT.NS")
    st.title(f"🎯 AI Sniper: {ticker}")
    
    if st.button("Analyze Trade"):
        with st.spinner("Calculating..."):
            stats = analyze_stock(ticker)
            if stats:
                c1, c2, c3 = st.columns(3)
                c1.metric("Price", f"₹{stats['Price']}")
                c2.metric("AI Prediction", f"{stats['AI_Upside']}%")
                c3.metric("RSI", stats['RSI'])
                
                st.divider()
                if stats['AI_Upside'] > 5:
                    if stats['RSI'] < 45:
                        st.success("✅ BUY NOW! (Trend Up + Price Cheap)")
                    elif stats['RSI'] > 70:
                        st.warning("✋ WAIT. (Trend Up but Price too High)")
                    else:
                        st.info("🔹 ACCUMULATE. (Fair Price)")
                else:
                    st.error("❌ AVOID. (Trend is Flat/Down)")