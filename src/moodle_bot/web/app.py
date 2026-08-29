import io
import time
import threading
import asyncio
from datetime import datetime, timezone

from PIL import Image
import segno
import streamlit as st
from neonize.client import NewClient
from neonize.events import ConnectedEv, PairStatusEv, event

from moodle_bot.config import SESSION_DB_PATH
from moodle_bot.models import UserSession, EnrolledCourse, db
from moodle_bot.chat.sender import send_message as send_msg
from moodle_bot.moodle.tracker import check_course_changes
from moodle_bot.moodle.courses import fetch_enrolled_courses
from moodle_bot.moodle.services.login import get_token, userinfo


class State:
    qr_img = None
    connected = False
    phone_number = None
    client_instance = None
    is_shutting_down = False
    last_check_time = None


@st.cache_resource
def get_shared_state():
    return State()


state = get_shared_state()


def run_course_checker(client):
    """Background worker that periodically checks Moodle for course changes every 5 minutes."""
    while True:
        try:
            check_course_changes(client)
            state.last_check_time = datetime.now(timezone.utc)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"[{now_str}] Course check cycle completed. Sleeping for 5 minutes until next check..."
            )
        except Exception as e:
            print(f"Error checking course changes: {e}")
        time.sleep(300)


def run_neonize():
    """Background worker that connects to Neonize and handles WhatsApp login state."""
    client = NewClient(str(SESSION_DB_PATH))
    state.client_instance = client

    @client.qr
    def on_qr(client_instance: NewClient, qr_data: bytes):
        qr = segno.make_qr(qr_data)
        buffer = io.BytesIO()
        qr.save(buffer, kind="png", scale=8)
        buffer.seek(0)
        state.qr_img = Image.open(buffer)

    @client.event(PairStatusEv)
    def on_pair_status(client_instance: NewClient, ev: PairStatusEv):
        if ev.ID and ev.ID.User:
            state.phone_number = ev.ID.User
            state.connected = True
            state.qr_img = None

    @client.event(ConnectedEv)
    def on_connected(client_instance: NewClient, ev: ConnectedEv):
        state.connected = True
        state.qr_img = None
        state.is_shutting_down = False

    def auto_detect_existing_session():
        time.sleep(3)
        if SESSION_DB_PATH.exists() and state.qr_img is None:
            state.connected = True

    threading.Thread(target=auto_detect_existing_session, daemon=True).start()

    client.connect()
    event.wait()


st.set_page_config(
    page_title="AI-Powered Moodle-to-WhatsApp Notification",
    page_icon="🎓",
    layout="centered",
)

# Custom CSS for modern styling and layout
st.markdown(
    """
    <style>
        .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .custom-card {
            background-color: var(--background-secondary-color, #f8f9fa);
            border: 1px solid var(--border-color, #e9ecef);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        }
        
        .stepper-wrapper {
            display: flex;
            justify-content: space-between;
            margin-bottom: 25px;
            padding: 12px 18px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            border: 1px solid rgba(128, 128, 128, 0.2);
        }
        .step-item {
            display: flex;
            align-items: center;
            font-size: 0.88rem;
            font-weight: 500;
        }
        .step-item.active {
            color: #25D366;
            font-weight: 600;
        }
        .step-item.completed {
            color: #0d6efd;
        }
        
        .feature-item {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
            font-size: 0.95rem;
        }
        
        .main-header {
            text-align: center;
            margin-bottom: 20px;
        }
        .main-header h1 {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 5px;
        }
        .main-header p {
            color: #6c757d;
            font-size: 0.95rem;
        }
    </style>
""",
    unsafe_allow_html=True,
)


def render_stepper(current_step: int):
    """Renders a visual step progress indicator."""
    s1_class = (
        "completed" if current_step > 1 else ("active" if current_step == 1 else "")
    )
    s2_class = (
        "completed" if current_step > 2 else ("active" if current_step == 2 else "")
    )
    s3_class = (
        "completed" if current_step > 3 else ("active" if current_step == 3 else "")
    )

    s1_icon = "✅" if current_step > 1 else "1️⃣"
    s2_icon = "✅" if current_step > 2 else "2️⃣"
    s3_icon = "✅" if current_step > 3 else "3️⃣"

    st.markdown(
        f"""
        <div class="stepper-wrapper">
            <div class="step-item {s1_class}"><span>{s1_icon} Google Auth</span></div>
            <div class="step-item {s2_class}"><span>{s2_icon} Moodle Setup</span></div>
            <div class="step-item {s3_class}"><span>{s3_icon} WhatsApp Link</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


_, center_col, _ = st.columns([1, 3.5, 1])

# Screen 1: Google Login
if not getattr(st.user, "is_logged_in", False):
    with center_col:
        render_stepper(1)

        st.markdown(
            """
            <div class="main-header">
                <h1>🎓 Moodle Notifications</h1>
                <p>Get instant AI-summarized Moodle updates delivered to WhatsApp</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown("### 🔒 Welcome")
            st.write("Please sign in with your Google account to get started.")

            st.markdown(
                """
                <div style="margin: 15px 0;">
                    <div class="feature-item">⚡ <span><b>Real-time course updates</b> directly to WhatsApp</span></div>
                    <div class="feature-item">🤖 <span><b>AI Summaries</b> of announcements & assignments</span></div>
                    <div class="feature-item">🔐 <span><b>Secure login</b> with Google & Moodle credentials</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.button(
                "🔑 Sign in with Google",
                on_click=st.login,
                use_container_width=True,
                type="primary",
            )

    st.stop()


# Update or insert current user session
user_sub = getattr(st.user, "sub", None) or getattr(st.user, "email", None)
session_record = UserSession.get_or_none(UserSession.id == 1)
if session_record:
    UserSession.update(google_id=user_sub).where(UserSession.id == 1).execute()
else:
    UserSession.create(id=1, google_id=user_sub)

session_record = UserSession.get_or_none(UserSession.google_id == user_sub)
user_id = getattr(session_record, "userid", None) if session_record else None

# Screen 2: Moodle Setup Form
if not user_id:
    with center_col:
        render_stepper(2)

        st.markdown(
            f"""
            <div class="main-header">
                <h1>📚 Connect Moodle Account</h1>
                <p>Welcome <b>{getattr(st.user, "name", "User")}</b> ({user_sub})</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.write("Please enter your Moodle account credentials below:")

            with st.form("login_form"):
                username = st.text_input(
                    "Username", placeholder="e.g. john_doe / Student ID"
                )
                password = st.text_input(
                    "Password", type="password", placeholder="••••••••"
                )
                your_site = st.text_input(
                    "Your Site URL",
                    placeholder="e.g. https://moodle.youruniversity.ac.lk",
                )
                phone_number = st.text_input(
                    "Preferred WhatsApp Number",
                    placeholder="e.g. 94771234567 (with country code, no + or spaces)",
                    help="Enter your WhatsApp number to receive Moodle update alerts.",
                )

                submitted = st.form_submit_button(
                    "Submit Moodle Details", use_container_width=True, type="primary"
                )

            if submitted:
                with st.spinner("Checking username and password..."):
                    result = asyncio.run(get_token(username, password, your_site))
                if result and result != "Invalid login, please try again":
                    userinfo(your_site, result)
                    fetch_enrolled_courses()
                    clean_phone = (
                        phone_number.strip()
                        .lstrip("+")
                        .replace(" ", "")
                        .replace("-", "")
                        if phone_number
                        else None
                    )
                    if clean_phone:
                        UserSession.update(phone_number=clean_phone).where(
                            (UserSession.google_id == user_sub) | (UserSession.id == 1)
                        ).execute()

                    session_record = UserSession.get_or_none(
                        UserSession.google_id == user_sub
                    )
                    site_name = getattr(session_record, "sitename", "LMS")
                    name = getattr(session_record, "lastname", "")
                    st.success(
                        f"🎉 {name}, your Moodle setup for {site_name} is completed!"
                    )
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error(
                        "❌ Your username or password is invalid. Please try again."
                    )
# Screen 3 & 4: WhatsApp Pairing & Main Bot Dashboard
else:
    with center_col:
        if "client_started" not in st.session_state:
            thread = threading.Thread(target=run_neonize, daemon=True)
            thread.start()
            st.session_state.client_started = True

        if not state.connected:
            render_stepper(3)

            st.markdown(
                """
                <div class="main-header">
                    <h1>💬 WhatsApp Connection</h1>
                    <p>Link your WhatsApp to start receiving automated notifications</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            status_placeholder = st.empty()
            qr_placeholder = st.empty()

            if state.qr_img:
                status_placeholder.info(
                    "📱 **Scan this QR code with WhatsApp to link your account:**\n\n"
                    "1. Open **WhatsApp** on your phone\n"
                    "2. Tap **Menu / Settings** ⚙️ > **Linked Devices**\n"
                    "3. Tap **Link a Device** and scan this QR code"
                )
                with qr_placeholder.container():
                    st.image(state.qr_img, caption="Scan with WhatsApp", width=300)
                time.sleep(2)
                st.rerun()
            else:
                with status_placeholder.container():
                    with st.spinner(
                        "⏳ Connecting to WhatsApp & generating QR code..."
                    ):
                        time.sleep(2)
                        st.rerun()
        else:
            # Screen 4: Main Bot Dashboard
            render_stepper(4)

            user_info = f" (+{state.phone_number})" if state.phone_number else ""
            userdata = UserSession.get_or_none(UserSession.google_id == user_sub)
            target_phone = getattr(userdata, "phone_number", None) if userdata else None
            if state.client_instance and not st.session_state.get("welcome_msg_sent"):
                send_msg(
                    state.client_instance,
                    f"""Dear,\n*{userdata.fullname}* \nLogging in successfully for *{userdata.sitename}*.\nMoodle-Bot is active!!!""",
                    phone_number=target_phone,
                )
                st.session_state["welcome_msg_sent"] = True

            if "checker_started" not in st.session_state and state.client_instance:
                checker_thread = threading.Thread(
                    target=run_course_checker,
                    args=(state.client_instance,),
                    daemon=True,
                )
                checker_thread.start()
                st.session_state["checker_started"] = True

            st.markdown(
                f"""
                <div class="main-header">
                    <h1>⚡ Moodle Bot Dashboard</h1>
                    <p>WhatsApp Paired Successfully{user_info}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.container(border=True):
                st.success(f"✅ WhatsApp connected{user_info}!")
                if target_phone:
                    st.info(f"📲 Notifications target: **+{target_phone}**")

                st.markdown("### 🤖 Bot Controls & Operations")
                st.write(
                    "Your bot is active and continuously monitoring Moodle for updates every 5 minutes."
                )
                if state.last_check_time:
                    st.info(
                        f"⏱️ Last check performed at: `{state.last_check_time.strftime('%Y-%m-%d %H:%M:%S UTC')}`"
                    )
                else:
                    st.info(
                        "⏳ Initial course change check running in the background..."
                    )

                courses = list(EnrolledCourse.select())
                with st.expander(f"📚 Monitored Courses ({len(courses)})", expanded=False):
                    if courses:
                        for c in courses:
                            st.markdown(f"- **{c.shortname}**: {c.fullname}")
                    else:
                        st.caption("No courses currently synced. Syncing will occur automatically during check.")

                with st.expander("⚙️ Update Preferred Notification Number"):
                    with st.form("update_phone_form"):
                        new_phone = st.text_input(
                            "Preferred WhatsApp Number",
                            value=target_phone or "",
                            placeholder="e.g. 94771234567 (with country code, no + or spaces)",
                        )
                        update_submitted = st.form_submit_button("Update Number")
                        if update_submitted:
                            clean_new_phone = (
                                new_phone.strip()
                                .lstrip("+")
                                .replace(" ", "")
                                .replace("-", "")
                                if new_phone
                                else None
                            )
                            UserSession.update(phone_number=clean_new_phone).where(
                                (UserSession.google_id == user_sub)
                                | (UserSession.id == 1)
                            ).execute()
                            st.success("✅ Preferred phone number updated!")
                            time.sleep(1)
                            st.rerun()
