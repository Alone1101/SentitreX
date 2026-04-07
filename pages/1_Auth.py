import streamlit as st

st.set_page_config(page_title="SentitreX | Auth", page_icon="📈")

# State Definition
if "auth_busy" not in st.session_state:
    st.session_state.auth_busy = False

if "pending_auth_action" not in st.session_state:
    st.session_state.pending_auth_action = None

# Auth Logic
if st.session_state.pending_auth_action == "login":
    st.session_state.auth_busy = True
    with st.spinner("Signing in..."):
        # auth check add on from here later
        st.session_state.authenticated = True
        st.session_state.user_email = st.session_state.get("pending_email", "")
    st.session_state.pending_auth_action = None
    st.session_state.auth_busy = False
    st.rerun()

elif st.session_state.pending_auth_action == "register":
    st.session_state.auth_busy = True
    with st.spinner("Creating account..."):
        # DB logic add here later
        st.session_state.auth_mode = "login"
        st.session_state.auth_success_message = "Account created successfully. Please log in."
    st.session_state.pending_auth_action = None
    st.session_state.auth_busy = False
    st.rerun()

st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}

    .brand-title {
        text-align: center;
        font-size: 2rem;
        font-weight: 800;
        color: #e5eefc;
        margin-bottom: 0.25rem;
    }

    .brand-subtitle {
        text-align: center;
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }

    .auth-inline {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 0.35rem;
        margin-top: 1rem;
        color: #94a3b8;
        font-size: 0.95rem;
    }

    div[data-testid="stButton"] > button[kind="tertiary"] {
        background: none !important;
        border: none !important;
        color: #60a5fa !important;
        padding: 0 !important;
        min-height: auto !important;
        height: auto !important;
        text-decoration: underline;
        box-shadow: none !important;
        font-weight: 500;
    }

    div[data-testid="stButton"] > button[kind="tertiary"]:hover {
        color: #93c5fd !important;
    }
</style>
""", unsafe_allow_html=True)

# Auth message
# I never add the failed message, you can add if you want, just change here
if st.session_state.get("auth_success_message"):
    st.success(st.session_state.auth_success_message)
    del st.session_state["auth_success_message"]

left, center, right = st.columns([1.2, 1, 1.2])

with center:
    st.markdown('<div class="brand-title">📈 SentitreX</div>', unsafe_allow_html=True)

    if st.session_state.auth_mode == "login":
        st.markdown(
            '<div class="brand-subtitle">Real-Time SOXL Sentiment & Price Intelligence</div>',
            unsafe_allow_html=True
        )

        email = st.text_input("Email Address", placeholder="name@gmail.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")

        if st.button("Log in", use_container_width=True, disabled=st.session_state.auth_busy):
            st.session_state.pending_email = email
            st.session_state.pending_auth_action = "login"
            st.session_state.auth_busy = True
            st.rerun()

        st.markdown(
            """
            <div style="
                width: 100%;
                text-align: center;
                color: #94a3b8;
                margin-top: 1rem;
                font-size: 0.95rem;
            ">
                No account?
            </div>
            """,
            unsafe_allow_html=True,
        )

        link_left, link_mid, link_right = st.columns([1, 2, 1])
        with link_mid:
            if st.button(
                "Sign up here",
                key="to_register",
                type="tertiary",
                use_container_width=True,
                disabled=st.session_state.auth_busy
            ):
                st.session_state.auth_mode = "register"
                st.rerun()

    else:
        st.markdown(
            '<div class="brand-subtitle">Create your account</div>',
            unsafe_allow_html=True
        )

        full_name = st.text_input("Full Name", placeholder="John Doe")
        email = st.text_input("Email Address", placeholder="name@gmail.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")

        if st.button("Create Account", use_container_width=True, disabled=st.session_state.auth_busy):
            st.session_state.pending_register_name = full_name
            st.session_state.pending_register_email = email
            st.session_state.pending_auth_action = "register"
            st.session_state.auth_busy = True
            st.rerun()

        st.markdown(
            """
            <div style="
                width: 100%;
                text-align: center;
                color: #94a3b8;
                margin-top: 1rem;
                font-size: 0.95rem;
            ">
                Already have an account?
            </div>
            """,
            unsafe_allow_html=True,
        )

        link_left, link_mid, link_right = st.columns([1, 2, 1])
        with link_mid:
            if st.button("Log in here", key="to_login", type="tertiary", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()