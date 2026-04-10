import streamlit as st

st.set_page_config(
    page_title="SentitreX",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "api_url" not in st.session_state:
    st.session_state.api_url = "https://sentitrex-api-bmf6dvdchabkcedx.malaysiawest-01.azurewebsites.net/api"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

auth_page = st.Page("pages/1_Auth.py", title="Auth", icon=":material/login:")
dashboard_page = st.Page("pages/2_Dashboard.py", title="Dashboard", icon=":material/monitoring:")

pages = [dashboard_page] if st.session_state.authenticated else [auth_page]

pg = st.navigation(pages, position="hidden")
pg.run()