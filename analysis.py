import os
import json
import datetime
import requests
import pandas as pd
import yfinance as yf
# Ensure you have 'google-generativeai' installed: pip install google-generativeai
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    print("Gemini library not available. Using mock analysis.")
    GEMINI_AVAILABLE = False


# --- CONFIGURATION & SECRETS ---
GEMINI_KEY = os.getenv('GEMINI_API_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# List of stocks to scan (Nifty 50 + High Momentum Stocks)
SYMBOLS = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
    'SBIN.NS', 'TATAMOTORS.NS', 'ITC.NS', 'BAJFINANCE.NS', 'BHARTIARTL.NS',
    'ADANIENT.NS', 'LT.NS', 'AXISBANK.NS', 'MARUTI.NS', 'SUNPHARMA.NS',
    'TITAN.NS', 'ULTRACEMCO.NS', 'KOTAKBANK.NS', 'WIPRO.NS', 'HCLTECH.NS',
    'TATASTEEL.NS', 'M&M.NS', 'NTPC.NS', 'POWERGRID.NS', 'ONGC.NS',
    'COALINDIA.NS', 'BHEL.NS', 'ZOMATO.NS', 'TRENT.NS', 'HAL.NS',
    'DLF.NS', 'PIDILITIND.NS', 'DMART.NS' 
]

def get_market_data(sym):
    """Fetches raw technical data for a stock."""
    try:
        stock = yf.Ticker(sym)
        hist = stock.history(period='1mo')
        if hist.empty: return None
        
        close = hist['Close'].iloc[-1]
        change_pct = ((close - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
        
        # RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        # Volume Spike
        vol_avg = hist['Volume'].rolling(20).mean().iloc[-1]
        vol_curr = hist['Volume'].iloc[-1]
        vol_factor = round(vol_curr / vol_avg, 1) if vol_avg > 0 else 1.0

        return f"{sym} | CMP: {round(close,1)} | Change: {round(change_pct,1)}% | RSI: {round(rsi,1)} | VolFactor: {vol_factor}x"
    except Exception as e:
        # print(f"Error fetching data for {sym}: {e}")
        return None

def generate_ai_analysis(data_list):
    """Sends data to Gemini and strictly controls the output format."""
    
    if not (GEMINI_AVAILABLE and GEMINI_KEY):
        return "⚠️ Gemini API not configured. Check GEMINI_API_KEY in GitHub Secrets."

    print("🧠 Sending data to Gemini for analysis...")
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # 🎯 STRICT PROMPT: Ensure it returns ONLY the report content
    prompt = f"""
    You are the most experienced stock market research analyst.
    Identify the top 5 most probable profitable NSE stocks for tomorrow (Buy side).
    Focus on stocks showing strong technical momentum (RSI 50-70) or recent volume-backed breakouts (VolFactor > 1.5x).
    
    The raw data is:
    {data_list}
    
    CRITICAL OUTPUT RULE: Your response must contain ONLY the formatted report below, with absolutely NO introduction, commentary, or text before or after the report. Use HTML tags <b> and <i> only for formatting.
    
    REPORT FORMAT (STRICT):
    
    🚀 <b>Top 5 High-Conviction NSE Stocks for Tomorrow</b>
    
    Market Sentiment: [One concise sentence about the market/Nifty trend, e.g., 'Bullish/Volatile due to Fed cues.']
    <i>Focus on high relative strength & breakout counters.</i>
    
    [Loop for 5 stocks, numbered 1️⃣ to 5️⃣]
    1️⃣ <b>Stock Name (SYMBOL)</b>
    • <b>CMP:</b> ₹[Current Price]
    • <b>Target:</b> ₹[Target Price]+ (5% Upside)
    • <b>Tech Signal:</b> [Very short technical reason, e.g., Strong Volume Breakout or RSI Reversal]
    • <b>Stop Loss:</b> ₹[Stop Loss Price]
    [End loop]
    
    📉 <b>Index Outlook:</b> [One concise sentence about Nifty support/resistance.]
    
    ⚠️ <b>Risk Note:</b> Strict Stop Loss is non-negotiable. These are high-risk/high-reward momentum setups.
    """
    
    try:
        response = model.generate_content(prompt)
        # Strip any leading/trailing whitespace/markdown, though the prompt should prevent it
        return response.text.strip()
    except Exception as e:
        return f"❌ Gemini API Error: Could not generate analysis. Check API Key or usage limits. Error: {e}"

def send_telegram(message):
    """Sends the final report message to the Telegram chat."""
    if not (BOT_TOKEN and CHAT_ID):
        print("❌ Telegram keys missing (BOT_TOKEN or CHAT_ID)")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID, 
        'text': message, 
        'parse_mode': 'HTML', 
        'disable_web_page_preview': True
    }
    try:
        requests.post(url, data=payload)
        print("✅ Telegram alert sent!")
    except Exception as e:
        print(f"❌ Telegram failed: {e}")

if __name__ == "__main__":
    print(f"Collecting data for {len(SYMBOLS)} stocks...")
    
    # 1. Collect Data
    market_snapshot = []
    for sym in SYMBOLS:
        data = get_market_data(sym)
        if data:
            market_snapshot.append(data)
            
    # 2. Ask Gemini to Analyze
    data_string = "\n".join(market_snapshot)
    ai_report = generate_ai_analysis(data_string)
    
    # 3. Send Result
    print("\n--- AI REPORT SENT TO TELEGRAM ---\n")
    print(ai_report) 
    
    # The crucial part: this function sends ONLY the string returned by Gemini.
    send_telegram(ai_report)
    
    print("\n--- END OF RUN ---")
