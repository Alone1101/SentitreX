import azure.functions as func
import logging
import requests
import datetime
import os
import hashlib

app = func.FunctionApp()

@app.timer_trigger(schedule="0 */15 * * * *", arg_name="mytimer", run_on_startup=True)
@app.cosmos_db_output(arg_name="outputDocument", 
                      database_name="sentitrex-market-db", 
                      container_name="newsArticles", 
                      connection="CosmosDbConnectionString")
def sentiment_scraper(mytimer: func.TimerRequest, outputDocument: func.Out[func.Document]) -> None:
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    symbol = "SOXL"
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        news_items = data.get("feed", [])
        
        if not news_items:
            logging.warning("No news items found in Alpha Vantage response.")
            return

        processed_articles = []
        for article in news_items:
            raw_url = article.get("url", "")
            safe_id = hashlib.md5(raw_url.encode('utf-8')).hexdigest() if raw_url else "unknown-id"

            doc = {
                "id": safe_id,
                "articleId": safe_id,
                "ticker": "SOXL",
                "sourceName": article.get("source"),
                "title": article.get("title"),
                "articleUrl": raw_url,
                "publishedAt": article.get("time_published"),
                "sentiment": {
                    "sentimentScore": float(article.get("overall_sentiment_score", 0)),
                    "relevanceScore": float(article.get("relevance_score", 0)),
                    "sentimentLabel": article.get("overall_sentiment_label"),
                    "sentimentTimestamp": datetime.datetime.utcnow().isoformat()
                }
            }
            processed_articles.append(func.Document.from_dict(doc))
        
        if processed_articles:
            outputDocument.set(processed_articles)
            logging.info(f"Successfully saved {len(processed_articles)} articles.")

    except Exception as e:
        logging.error(f"Error during scraping: {str(e)}")