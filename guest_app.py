import streamlit as st
import pandas as pd
import datetime
import uuid
import urllib.parse

st.set_page_config(page_title="Enterprise CRM", layout="wide")

# ------------------ THEME ------------------
st.markdown("""
<style>
body {background-color: #0f172a;}
.big-title {font-size:28px;font-weight:600;color:white;}
.card {
background:#111827;
padding:20px;
border-radius:15px;
box-shadow:0px 5px 20px rgba(0,0,0,0.4);
margin-bottom:20px;
}
button {
border-radius:8px !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------ SESSION INIT ------------------

if "data" not in st.session_state:
    st.session_state.data = []

if "feedback" not in st.session_state:
    st.session_state.feedback = []

if "edit_used" not in st.session_state:
    st.session_state.edit_used = {}

# ------------------ LOGIN SYSTEM ------------------

users = {
    "admin": {"password": "admin123", "role": "admin"},
    "staff1": {"password": "staff123", "role": "staff"},
    "staff2": {"password": "staff123", "role": "staff"},
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Enterprise CRM Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = users[username]["role"]
            st.rerun()
        else:
            st.error("Invalid Credentials")

    st.stop()

# ------------------ SIDEBAR ------------------

st.sidebar.title("CRM Panel")
menu = st.sidebar.radio("Navigation", [
    "Guest Entry",
    "Feedback Portal",
    "Dashboard",
    "Admin Panel"
])

st.sidebar.write(f"Logged in as: {st.session_state.username}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ------------------ GUEST ENTRY ------------------

if menu == "Guest Entry":
    st.markdown('<div class="big-title">Guest Entry Form</div>', unsafe_allow_html=True)

    with st.container():
        name = st.text_input("Guest Name")
        mobile = st.text_input("Mobile Number")
        date = st.date_input("Entry Date", datetime.date.today())

        if st.button("Save Entry"):
            entry_id = str(uuid.uuid4())[:8]

            st.session_state.data.append({
                "id": entry_id,
                "name": name,
                "mobile": mobile,
                "date": date,
                "created_by": st.session_state.username
            })

            st.success("Guest Entry Saved")

            # Generate Feedback Link
            app_link = "https://rjraunakapp.streamlit.app/"
            feedback_link = f"{app_link}?feedback_id={entry_id}"

            encoded = urllib.parse.quote(f"Please share your feedback here: {feedback_link}")
            whatsapp_url = f"https://wa.me/91{mobile}?text={encoded}"

            st.markdown(f"[📲 Send Feedback Link on WhatsApp]({whatsapp_url})")

# ------------------ FEEDBACK PORTAL ------------------

elif menu == "Feedback Portal":

    st.title("Guest Feedback Form")

    query_params = st.query_params
    feedback_id = query_params.get("feedback_id")

    if feedback_id:
        entry = next((x for x in st.session_state.data if x["id"] == feedback_id), None)

        if entry:
            rating = st.slider("Rate Us", 1, 5, 5)
            suggestion = st.text_area("Suggestion")

            if st.button("Submit Feedback"):
                st.session_state.feedback.append({
                    "guest": entry["name"],
                    "mobile": entry["mobile"],
                    "rating": rating,
                    "suggestion": suggestion,
                    "date": datetime.date.today()
                })

                st.success("Thank You For Your Feedback 🎉")
                st.balloons()
        else:
            st.error("Invalid Link")

    else:
        st.info("No Feedback ID Provided")

# ------------------ DASHBOARD ------------------

elif menu == "Dashboard":

    st.title("📊 Analytics Dashboard")

    if st.session_state.feedback:

        df = pd.DataFrame(st.session_state.feedback)

        st.metric("Total Feedback", len(df))
        st.metric("Average Rating", round(df["rating"].mean(),2))

        st.bar_chart(df["rating"].value_counts())

    else:
        st.info("No feedback yet.")

# ------------------ ADMIN PANEL ------------------

elif menu == "Admin Panel":

    if st.session_state.role != "admin":
        st.error("Admin Access Required")
        st.stop()

    st.title("🛠 Admin Panel")

    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        st.dataframe(df)

        # Download Excel
        excel = df.to_excel("guest_data.xlsx", index=False)
        with open("guest_data.xlsx", "rb") as f:
            st.download_button("Download Excel", f, file_name="guest_data.xlsx")

    if st.session_state.feedback:
        st.subheader("Feedback Records")
        df2 = pd.DataFrame(st.session_state.feedback)
        st.dataframe(df2)

        excel2 = df2.to_excel("feedback_data.xlsx", index=False)
        with open("feedback_data.xlsx", "rb") as f:
            st.download_button("Download Feedback Excel", f, file_name="feedback.xlsx")
