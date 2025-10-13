# analysis.py
fundamentals = {'PE': None, 'ROE': None}


# simple signal rule
signal = 'BUY' if (latest['rsi'] < 60 and latest['macd_cross']=='bullish' and latest['ema_cross']=='bullish') else 'HOLD'


rec = {
'symbol': sym,
'score_short': round(score_short,2),
'score_medium': round(score_medium,2),
'score_long': round(score_long,2),
'signal': signal,
'rsi': round(latest['rsi'],2) if latest['rsi'] else None,
'macd_cross': latest['macd_cross'],
'ema_cross': latest['ema_cross'],
'fundamentals': fundamentals
}
signals.append(rec)
except Exception as e:
print('Error', sym, e)


# Save JSON
with open('output/signals.json','w') as f:
json.dump(signals,f,indent=2)


# Render HTML report
with open('templates/report_template.html') as f:
tpl = Template(f.read())


html = tpl.render(signals=signals, generated_at=str(datetime.datetime.now()), affiliates=AFFILIATES)
with open(REPORT_PATH,'w') as f:
f.write(html)


# Telegram alert
BOT = cfg.get('BOT_TOKEN')
CHAT = cfg.get('CHAT_ID')
if BOT and CHAT:
buy_list = [s['symbol'] for s in signals if s['signal']=='BUY']
msg = '<b>Top Buys</b>\n' + ('None' if not buy_list else '\n'.join(buy_list))
try:
requests.post(f'https://api.telegram.org/bot{BOT}/sendMessage', data={'chat_id':CHAT,'text':msg,'parse_mode':'HTML'})
except Exception as e:
print('Telegram error', e)


print('Done. Reports written to', REPORT_PATH)
