import azure.functions as func
import logging
import requests
import os
import datetime

app = func.FunctionApp()

@app.timer_trigger(schedule="0 */15 * * * *", arg_name="mytimer", run_on_startup=True)
def sentiment_scraper(mytimer: func.TimerRequest) -> None:
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    symbol = "SOXL"
    
    # URL for News Sentiment from Alpha Vantage
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # Log the number of articles found
        news_items = data.get("feed", [])
        logging.info(f"Found {len(news_items)} news items for {symbol}")
        
        # WIP to save 'data' into Cosmos DB
        logging.info("Scraper successfully executed and retrieved data.")
        
    except Exception as e:
        logging.error(f"Error during scraping: {str(e)}")