# app.py

# Streamlit Enhanced Stock Screener
!pip install yfinance textblob streamlit requests beautifulsoup4

import streamlit as st
import yfinance as yf
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd

st.title("📈 Stock Screener with Akash")

# -----------------------
# 1. User Inputs
# -----------------------
stock_name = st.text_input("Enter Stock Name (e.g., Sagility)")
base_date = st.date_input("Select Base Date")

if stock_name:
    stock_symbol = stock_name.upper() + ".NS"  # Auto convert to NSE symbol

    # -----------------------
    # 2. Check 5% target in 15 days
    # -----------------------
    def check_5pct_target(stock_symbol, base_date):
        try:
            ticker = yf.Ticker(stock_symbol)
            base = pd.to_datetime(base_date)
            hist = ticker.history(start=base, end=base + timedelta(days=15))
            if hist.empty:
                return False
            base_price = hist['Close'][0]
            for price in hist['Close']:
                if price >= base_price * 1.05:
                    return True
            return False
        except:
            return False

    # -----------------------
    # 3. Sector Trend
    # -----------------------
    def fetch_sector_trend(stock_symbol, base_date):
        try:
            ticker = yf.Ticker(stock_symbol)
            sector = ticker.info.get("sector", "")
            if not sector:
                return True
            sector_index_map = {
                "Technology": "^NSEIT",
                "Pharmaceuticals": "^NSEPHARMA",
                "Healthcare": "^NSEHC",
                "Finance": "^NSEFIN",
                "Energy": "^NSENRG",
                "Automobile": "^NSEAUTO"
            }
            sector_idx = sector_index_map.get(sector, "")
            if not sector_idx:
                return True
            sec_ticker = yf.Ticker(sector_idx)
            hist = sec_ticker.history(period="1mo")
            base = pd.to_datetime(base_date)
            week_data = hist[(hist.index < base) & (hist.index >= base - timedelta(days=7))]
            if week_data.empty:
                return True
            change_pct = (week_data['Close'][-1] - week_data['Close'][0]) / week_data['Close'][0] * 100
            return change_pct > 0
        except:
            return True

    # -----------------------
    # 4. News Sentiment
    # -----------------------
    def fetch_news_sentiment(stock_name):
        try:
            url = f"https://www.google.com/search?q={stock_name}+stock&tbm=nws"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            headlines = [h.get_text() for h in soup.find_all('div', class_='BNeawe vvjwJb AP7Wnd')][:5]
            scores = [TextBlob(h).sentiment.polarity for h in headlines]
            avg_score = sum(scores)/len(scores) if scores else 0
            return avg_score >= 0
        except:
            return True

    # -----------------------
    # 5. Evaluate
    # -----------------------
    hit_5pct = check_5pct_target(stock_symbol, base_date)
    sector_up = fetch_sector_trend(stock_symbol, base_date)
    news_positive = fetch_news_sentiment(stock_name)
    recommended = sector_up and news_positive

    # -----------------------
    # 6. Display results
    # -----------------------
    st.subheader(f"Results for {stock_symbol}")
    st.write(f"✅ Recommended: {recommended}")
    st.write(f"📈 Hit 5% Target in 15 Days: {hit_5pct}")
    st.write(f"🏭 Sector Trend Positive: {sector_up}")
    st.write(f"📰 News Sentiment Positive: {news_positive}")