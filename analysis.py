import json
import datetime
import os
import requests
from jinja2 import Template
import yfinance as yf  # For real stock data

# Create output folder if it doesn't exist
os.makedirs('output', exist_ok=True)

# Load config from config.json or use defaults (defines 'cfg')
cfg = {}
cfg_path = 'config.json'
if os.path.exists(cfg_path):
    try:
        with open(cfg_path, 'r') as f:
            cfg = json.load(f)
        print("Loaded config from config.json")
    except Exception as e:
        print(f"Error loading config: {e}. Using defaults.")
else:
    print(f"No {cfg_path} found. Using defaults.")

# Define AFFILIATES (fixes NameError)
AFFILIATES = cfg.get('AFFILIATES', {'Broker': 'https://example.com/referral'})

# Initialize fundamentals dictionary
fundamentals = {'PE': None, 'ROE': None}

# Initialize signals list
signals = []

# Example list of symbols (edit as needed)
symbols = ['AAPL', 'MSFT', 'GOOG']

# Define get_latest_data function (fixes NameError)
def get_latest_data(sym):
    try:
        print(f"Fetching data for {sym}...")
        stock = yf.Ticker(sym)
        hist = stock.history(period='1mo')  # Get last month's data
        if hist.empty:
            raise ValueError(f"No data available for {sym}")
        
        # Calculate RSI (14-day)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1] if not loss.iloc[-1] == 0 else 100
        
        # Simple MACD cross (short EMA > long EMA = bullish)
        macd_cross = 'bullish' if hist['Close'].rolling(window=12).mean().iloc[-1] > hist['Close'].rolling(window=26).mean().iloc[-1] else 'bearish'
        
        # EMA cross (price > 50-day EMA = bullish)
        ema_cross = 'bullish' if hist['Close'].iloc[-1] > hist['Close'].rolling(window=50).mean().iloc[-1] else 'bearish'
        
        return {
            'rsi': float(rsi),
            'macd_cross': macd_cross,
            'ema_cross': ema_cross
        }
    except Exception as e:
        print(f"Error fetching data for {sym}: {e}")
        return {'rsi': None, 'macd_cross': None, 'ema_cross': None}

# Define scoring functions (fixes NameError)
def get_score_short(sym):
    return 0.75  # Placeholder: Customize based on short-term indicators

def get_score_medium(sym):
    return 0.65  # Placeholder

def get_score_long(sym):
    return 0.55  # Placeholder

# Loop over symbols
for sym in symbols:
    try:
        # Fetch data and scores (now functions are defined)
        latest = get_latest_data(sym)
        score_short = get_score_short(sym)
        score_medium = get_score_medium(sym)
        score_long = get_score_long(sym)

        # Simple signal rule
        signal = 'BUY' if (
            latest.get('rsi', 100) < 60
            and latest.get('macd_cross') == 'bullish'
            and latest.get('ema_cross') == 'bullish'
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
        print(f"Processed {sym}: {signal} (RSI: {rec['rsi']})")

    except Exception as e:
        print(f'Error processing {sym}: {e}')

# Save JSON safely (now cfg and AFFILIATES are defined)
try:
    with open('output/signals.json', 'w') as f:
        json.dump(signals, f, indent=2)
    print("Saved signals.json")
except Exception as e:
    print('Error saving JSON:', e)

# Render HTML report
try:
    template_path = 'templates/report_template.html'
    if os.path.exists(template_path):
        with open(template_path, 'r') as f:
            template_content = f.read()
        print("Loaded report template from file")
    else:
        # Fallback template (basic HTML table)
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
            <p>Affiliate Broker: <a href="{{ affiliates.Broker }}">Trade Now</a></p>
        </body>
        </html>
        """
        print("Using fallback template")

    tpl = Template(template_content)
    html = tpl.render(
        signals=signals,
        generated_at=str(datetime.datetime.now()),
        affiliates=AFFILIATES  # Now defined
    )

    REPORT_PATH = 'output/daily_report.html'
    with open(REPORT_PATH, 'w') as f:
        f.write(html)
    print(f"Saved report to {REPORT_PATH}")

except Exception as e:
    print('Error rendering HTML report:', e)

# Telegram alert (now cfg is defined)
BOT = cfg.get('BOT_TOKEN')  # Line 78 fixed
CHAT = cfg.get('CHAT_ID')

if BOT and CHAT:
    try:
        buy_list = [s['symbol'] for s in signals if s['signal'] == 'BUY']
        msg = '<b>Top Buys</b>\n' + ('None' if not buy_list else '\n'.join(buy_list))

        response = requests.post(
            f'https://api.telegram.org/bot{BOT}/sendMessage',
            data={'chat_id': CHAT, 'text': msg, 'parse_mode': 'HTML'}
        )
        response.raise_for_status()
        print("Telegram alert sent successfully!")
    except Exception as e:
        print('Telegram error:', e)
else:
    print("Skipping Telegram (no BOT_TOKEN or CHAT_ID in config)")

print('Done. Reports written to', REPORT_PATH)
