import streamlit as st
from azure.cosmos import CosmosClient
import pandas as pd
import os

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="SentitreX Dashboard", page_icon="📈", layout="wide")
st.title("📈 SentitreX: Real-Time SOXL Sentiment & Price")
st.markdown("Monitoring the Direxion Daily Semiconductor Bull 3x Shares (SOXL)")

# --- 2. DATABASE CONNECTION ---
ENDPOINT = "https://sentitex-db.documents.azure.com:443/"
KEY = "TVBDiQoL18VIEf9Bwf35mNtWhSppYRDX560vKadGYIqfpVeJbwAuZ20npVj6UakPivTQkeNNBIYCACDbAO4omA=="

@st.cache_resource
def init_connection():
    return CosmosClient(ENDPOINT, credential=KEY)

try:
    client = init_connection()
    database = client.get_database_client("sentitrex-market-db")
    
    # Connect to Both containers
    news_container = database.get_container_client("newsArticles")
    price_container = database.get_container_client("priceSnapshots")
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

# --- 3. DATA FETCHING ---
@st.cache_data(ttl=300) # Cache the data for 5 minutes
def fetch_sentiment_data():
    query = """
        SELECT c.title, c.sourceName, c.publishedAt, c.sentiment.sentimentScore, c.sentiment.sentimentLabel 
        FROM c 
        WHERE c.ticker = 'SOXL'
    """
    items = list(news_container.query_items(query=query, enable_cross_partition_query=False, partition_key="SOXL"))
    return pd.DataFrame(items)

@st.cache_data(ttl=300) 
def fetch_price_data():
    query = """
        SELECT c.priceTimestamp, c.closePrice 
        FROM c 
        WHERE c.ticker = 'SOXL'
    """
    items = list(price_container.query_items(query=query, enable_cross_partition_query=False, partition_key="SOXL"))
    return pd.DataFrame(items)

# --- 4. RENDER THE UI ---
with st.spinner("Fetching latest market data..."):
    df_sentiment = fetch_sentiment_data()
    df_price = fetch_price_data()

if not df_sentiment.empty:
    # Clean up sentiment data
    df_sentiment['publishedAt'] = pd.to_datetime(df_sentiment['publishedAt'])
    df_sentiment = df_sentiment.sort_values(by='publishedAt')
    
    # Create Columns for Top-Level Metrics
    col1, col2, col3 = st.columns(3)
    avg_score = df_sentiment['sentimentScore'].mean()
    
    col1.metric("Articles Analyzed", len(df_sentiment))
    col2.metric("Average Sentiment Score", f"{avg_score:.2f}")
    col3.metric("Dominant Trend", "Bullish" if avg_score > 0.15 else "Bearish" if avg_score < -0.15 else "Neutral")

    st.divider()

    # --- CHARTS ---
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Market Price (SOXL)")
        if not df_price.empty:
            df_price['priceTimestamp'] = pd.to_datetime(df_price['priceTimestamp'])
            df_price = df_price.sort_values(by='priceTimestamp')
            
            # Show the current price as a metric
            latest_price = df_price.iloc[-1]['closePrice']
            st.metric("Latest Close Price", f"${latest_price:.2f}")
            
            # Plot the price chart
            price_chart_data = df_price.set_index('priceTimestamp')[['closePrice']]
            st.line_chart(price_chart_data, color="#00FF00") # Green line for money!
        else:
            st.warning("No price data yet. Waiting for scraper...")

    with chart_col2:
        st.subheader("Sentiment Timeline")
        st.metric("Sentiment Volatility", "Active")
        sentiment_chart_data = df_sentiment.set_index('publishedAt')[['sentimentScore']]
        st.line_chart(sentiment_chart_data, color="#FF0000") # Red line for news

    st.divider()

    # Raw Data Table
    st.subheader("Latest Headlines")
    df_sentiment['publishedAt'] = df_sentiment['publishedAt'].dt.strftime('%Y-%m-%d %H:%M')
    st.dataframe(df_sentiment[['publishedAt', 'sourceName', 'title', 'sentimentLabel', 'sentimentScore']], use_container_width=True)

else:
    st.warning("No data found. Is the scraper running?")