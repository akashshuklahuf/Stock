import yfinance as yf
from textblob import TextBlob
import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# -------------------------------
# Validate stock before running
# -------------------------------
def is_valid_stock(stock_symbol):
    try:
        ticker = yf.Ticker(stock_symbol)
        info = ticker.info
        return 'regularMarketPrice' in info and info['regularMarketPrice'] is not None
    except:
        return False

# -------------------------------
# Check 5% Target Logic
# -------------------------------
def check_5pct_target(stock_symbol, base_date):
    try:
        start_date = (base_date - timedelta(days=5)).strftime("%Y-%m-%d")
        end_date = (base_date + timedelta(days=15)).strftime("%Y-%m-%d")

        df = yf.download(stock_symbol, start=start_date, end=end_date)

        if df.empty:
            return f"No data for {stock_symbol}."

        if base_date.strftime("%Y-%m-%d") not in df.index.strftime("%Y-%m-%d"):
            return f"No trading data on {base_date.strftime('%Y-%m-%d')}."

        base_price = df.loc[base_date.strftime("%Y-%m-%d")]["Close"]
        target_price = base_price * 1.05
        max_price = df["High"].max()

        if max_price >= target_price:
            return f"✅ {stock_symbol}: Reached 5% target (Base {base_price:.2f} → Max {max_price:.2f})"
        else:
            return f"❌ {stock_symbol}: Did not reach 5% target (Base {base_price:.2f} → Max {max_price:.2f})"

    except Exception as e:
        return f"Error checking {stock_symbol}: {e}"

# -------------------------------
# Sector Trend
# -------------------------------
def check_sector_trend(stock_symbol):
    try:
        ticker = yf.Ticker(stock_symbol)
        sector = ticker.info.get("sector", "Unknown")

        if sector == "Unknown":
            return "Sector info not available"

        sector_etf_map = {
            "Technology": "XLK",
            "Financial Services": "XLF",
            "Healthcare": "XLV",
            "Energy": "XLE",
            "Consumer Cyclical": "XLY",
            "Industrials": "XLI"
        }

        if sector in sector_etf_map:
            etf = yf.Ticker(sector_etf_map[sector])
            hist = etf.history(period="1mo")
            if len(hist) > 0:
                change = (hist["Close"][-1] - hist["Close"][0]) / hist["Close"][0] * 100
                if change > 2:
                    return f"📈 Sector ({sector}) trending up +{change:.2f}%"
                elif change < -2:
                    return f"📉 Sector ({sector}) trending down {change:.2f}%"
                else:
                    return f"➖ Sector ({sector}) sideways ({change:.2f}%)"
        return f"Sector: {sector} (No ETF mapping)"
    except:
        return "Sector trend unavailable"

# -------------------------------
# News Sentiment
# -------------------------------
def check_news_sentiment(stock_name):
    try:
        url = f"https://news.google.com/search?q={stock_name}+stock&hl=en-IN&gl=IN&ceid=IN:en"
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")

        headlines = [h.text for h in soup.find_all("a", class_="DY5T1d")[:5]]
        if not headlines:
            return "No recent news found."

        sentiment_scores = [TextBlob(h).sentiment.polarity for h in headlines]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

        if avg_sentiment > 0.1:
            return f"🟢 Positive sentiment ({avg_sentiment:.2f})"
        elif avg_sentiment < -0.1:
            return f"🔴 Negative sentiment ({avg_sentiment:.2f})"
        else:
            return f"⚪ Neutral sentiment ({avg_sentiment:.2f})"
    except:
        return "News sentiment unavailable."

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("📊 Stock Screener (5% Target + Sector + Sentiment)")

stock_name = st.text_input("Enter stock name (e.g. Sagility, NTPC, Cipla)")
base_date = st.date_input("Select base date", datetime(2025, 9, 1))

if stock_name:
    stock_symbol = stock_name.upper() + ".NS"

    if not is_valid_stock(stock_symbol):
        st.error(f"❌ The stock '{stock_name}' is not valid on NSE.")
    else:
        st.success(f"✅ Valid stock: {stock_symbol}")
        st.write(check_5pct_target(stock_symbol, base_date))
        st.write(check_sector_trend(stock_symbol))
        st.write(check_news_sentiment(stock_name))
