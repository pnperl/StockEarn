import json
import datetime
import requests
from jinja2 import Template

# Initialize fundamentals dictionary
fundamentals = {'PE': None, 'ROE': None}

# Ensure signals list exists
signals = []

# Loop over your symbols (assuming you have a list `symbols`)
for sym in symbols:
    try:
        # Get latest data for this symbol (ensure latest is defined)
        latest = get_latest_data(sym)  # replace with your function
        score_short = get_score_short(sym)  # replace with your function
        score_medium = get_score_medium(sym)  # replace with your function
        score_long = get_score_long(sym)  # replace with your function

        # simple signal rule
        signal = 'BUY' if (
            latest['rsi'] < 60
            and latest['macd_cross'] == 'bullish'
            and latest['ema_cross'] == 'bullish'
        ) else 'HOLD'

        rec = {
            'symbol': sym,
            'score_short': round(score_short, 2),
            'score_medium': round(score_medium, 2),
            'score_long': round(score_long, 2),
            'signal': signal,
            'rsi': round(latest['rsi'], 2) if latest['rsi'] is not None else None,
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
        affiliates=AFFILIATES  # make sure AFFILIATES is defined
    )

    with open(REPORT_PATH, 'w') as f:
        f.write(html)

except Exception as e:
    print('Error rendering HTML report:', e)

# Telegram alert
BOT = cfg.get('BOT_TOKEN')  # ensure cfg is defined
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
