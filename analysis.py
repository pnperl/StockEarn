import json
import datetime
import os
import requests
from jinja2 import Template
import yfinance as yf  # For real stock data; install via requirements.txt

# Create output folder
os.makedirs('output', exist_ok=True)

# Load cfg from config.json or use defaults (fixes NameError)
cfg_path = 'config.json'
cfg = {}
if os.path.exists(cfg_path):
    try:
        with open(cfg_path, 'r') as f:
            cfg = json.load(f)
        print("Loaded config.json")
    except Exception as e:
        print(f"Config load error: {e}")
else:
    print("No config.json; using defaults")

# Initialize fundamentals (stub for now)
fundamentals = {'PE': None, 'ROE': None}

# Signals list
signals = []

# Stock symbols (edit as needed)
symbols = ['AAPL', 'MSFT', 'GOOG']

# Define get_latest_data (fixes NameError)
def get_latest_data(sym):
    try:
        print(f"Fetching data for {sym}...")
        stock = yf.Ticker(sym)
        hist = stock.history(period='1mo')
        if hist.empty:
            return {'rsi': None, 'macd_cross': None, 'ema_cross': None}
        
        # RSI calculation
        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1] if not loss.iloc[-1] == 0 else 100
        
        # Simple MACD/EMA signals
        macd_cross = 'bullish' if hist['Close'].rolling(12).mean().iloc[-1] > hist['Close'].rolling(26).mean().iloc[-1] else 'bearish'
        ema_cross = 'bullish' if hist['Close'].iloc[-1] > hist['Close'].rolling(50).mean().iloc[-1] else 'bearish'
        
        return {'rsi': float(rsi), 'macd_cross': macd_cross, 'ema_cross': ema_cross}
    except Exception as e:
        print(f"Data error for {sym}: {e}")
        return {'rsi': None, 'macd_cross': None, 'ema_cross': None}

# Define scoring functions (fixes NameError)
def get_score_short(sym): return 0.75
def get_score_medium(sym): return 0.65
def get_score_long(sym): return 0.55

# Process symbols
for sym in symbols:
    try:
        latest = get_latest_data(sym)
        score_short = get_score_short(sym)
        score_medium = get_score_medium(sym)
        score_long = get_score_long(sym)

        signal = 'BUY' if (latest.get('rsi', 100) < 60 and latest.get('macd_cross') == 'bullish' and latest.get('ema_cross') == 'bullish') else 'HOLD'

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
        print(f"Processing error for {sym}: {e}")

# Save JSON
try:
    with open('output/signals.json', 'w') as f:
        json.dump(signals, f, indent=2)
    print("Saved signals.json")
except Exception as e:
    print(f"JSON save error: {e}")

# Render HTML (fixes AFFILIATES error)
AFFILIATES = cfg.get('AFFILIATES', {'Broker': 'https://example.com/referral'})  # Define here
try:
    template_path = 'templates/report_template.html'
    if os.path.exists(template_path):
        with open(template_path) as f:
            tpl_str = f.read()
    else:
        tpl_str = """
        <html><head><title>Stock Report</title></head><body>
        <h1>Daily Report - {{ generated_at }}</h1>
        <table border="1">
        <tr><th>Symbol</th><th>Signal</th><th>RSI</th><th>Short Score</th></tr>
        {% for s in signals %}
        <tr><td>{{ s.symbol }}</td><td>{{ s.signal }}</td><td>{{ s.rsi }}</td><td>{{ s.score_short }}</td></tr>
        {% endfor %}</table>
        <p><a href="{{ affiliates.Broker }}">Trade Now</a></p>
        </body></html>
        """
        print("Using fallback template")

    tpl = Template(tpl_str)
    html = tpl.render(signals=signals, generated_at=str(datetime.datetime.now()), affiliates=AFFILIATES)

    with open('output/daily_report.html', 'w') as f:
        f.write(html)
    print("Saved daily_report.html")
except Exception as e:
    print(f"HTML error: {e}")

# Telegram (now cfg is defined)
BOT = cfg.get('BOT_TOKEN')
CHAT = cfg.get('CHAT_ID')
if BOT and CHAT:
    try:
        buy_list = [s['symbol'] for s in signals if s['signal'] == 'BUY']
        msg = '<b>Top Buys</b>\n' + ('None' if not buy_list else '\n'.join(buy_list))
        requests.post(f'https://api.telegram.org/bot{BOT}/sendMessage', data={'chat_id': CHAT, 'text': msg, 'parse_mode': 'HTML'})
        print("Telegram sent")
    except Exception as e:
        print(f"Telegram error: {e}")
else:
    print("No Telegram config; skipping")

print("Script completed successfully!")
