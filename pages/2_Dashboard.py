import streamlit as st

if not st.session_state.get("authenticated", False):
    st.switch_page("pages/1_Auth.py")

import pandas as pd
import plotly.graph_objects as go
import html as html_lib
import requests
import os

if "logout_busy" not in st.session_state:
    st.session_state.logout_busy = False

if "pending_logout" not in st.session_state:
    st.session_state.pending_logout = False

# Logging out here
if st.session_state.pending_logout:
    st.session_state.logout_busy = True
    with st.spinner("Signing out..."):
        st.session_state.authenticated = False
        st.session_state.auth_mode = "login"

        for key in ["user_email", "user_name", "user_token", "user_role"]:
            if key in st.session_state:
                del st.session_state[key]

    st.session_state.pending_logout = False
    st.session_state.logout_busy = False
    st.rerun()

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="SentitreX Dashboard", 
                   page_icon="📈", 
                   layout="wide", 
                   initial_sidebar_state="collapsed")

header_left, header_right = st.columns([8, 1])

with header_left:
    st.title("📈 SentitreX: Real-Time SOXL Sentiment & Price")
    st.markdown("Monitoring the Direxion Daily Semiconductor Bull 3x Shares (SOXL)")

with header_right:
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    if st.button("↪ Sign out", use_container_width=True, disabled=st.session_state.logout_busy):
        st.session_state.pending_logout = True
        st.session_state.logout_busy = True
        st.rerun()

st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    .metric-card {
        text-align: center;
        padding: 0.5rem 0;
    }

    .metric-card [data-testid="stMetricLabel"] {
        justify-content: center;
    }

    .metric-card [data-testid="stMetricValue"] {
        justify-content: center;
    }

    .metric-card [data-testid="stMetricDelta"] {
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    .news-ticker-wrap {
        width: 100%;
        overflow: hidden;
        background: linear-gradient(90deg, #111827, #0f172a);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 0.65rem 0;
        margin: 0.75rem 0 1.25rem 0;
        white-space: nowrap;
        position: relative;
    }

    .news-ticker {
        display: inline-block;
        white-space: nowrap;
        padding-left: 100%;
        animation: ticker-scroll 175s linear infinite;
    }

    .news-ticker-wrap:hover .news-ticker {
        animation-play-state: paused;
    }

    .ticker-item {
        display: inline-flex;
        align-items: center;
        gap: 0.55rem;
        margin-right: 2.5rem;
        color: #e5e7eb;
        font-size: 0.96rem;
    }

    .ticker-source {
        color: #93c5fd;
        font-weight: 600;
    }

    .ticker-time {
        color: #9ca3af;
        font-size: 0.88rem;
    }

    .ticker-pill {
        padding: 0.2rem 0.55rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }

    .pill-bullish {
        background: rgba(34,197,94,0.18);
        color: #86efac;
        border: 1px solid rgba(34,197,94,0.28);
    }

    .pill-bearish {
        background: rgba(239,68,68,0.18);
        color: #fca5a5;
        border: 1px solid rgba(239,68,68,0.28);
    }

    .pill-neutral {
        background: rgba(148,163,184,0.16);
        color: #cbd5e1;
        border: 1px solid rgba(148,163,184,0.24);
    }

    .ticker-sep {
        color: #475569;
        margin: 0 0.2rem;
    }

    @keyframes ticker-scroll {
        0% {
            transform: translateX(0);
        }
        100% {
            transform: translateX(-100%);
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    button[data-baseweb="tab"] {
        font-size: 1rem;
        font-weight: 700;
        padding: 0.75rem 1.25rem;
        border-radius: 12px 12px 0 0;
        background-color: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        margin-right: 0.35rem;
    }

    button[data-baseweb="tab"]:hover {
        background-color: rgba(59,130,246,0.12);
        color: #dbeafe;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(180deg, rgba(59,130,246,0.24), rgba(37,99,235,0.14));
        color: white;
        border-bottom: 2px solid #60a5fa;
    }

    div[data-baseweb="tab-list"] {
        gap: 0.25rem;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

BASE_URL = st.session_state.get("api_url", "https://sentitrex-api-bmf6dvdchabkcedx.malaysiawest-01.azurewebsites.net/api")

def _auth_headers() -> dict:
    token = st.session_state.get("user_token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}

# --- 3. DATA FETCHING ---
@st.cache_data(ttl=300) 
def fetch_sentiment_data():
    try:
        resp = requests.get(f"{BASE_URL}/news", headers=_auth_headers(), timeout=15)
        
        if resp.status_code == 401:
            st.session_state.authenticated = False
            st.session_state.auth_mode = "login"
            st.rerun()

        # Check if the response actually has text before parsing JSON
        if resp.status_code == 200 and resp.text.strip():
            return pd.DataFrame(resp.json())
        else:
            st.warning("Backend is currently updating. Showing empty dataset for now.")
            return pd.DataFrame() 
            
    except Exception as e:
        st.error(f"Connection failed: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300) 
def fetch_price_data():
    try:
        resp = requests.get(f"{BASE_URL}/prices", headers=_auth_headers(), timeout=15)
        
        if resp.status_code == 401:
            st.session_state.authenticated = False
            st.session_state.auth_mode = "login"
            st.rerun()

        # Check if the response actually has text before parsing JSON
        if resp.status_code == 200 and resp.text.strip():
            return pd.DataFrame(resp.json())
        else:
            st.warning("📈 Market API is waking up. Please refresh in 30 seconds.")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Price data fetch error: {e}")
        return pd.DataFrame()

# --- 4. LOAD DATA ---
with st.spinner("Fetching latest market data..."):
    df_sentiment = fetch_sentiment_data()
    df_price = fetch_price_data()

# --- 5. CLEAN SENTIMENT DATA ---
if not df_sentiment.empty:
    df_sentiment["publishedAt"] = pd.to_datetime(df_sentiment["publishedAt"], errors="coerce")
    df_sentiment["sentimentScore"] = pd.to_numeric(df_sentiment["sentimentScore"], errors="coerce")
    df_sentiment = df_sentiment.dropna(subset=["publishedAt", "sentimentScore"])
    df_sentiment = df_sentiment.sort_values(by="publishedAt")

# --- 6. CLEAN PRICE DATA ---
if not df_price.empty:
    df_price["priceTimestamp"] = pd.to_datetime(df_price["priceTimestamp"], errors="coerce")

    for col in ["openPrice", "highPrice", "lowPrice", "closePrice", "volume"]:
        df_price[col] = pd.to_numeric(df_price[col], errors="coerce")

    df_price = df_price.dropna(
        subset=["priceTimestamp", "openPrice", "highPrice", "lowPrice", "closePrice", "volume"]
    )
    df_price = df_price.sort_values(by="priceTimestamp")

    df_price = df_price.set_index("priceTimestamp")

    df_price = df_price.resample("5min").agg({
        "openPrice": "first",
        "highPrice": "max",
        "lowPrice": "min",
        "closePrice": "last",
        "volume": "sum"
    }).dropna()

    df_price = df_price.reset_index()

# --- 7. Headlines ---
headline_ticker_html = ""

if not df_sentiment.empty:
    ticker_df = df_sentiment.sort_values(by="publishedAt", ascending=False).copy()

    # keep latest unique titles only
    ticker_df = ticker_df.drop_duplicates(subset=["title"]).head(10)

    ticker_items = []
    for _, row in ticker_df.iterrows():
        source = html_lib.escape(str(row.get("sourceName", "Unknown")))
        title = html_lib.escape(str(row.get("title", "No title")))
        label = html_lib.escape(str(row.get("sentimentLabel", "Neutral")).strip().title())
        timestamp = row["publishedAt"].strftime("%d %b %H:%M")

        if len(title) > 120:
            title = title[:117] + "..."

        if label.lower() == "bullish":
            pill_class = "pill-bullish"
        elif label.lower() == "bearish":
            pill_class = "pill-bearish"
        else:
            pill_class = "pill-neutral"

        ticker_items.append(f"""
            <span class="ticker-item">
                <span class="ticker-source">{source}</span>
                <span class="ticker-sep">•</span>
                <span>{title}</span>
                <span class="ticker-pill {pill_class}">{label}</span>
                <span class="ticker-time">{timestamp}</span>
            </span>
        """)

    if ticker_items:
        # duplicate content once so the scroll feels continuous
        ticker_content = "".join(ticker_items)
        headline_ticker_html = f"""
        <div class="news-ticker-wrap">
            <div class="news-ticker">
                {ticker_content}
                {ticker_content}
            </div>
        </div>
        """
if headline_ticker_html:
    st.markdown("##### Live Headlines")
    st.html(headline_ticker_html)

# --- 8. UNIFIED DASHBOARD ---
st.subheader("SOXL Market & Sentiment Overview")

if not df_price.empty:
    # 1. Calculate Market Metrics
    latest_price = df_price.iloc[-1]["closePrice"]
    latest_open = df_price.iloc[-1]["openPrice"]
    latest_high = df_price.iloc[-1]["highPrice"]
    latest_low = df_price.iloc[-1]["lowPrice"]
    latest_volume = df_price.iloc[-1]["volume"]
    latest_timestamp = df_price.iloc[-1]["priceTimestamp"]

    day_change = latest_price - latest_open
    day_change_pct = (day_change / latest_open * 100) if latest_open else 0
    
    # 2. Calculate Sentiment Metrics
    avg_score = df_sentiment["sentimentScore"].mean() if not df_sentiment.empty else 0
    dominant_trend = "Bullish" if avg_score > 0.15 else "Bearish" if avg_score < -0.15 else "Neutral"

    # 3. Display Top Metrics Row
    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Last Price", f"${latest_price:.2f}", f"{day_change_pct:+.2f}%")
        st.markdown('</div>', unsafe_allow_html=True)

    with m2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Volume", f"{int(latest_volume):,}")
        st.markdown('</div>', unsafe_allow_html=True)

    with m3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Intraday High/Low", f"${latest_high:.2f} / ${latest_low:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)

    with m4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Avg Sentiment Score", f"{avg_score:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)

    with m5:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Dominant Trend", dominant_trend)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.caption(f"Last updated: {latest_timestamp.strftime('%d %b %Y %H:%M')}")

    # --- 4. BUILD COMBINED CHART ---
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_price["priceTimestamp"],
        y=df_price["closePrice"],
        mode="lines+markers",
        name="SOXL Price",
        line=dict(color="#60a5fa", width=2),
        marker=dict(size=4),
        connectgaps=True
    ))

    # Volume Bar (Bottom Axis)
    fig.add_trace(go.Bar(
        x=df_price["priceTimestamp"],
        y=df_price["volume"],
        name="SOXL Volume",
        yaxis="y2",
        marker=dict(
            color="rgba(150, 150, 150, 0.4)",
            line=dict(color="rgba(200, 200, 200, 0.8)", width=1) # The 'line' outline forces it to be visible
        ) 
    ))

    # Sentiment Line (Overlaid, Right Axis)
    if not df_sentiment.empty:
        fig.add_trace(go.Scatter(
            x=df_sentiment["publishedAt"],
            y=df_sentiment["sentimentScore"],
            mode="lines+markers",
            name="Sentiment Score",
            yaxis="y3", 
            line=dict(color="#facc15", width=2), 
            marker=dict(size=6, color="#facc15"),
            connectgaps=True
        ))

    # Layout & Axes Setup
    fig.update_layout(
        template="plotly_dark",
        height=760,
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=30, b=20),
        
        yaxis=dict(title="Price", domain=[0.25, 1.0], side="left"),
        yaxis2=dict(title="Volume", domain=[0.0, 0.20], side="left"),
        yaxis3=dict(
            title="Sentiment (-1 to 1)", 
            overlaying="y", 
            side="right",   
            range=[-1.2, 1.2], 
            showgrid=False  
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, width="stretch", key="combined_market_sentiment_chart")

    # --- HEADLINES TABLE ---
    if not df_sentiment.empty:
        st.markdown("### Latest News & Articles")
        display_df = df_sentiment.sort_values(by="publishedAt", ascending=False).copy()
        display_df["publishedAt"] = display_df["publishedAt"].dt.strftime("%Y-%m-%d %H:%M")

        st.dataframe(
            display_df[["publishedAt", "sourceName", "title", "sentimentLabel", "sentimentScore"]],
            width="stretch",
            hide_index=True
        )
else:
    st.warning("No price data yet. Waiting for scraper...")
