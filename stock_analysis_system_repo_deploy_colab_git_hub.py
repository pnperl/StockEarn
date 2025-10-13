# stock_analysis_system - Ready-to-deploy repository
# This single Python file contains all repository files as separate string constants.
# Save each block to its respective path in a new repo, then push to GitHub.

# === README.md ===
README = r"""
# Stock Analysis System — Automated, Monetization-Ready (Hybrid B)

This repository contains a ready-to-deploy, low-code, automation-first stock analysis system that:
- Runs multi-timeframe technical + fundamental analysis
- Produces an HTML daily report with affiliate buttons
- Sends Telegram alerts for top signals
- Is scheduled via GitHub Actions for daily automated runs
- Is designed for easy hosting (GitHub Pages / Streamlit) and monetization (Substack, affiliate links)

Files in this repo:
- analysis.py             -> Main runnable analysis script (can also be used in Colab)
- requirements.txt       -> Python dependencies
- config_sample.json     -> Sample config (replace with your keys)
- templates/report_template.html -> HTML template for reports
- .github/workflows/run.yml -> GitHub Actions scheduler
- output/                -> generated at runtime (daily_report.html, signals.json)

Quick deploy steps:
1. Create a new GitHub repo and push these files.
2. Add your Telegram BOT_TOKEN and CHAT_ID to config.json (rename from config_sample.json).
3. Configure affiliate links in templates/report_template.html.
4. Enable GitHub Actions in repo — scheduled job will run daily.
5. (Optional) Host output/daily_report.html via GitHub Pages or convert to Streamlit for subscription.

"""

# === requirements.txt ===
REQUIREMENTS = r"""
yfinance
pandas
numpy
matplotlib
mplfinance
requests
jinja2
pyyaml
"""

# === config_sample.json ===
CONFIG = r"""
{
  "BOT_TOKEN": "<telegram-bot-token>",
  "CHAT_ID": "<telegram-chat-id>",
  "AFFILIATES": {
    "zerodha": "https://zerodha.com/open-account?ref=YOUR_ID",
    "dhan": "https://dhan.co/?ref=YOUR_ID"
  },
  "SYMBOLS": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS"],
  "TIMEFRAMES": ["1d","1wk","1mo"],
  "REPORT_PATH": "output/daily_report.html"
}
"""

# === templates/report_template.html ===
TEMPLATE = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Daily Stock Report</title>
  <style>
    body {font-family: Arial, sans-serif; padding: 20px}
    .card {border:1px solid #ddd; padding:12px; margin:8px 0; border-radius:8px}
    .header {display:flex; justify-content:space-between}
    .symbols {display:flex; gap:12px; flex-wrap:wrap}
    .meta {font-size:0.9em;color:#666}
  </style>
</head>
<body>
  <div class="header">
    <h1>Daily Stock Report</h1>
    <div class="meta">Generated: {{ generated_at }}</div>
  </div>

  <h3>Top Picks</h3>
  <div class="symbols">
    {% for s in signals %}
    <div class="card">
      <h2>{{ s.symbol }}</h2>
      <div>Signal: <b>{{ s.signal }}</b></div>
      <div>Score (S/M/L): {{ s.score_short }} / {{ s.score_medium }} / {{ s.score_long }}</div>
      <div>RSI: {{ s.rsi }}, MACD: {{ s.macd_cross }}, EMA50/200: {{ s.ema_cross }}</div>
      <div>PE: {{ s.fundamentals.PE }} | ROE: {{ s.fundamentals.ROE }}</div>
      <p>
        <a href="{{ affiliates.zerodha }}" target="_blank">Trade on Zerodha</a> |
        <a href="{{ affiliates.dhan }}" target="_blank">Trade on Dhan</a>
      </p>
    </div>
    {% endfor %}
  </div>

  <hr>
  <footer>Automated report — update config.json to change symbols/timeframes.</footer>
</body>
</html>
"""

# === .github/workflows/run.yml ===
GHA = r"""
name: Daily Analysis Run
on:
  schedule:
    - cron: '30 2 * * *'  # 8:00 AM IST
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run analysis
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python analysis.py
      - name: Commit outputs
        run: |
          git config --global user.name 'github-actions'
          git config --global user.email 'actions@github.com'
          git add output || true
          if git diff --quiet --exit-code; then echo 'No changes'; else git commit -m 'Auto-update report' && git push; fi
"""

# === analysis.py ===
ANALYSIS = r"""
# analysis.py
# Usage: python analysis.py

import yfinance as yf
import pandas as pd
import numpy as np
import os, json, datetime
from jinja2 import Template
import requests

# -- helpers (lightweight indicators)
def rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(period).mean()
    ma_down = down.rolling(period).mean()
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))


def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()


def macd(series, fast=12, slow=26, signal=9):
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


# Load config
cfg_path = 'config.json'
if not os.path.exists(cfg_path):
    # try sample
    with open('config_sample.json') as f:
        cfg = json.load(f)
else:
    with open(cfg_path) as f:
        cfg = json.load(f)

SYMBOLS = cfg.get('SYMBOLS', ['RELIANCE.NS'])
TIMEFRAMES = cfg.get('TIMEFRAMES', ['1d'])
AFFILIATES = cfg.get('AFFILIATES', {})
REPORT_PATH = cfg.get('REPORT_PATH', 'output/daily_report.html')

os.makedirs('output', exist_ok=True)

signals = []

for sym in SYMBOLS:
    try:
        data = yf.download(sym, period='1y', interval='1d', progress=False)
        if data.empty:
            continue
        close = data['Close']
        r = rsi(close)
        macd_line, signal_line, hist = macd(close)
        ma50 = close.rolling(50).mean()
        ema200 = ema(close, 200)

        latest = {
            'symbol': sym,
            'rsi': float(r.iloc[-1]) if not r.empty else None,
            'macd_cross': 'bullish' if macd_line.iloc[-1] > signal_line.iloc[-1] else 'bearish',
            'ema_cross': 'bullish' if ma50.iloc[-1] > ema200.iloc[-1] else 'bearish'
        }

        # very simple scoring (example)
        score_short = (100 - latest['rsi'])/10 if latest['rsi'] else 5
        score_medium = score_short + (1 if latest['macd_cross']=='bullish' else -1)
        score_long = score_medium + (1 if latest['ema_cross']=='bullish' else -1)

        # dummy fundamentals (replace with real metrics if desired)
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
"""

# === End of file strings ===

# Helper: write files to disk for quick repo init
FILES = {
    'README.md': README,
    'requirements.txt': REQUIREMENTS,
    'config_sample.json': CONFIG,
    'templates/report_template.html': TEMPLATE,
    '.github/workflows/run.yml': GHA,
    'analysis.py': ANALYSIS
}

if __name__ == '__main__':
    for path, content in FILES.items():
        d = os.path.dirname(path)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(content)
    print('Repo skeleton written. Edit config.json with your keys, then push to GitHub.')
