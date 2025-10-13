import json
import datetime
import os
import requests
from jinja2 import Template

# Ensure output folder exists
os.makedirs('output', exist_ok=True)

# Initialize fundamentals dictionary
fundamentals = {'PE': None, 'ROE': None}

# Ensure signals list exists
signals = []

# Example list of symbols (replace with your actual symbols list)
symbols = ['AAPL', 'MSFT', 'GOOG']  # replace with real symbols

# Loop over symbols
for sym in symbols:
    try:
        # Fetch or compute latest data and scores
        latest = get_latest_data(sym)       # define your own function
        score_short = get_score_short(sym)  # define your own function
        score_medium = get_score_medium(sym)  # define your own function
        score_long = get_score_long(sym)    # define your own function

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

    except Exception as e:
        print('Error processing', sym, e)

# Save JSON safely
try:
    with open('output/signals.json', 'w') as f:
        json.dump(signals, f, indent=2)
except Exception as e:
    print('Error saving JSON:', e)

# Render HTML report
try:
    with open('templates/report_template.html') as f:
        tpl = Template(f.read())

    html = tpl.render(
        signals=signals,
        generated_at=str(datetime.datetime.now()),
        affiliates=AFFILIATES  # ensure AFFILIATES dict/list is defined
    )

    REPORT_PATH = 'output/daily_report.html'
    with open(REPORT_PATH, 'w') as f:
        f.write(html)

except Exception as e:
    print('Error rendering HTML report:', e)

# Telegram alert
BOT = cfg.get('BOT_TOKEN')  # ensure cfg dict is defined
CHAT = cfg.get('CHAT_ID')

if BOT and CHAT:
    try:
        buy_list = [s['symbol'] for s in signals if s['signal'] == 'BUY']
        msg = '<b>Top Buys</b>\n' + ('None' if not buy_list else '\n'.join(buy_list))

        requests.post(
            f'https://api.telegram.org/bot{BOT}/sendMessage',
            data={'chat_id': CHAT, 'text': msg, 'parse_mode': 'HTML'}
        )
    except Exception as e:
        print('Telegram error:', e)

print('Done. Reports written to', REPORT_PATH)
