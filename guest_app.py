import streamlit as st
import pandas as pd
import datetime
import urllib.parse

st.set_page_config(page_title="Enterprise Restaurant CRM", layout="wide")

# ==========================
# ENTERPRISE THEME CSS
# ==========================

st.markdown("""
<style>
body {
    background-color: #0f172a;
}
.stApp {
    background: linear-gradient(145deg, #0f172a, #111827);
    color: white;
}
.card {
    background: #1e293b;
    padding: 25px;
    border-radius: 20px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.5);
    margin-bottom: 20px;
    transition: 0.3s ease-in-out;
}
.card:hover {
    transform: translateY(-5px);
}
.badge {
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}
.excellent { background:#16a34a; }
.good { background:#2563eb; }
.average { background:#f59e0b; }
.poor { background:#dc2626; }
.metric-card {
    background:#1e293b;
    padding:20px;
    border-radius:18px;
    text-align:center;
}
</style>
""", unsafe_allow_html=True)

# ==========================
# LOGIN SYSTEM
# ==========================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.data = []

def login():
    st.title("Enterprise CRM Login")

    username = st.text_input("User ID")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.session_state.role = "admin"
        elif username == "staff" and password == "staff123":
            st.session_state.logged_in = True
            st.session_state.role = "staff"
        else:
            st.error("Invalid Credentials")

if not st.session_state.logged_in:
    login()
    st.stop()

st.sidebar.success(f"Logged in as {st.session_state.role}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ==========================
# MENU
# ==========================

if st.session_state.role == "admin":
    menu = st.sidebar.radio("Menu", ["Staff Entry", "Feedback Form", "Dashboard"])
else:
    menu = st.sidebar.radio("Menu", ["Staff Entry"])

# ==========================
# STAFF ENTRY
# ==========================

if menu == "Staff Entry":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.title("Staff Entry Panel")

    guest_name = st.text_input("Guest Name")
    mobile = st.text_input("Mobile Number")
    guest_count = st.number_input("Number of Guests", min_value=1)
    source = st.selectbox("Order Source", ["Zomato", "Swiggy", "Easy Dinner", "Party"])

    if st.button("Save Entry"):

        entry = {
            "Date": datetime.datetime.now(),
            "Guest Name": guest_name,
            "Mobile": mobile,
            "Guest Count": guest_count,
            "Source": source,
            "Rating": None,
            "Suggestion": None,
            "Sentiment": None
        }

        st.session_state.data.append(entry)

        feedback_link = "YOUR_APP_LINK_HERE"
        message = f"Thank you for visiting! Please share feedback here: {feedback_link}"
        encoded_message = urllib.parse.quote(message)

        whatsapp_link = f"https://wa.me/91{mobile}?text={encoded_message}"

        st.success("Entry Saved Successfully!")
        st.markdown(f"[📲 Send Feedback on WhatsApp]({whatsapp_link})")

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# FEEDBACK FORM
# ==========================

elif menu == "Feedback Form":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.title("Guest Experience Feedback")

    mobile_search = st.text_input("Enter Mobile Number")

    record = None
    for item in st.session_state.data:
        if item["Mobile"] == mobile_search:
            record = item
            break

    if record:

        rating = st.slider("Rate Your Experience", 1, 5, 5)
        suggestion = st.text_area("Your Suggestions")

        if rating >= 4:
            sentiment = "Positive"
        elif rating == 3:
            sentiment = "Neutral"
        else:
            sentiment = "Negative"

        if st.button("Submit Feedback"):

            record["Rating"] = rating
            record["Suggestion"] = suggestion
            record["Sentiment"] = sentiment

            st.success("🎉 Thank You For Your Feedback!")
            st.balloons()

    else:
        if mobile_search != "":
            st.warning("No Record Found")

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# DASHBOARD
# ==========================

elif menu == "Dashboard":

    st.title("Enterprise Admin Dashboard")

    if len(st.session_state.data) == 0:
        st.info("No Data Available")
    else:

        df = pd.DataFrame(st.session_state.data)

        total_entries = len(df)
        total_guests = df["Guest Count"].sum()
        avg_rating = df["Rating"].dropna().mean()
        if pd.isna(avg_rating):
            avg_rating = 0

        col1, col2, col3 = st.columns(3)

        col1.markdown(f'<div class="metric-card"><h3>Total Entries</h3><h2>{total_entries}</h2></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-card"><h3>Total Guests</h3><h2>{total_guests}</h2></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="metric-card"><h3>Avg Rating</h3><h2>{round(avg_rating,2)}</h2></div>', unsafe_allow_html=True)

        low = df[df["Rating"] <= 2]
        if not low.empty:
            st.error("⚠ Low Rating Alert! Immediate Attention Needed!")

        st.subheader("Customer Data")
        st.dataframe(df)

        st.subheader("Order Source Analytics")
        st.bar_chart(df["Source"].value_counts())
