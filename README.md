# Stock Analysis System — Automated, Monetization-Ready (Hybrid B)


This repository contains a ready-to-deploy, low-code, automation-first stock analysis system that:
- Runs multi-timeframe technical + fundamental analysis
- Produces an HTML daily report with affiliate buttons
- Sends Telegram alerts for top signals
- Is scheduled via GitHub Actions for daily automated runs
- Is designed for easy hosting (GitHub Pages / Streamlit) and monetization (Substack, affiliate links)


Files in this repo:
- analysis.py -> Main runnable analysis script (can also be used in Colab)
- requirements.txt -> Python dependencies
- config_sample.json -> Sample config (replace with your keys)
- templates/report_template.html -> HTML template for reports
- .github/workflows/run.yml -> GitHub Actions scheduler
- output/ -> generated at runtime (daily_report.html, signals.json)


Quick deploy steps:
1. Create a new GitHub repo and push these files.
2. Add your Telegram BOT_TOKEN and CHAT_ID to config.json (rename from config_sample.json).
3. Configure affiliate links in templates/report_template.html.
4. Enable GitHub Actions in repo — scheduled job will run daily.
5. (Optional) Host output/daily_report.html via GitHub Pages or convert to Streamlit for subscription.
