import json
import datetime
import os
import requests
from jinja2 import Template
import yfinance as yf  # For fetching real stock data

# Create output folder if it doesn't exist
os.makedirs('output', exist_ok=True)

# Load config from file or use defaults
cfg_path = 'config.json'
if os.path.exists(cfg_path):
    try:
        with open(cfg_path, 'r') as f:
            config = json.load(f)
        print(f"Loaded config from {cfg_path}")
    except Exception as e:
        print(f"Error loading config: {e}. Using defaults.")
        config = {}
else:
    print(f"No {cfg_path} found. Using defaults.")
    config = {}

# Default config if not loaded
default_config = {
    'BOT_TOKEN': config.get('BOT_TOKEN', ''),  # Empty = no Telegram
    'CHAT_ID': config.get('CHAT_ID', ''),
    'AFFILIATES': config.get('AFFILIATES', {'Broker': 'https://example.com/referral'})
}

# Initialize fundamentals dictionary (stubbed for now - can add real data later)
fundamentals = {'PE': None, 'ROE': None}

# Initialize signals list
signals = []

# List of stock symbols (edit this list as needed)
symbols = ['AAPL', 'MSFT', 'GOOG']

# Function to fetch latest stock data (now defined!)
def get_latest_data(symbol):
    try:
        print(f"Fetching data for {symbol}...")
        stock = yf.Ticker(symbol)
        hist = stock.history(period='1mo')  # Last 1 month data
        if hist.empty:
            raise ValueError(f"No data for {symbol}")
        
        # Calculate RSI (14-period, simplified)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1] if not loss.iloc[-1] == 0 else 100
        
        # Simple MACD/EMA cross signals (bullish if close > moving average)
        short_ema = hist['Close'].rolling(window=12).mean().iloc[-1]
        long_ema = hist['Close'].rolling(window=26).mean().iloc[-1]
        macd_cross = 'bullish' if short_ema > long_ema else 'bearish'
        ema_cross = 'bullish' if hist['Close'].iloc[-1] > hist['Close'].rolling(window=50).mean().iloc[-1] else 'bearish'
        
        return {
            'rsi': float(rsi),  # Ensure it's a number
            'macd_cross': macd_cross,
            'ema_cross': ema_cross
        }
    except Exception as e:
        print(f"Error in get_latest_data for {symbol}: {e}")
        return {'rsi': None, 'macd_cross': None, 'ema_cross': None}

# Scoring functions (now defined! Customize these with your logic)
def get_score_short(symbol):
    return 0.75  # Short-term score (e.g., based on RSI)

def get_score_medium(symbol):
    return 0.65  # Medium-term

def get_score_long(symbol):
    return 0.55  # Long-term

# Process each symbol
for sym in symbols:
    try:
        print(f"Processing {sym}...")
        latest = get_latest_data(sym)
        score_short = get_score_short(sym)
        score_medium = get_score_medium(sym)
        score_long = get_score_long(sym)

        # Generate signal
        signal = 'BUY' if (
            latest.get('rsi', 100) < 60 and
            latest.get('macd_cross') == 'bullish' and
            latest.get('ema_cross') == 'bullish'
        ) else 'HOLD'

        rec = {
            'symbol': sym,
            'score_short': round(score_short, 2),
            'score_medium': round(score_medium, 2),
            'score_long': round(score_long, 2),
            'signal': signal,
            'rsi': round(latest['rsi'], 2) if latest.get('rsi') is not None else None,
            'macd_cross': latest.get('macd_cross'),
            'ema_cross': latest.get('ema_cross'),
            'fundamentals': fundamentals
        }
        signals.append(rec)
        print(f"{sym}: {signal} (RSI: {rec['rsi']})")

    except Exception as e:
        print(f"Error processing {sym}: {e}")

# Save JSON
try:
    json_path = 'output/signals.json'
    with open(json_path, 'w') as f:
        json.dump(signals, f, indent=2)
    print(f"Saved JSON to {json_path}")
except Exception as e:
    print(f"Error saving JSON: {e}")

# Render HTML report
try:
    template_path = 'templates/report_template.html'
    if os.path.exists(template_path):
        with open(template_path, 'r') as f:
            template_content = f.read()
    else:
        # Fallback template if file missing
        template_content = """
        <html>
        <head><title>Daily Stock Report</title></head>
        <body>
            <h1>Stock Analysis Report</h1>
            <p>Generated at: {{ generated_at }}</p>
            <table border="1">
                <tr><th>Symbol</th><th>Signal</th><th>RSI</th><th>Short Score</th></tr>
                {% for signal in signals %}
                <tr>
                    <td>{{ signal.symbol }}</td>
                    <td>{{ signal.signal }}</td>
                    <td>{{ signal.rsi }}</td>
                    <td>{{ signal.score_short }}</td>
                </tr>
                {% endfor %}
            </table>
            <p>Affiliate: <a href="{{ affiliates.Broker }}">Trade Now</a></p>
        </body>
        </html>
        """
        print("Using fallback template")

    tpl = Template(template_content)
    html = tpl.render(
        signals=signals,
        generated_at=str(datetime.datetime.now()),
        affiliates=default_config['AFFILIATES']
    )

    report_path = 'output/daily_report.html'
    with open(report_path, 'w') as f:
        f.write(html)
    print(f"Saved HTML to {report_path}")

except Exception as e:
    print(f"Error rendering HTML: {e}")

# Telegram alert (only if configured)
BOT = default_config['BOT_TOKEN']
CHAT = default_config['CHAT_ID']
if BOT and CHAT:
    try:
        buy_list = [s['symbol'] for s in signals if s['signal'] == 'BUY']
        msg = '<b>Top Buys</b>\n' + ('None' if not buy_list else '\n'.join(buy_list))
        response = requests.post(
            f'https://api.telegram.org/bot{BOT}/sendMessage',
            data={'chat_id': CHAT, 'text': msg, 'parse_mode': 'HTML'}
        )
        response.raise_for_status()
        print("Telegram alert sent!")
    except Exception as e:
        print(f"Telegram error: {e}")
else:
    print("Skipping Telegram (no config)")

print("Done! Check output/ folder.")
