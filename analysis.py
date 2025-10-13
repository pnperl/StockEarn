import json
import datetime
import requests
from jinja2 import Template

fundamentals = {'PE': None, 'ROE': None}

try:
    # simple signal rule
    signal = 'BUY' if (latest['rsi'] < 60 and latest['macd_cross'] == 'bullish' and latest['ema_cross'] == 'bullish') else 'HOLD'

    rec = {
        'symbol': sym,
        'score_short': round(score_short, 2),
        'score_medium': round(score_medium, 2),
        'score_long': round(score_long, 2),
        'signal': signal,
        'rsi': round(latest['rsi'], 2) if latest['rsi'] else None,
        'macd_cross': latest['macd_cross'],
        'ema_cross': latest['ema_cross'],
        'fundamentals': fundamentals
    }
    signals.append(rec)

except Exception as e:
    print('Error', sym, e)

# Save JSON
try:
    with open('output/signals.json', 'w') as f:
        json.dump(signals, f, indent=2)
except Exception as e:
    print('Error saving JSON', e)

# Render HTML report
try:
    with open('templates/report_template.html') as f:
        tpl = Template(f.read())
    html = tpl.render(
        signals=signals,
        generated_at=str(datetime.datetime.now()),
        affiliates=AFFILIATES
    )
    with open(REPORT_PATH, 'w') as f:
        f.write(html)
except Exception as e:
    print('Error rendering HTML', e)

# Telegram alert
BOT = cfg.get('BOT_TOKEN')
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
        print('Telegram error', e)

print('Done. Reports written to', REPORT_PATH)
