import yfinance as yf
import ollama

AI_MODEL = "phi3" 

def get_data_and_news(ticker):
    print(f"\n[BLUE] Fetching data & news for {ticker}...")
    stock = yf.Ticker(ticker)
    
    # 1. Get Price History (Safe Mode)
    try:
        history = stock.history(period="1mo")
        if history.empty:
            print(f"[ERROR] No price data found for {ticker}. Market might be closed or symbol is wrong.")
            return None
    except Exception as e:
        print(f"[ERROR] Failed to fetch price: {e}")
        return None
    
    current_price = round(history['Close'].iloc[-1], 2)
    start_price = history['Close'].iloc[0]
    growth = round(((current_price - start_price) / start_price) * 100, 2)
    
    # 2. Get News Headlines (Bulletproof Mode)
    headlines = []
    try:
        news_list = stock.news
        if news_list:
            for item in news_list[:3]:
                # This fixes the 'title' crash:
                title = item.get('title', 'No Title Available')
                headlines.append(f"- {title}")
        else:
            headlines.append("No recent news found.")
    except Exception as e:
        headlines.append(f"Could not fetch news: {e}")
        
    return {
        "symbol": ticker,
        "price": current_price,
        "growth": growth,
        "news": "\n".join(headlines)
    }

def analyze_market(data):
    print("[BLUE] Reading news & thinking... (Running on Ryzen CPU)")
    
    prompt = f"""
    You are BLUE, an institutional financial analyst.
    
    TARGET: {data['symbol']}
    PRICE: {data['price']} (Monthly Change: {data['growth']}%)
    
    NEWS HEADLINES:
    {data['news']}
    
    TASK:
    1. Identify the Sentiment (Positive/Negative).
    2. Give a strict BUY, SELL, or HOLD verdict.
    3. Explain WHY in 1 short sentence.
    """
    
    try:
        response = ollama.chat(model=AI_MODEL, messages=[
            {'role': 'user', 'content': prompt}
        ])
        return response['message']['content']
    except Exception as e:
        return f"AI Brain Malfunction: {e}"

# --- MAIN LOOP ---
if __name__ == "__main__":
    # You can change this list to test multiple stocks
    targets = ["RELIANCE.NS", "GOOG", "TATASTEEL.NS"]
    
    for ticker in targets:
        try:
            info = get_data_and_news(ticker)
            
            if info:
                report = analyze_market(info)
                print("\n" + "="*50)
                print(f" BLUE REPORT: {ticker}")
                print("="*50)
                print(report)
                print("="*50 + "\n")
        except Exception as e:
            print(f"Skipping {ticker} due to error: {e}")