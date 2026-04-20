import streamlit as st
import requests

st.set_page_config(page_title="SentitreX | Auth", page_icon="📈")

BASE_URL = st.session_state.get(
    "api_url",
    "https://sentitrex-api-bmf6dvdchabkcedx.malaysiawest-01.azurewebsites.net/api"
)

# --- STATE INIT ---
defaults = {
    "auth_error": None,
    "auth_mode": "login",
    "authenticated": False,
    "login_busy": False,
    "register_busy": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def safe_error_message(response, fallback: str) -> str:
    try:
        data = response.json()
        return data.get("error") or data.get("message") or fallback
    except Exception:
        return fallback


def switch_to_login():
    st.session_state.auth_mode = "login"
    st.session_state.login_busy = False
    st.session_state.register_busy = False
    st.session_state.auth_error = None


def switch_to_register():
    st.session_state.auth_mode = "register"
    st.session_state.login_busy = False
    st.session_state.register_busy = False
    st.session_state.auth_error = None


# --- STYLES ---
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

div[data-testid="stButton"] > button[kind="tertiary"] {
    background: none !important;
    border: none !important;
    color: #60a5fa !important;
    padding: 0 !important;
    text-decoration: underline;
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

# --- LAYOUT ---
left, center, right = st.columns([1.2, 1, 1.2])

with center:
    st.markdown('<div class="brand-title">📈 SentitreX</div>', unsafe_allow_html=True)

    if st.session_state.auth_error:
        st.error(st.session_state.auth_error)
        st.session_state.auth_error = None

    # =========================
    # LOGIN
    # =========================
    if st.session_state.auth_mode == "login":
        st.markdown(
            '<div class="brand-subtitle">Real-Time SOXL Sentiment & Price Intelligence</div>',
            unsafe_allow_html=True
        )

        email = st.text_input(
            "Email Address",
            placeholder="name@gmail.com",
            key="login_email"
        )
        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        login_label = "Signing in..." if st.session_state.login_busy else "Log in"

        clicked = st.button(
            login_label,
            key="login_submit",
            use_container_width=True,
            disabled=st.session_state.login_busy
        )

        if clicked and not st.session_state.login_busy:
            st.session_state.login_busy = True
            st.rerun()

        if st.session_state.login_busy:
            try:
                response = requests.post(
                    f"{BASE_URL}/login",
                    json={"email": st.session_state.login_email, "password": st.session_state.login_password},
                    timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    st.session_state.authenticated = True
                    st.session_state.user_token = data.get("token")
                    st.session_state.user_role = data.get("role")
                    st.session_state.user_email = st.session_state.login_email
                    st.session_state.login_busy = False
                    st.rerun()
                else:
                    st.session_state.auth_error = safe_error_message(response, "Login failed")
                    st.session_state.login_busy = False
                    st.rerun()

            except Exception as e:
                st.session_state.auth_error = f"Connection error: {e}"
                st.session_state.login_busy = False
                st.rerun()

        st.markdown("<div style='text-align:center; margin-top:1rem;'>No account?</div>", unsafe_allow_html=True)

        if st.button(
            "Sign up here",
            key="go_register",
            type="tertiary",
            use_container_width=True,
            disabled=st.session_state.login_busy
        ):
            switch_to_register()
            st.rerun()

    # =========================
    # REGISTER
    # =========================
    else:
        st.markdown(
            '<div class="brand-subtitle">Create your account</div>',
            unsafe_allow_html=True
        )

        full_name = st.text_input("Full Name", key="register_full_name")
        email = st.text_input("Email Address", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")

        register_label = "Creating account..." if st.session_state.register_busy else "Create Account"

        clicked = st.button(
            register_label,
            key="register_submit",
            use_container_width=True,
            disabled=st.session_state.register_busy
        )

        if clicked and not st.session_state.register_busy:
            st.session_state.register_busy = True
            st.rerun()

        if st.session_state.register_busy:
            try:
                response = requests.post(
                    f"{BASE_URL}/register",
                    json={
                        "email": st.session_state.register_email,
                        "password": st.session_state.register_password,
                        "fullName": st.session_state.register_full_name,
                        "role": "user"
                    },
                    timeout=15
                )

                if response.status_code == 201:
                    st.session_state.register_busy = False
                    st.session_state.auth_mode = "login"
                    st.session_state.auth_error = "Account created successfully. Please log in."
                    st.rerun()
                else:
                    st.session_state.auth_error = safe_error_message(response, "Registration failed")
                    st.session_state.register_busy = False
                    st.rerun()

            except Exception as e:
                st.session_state.auth_error = f"Connection error: {e}"
                st.session_state.register_busy = False
                st.rerun()

        st.markdown("<div style='text-align:center; margin-top:1rem;'>Already have an account?</div>", unsafe_allow_html=True)

        if st.button(
            "Log in here",
            key="go_login",
            type="tertiary",
            use_container_width=True,
            disabled=st.session_state.register_busy
        ):
            switch_to_login()
            st.rerun()