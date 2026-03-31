import streamlit as st
from azure.cosmos import CosmosClient
import pandas as pd
import os

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="SentitreX Dashboard", page_icon="📈", layout="wide")
st.title("📈 SentitreX: Real-Time SOXL Sentiment")
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
    container = database.get_container_client("newsArticles")
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

# --- 3. DATA FETCHING ---
@st.cache_data(ttl=300) # Cache the data for 5 minutes
def fetch_sentiment_data():
    # Grab the data and sort it by newest first
    query = """
        SELECT c.title, c.sourceName, c.publishedAt, c.sentiment.sentimentScore, c.sentiment.sentimentLabel 
        FROM c 
        WHERE c.ticker = 'SOXL'
    """
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=False,
        partition_key="SOXL"
    ))
    return pd.DataFrame(items)

# --- 4. RENDER THE UI ---
with st.spinner("Fetching latest market data..."):
    df = fetch_sentiment_data()

if not df.empty:
    # Clean up data for display
    df['publishedAt'] = pd.to_datetime(df['publishedAt'])
    df = df.sort_values(by='publishedAt') # Sort oldest to newest for the chart
    
    # Create Columns for Top-Level Metrics
    col1, col2, col3 = st.columns(3)
    avg_score = df['sentimentScore'].mean()
    
    col1.metric("Articles Analyzed", len(df))
    col2.metric("Average Sentiment Score", f"{avg_score:.2f}")
    col3.metric("Dominant Trend", "Bullish" if avg_score > 0.15 else "Bearish" if avg_score < -0.15 else "Neutral")

    st.divider()

    # Chart
    st.subheader("Sentiment Timeline")
    # Set the timestamp as the index
    chart_data = df.set_index('publishedAt')[['sentimentScore']]
    st.line_chart(chart_data)

    # Raw Data Table
    st.subheader("Latest Headlines")
    # Format date
    df['publishedAt'] = df['publishedAt'].dt.strftime('%Y-%m-%d %H:%M')
    st.dataframe(df[['publishedAt', 'sourceName', 'title', 'sentimentLabel', 'sentimentScore']], use_container_width=True)

else:
    st.warning("No data found. Is the scraper running?")