import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Restaurant Intelligence CRM",
    page_icon="🍽️",
    layout="wide"
)

# ---------------- PREMIUM CSS ----------------
st.markdown("""
<style>
.main {
    background-color: #0e1117;
}
h1, h2, h3, h4 {
    color: white;
}
.stMetric {
    background-color: #1c1f26;
    padding: 15px;
    border-radius: 12px;
}
.block-container {
    padding-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("restaurant.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS visits(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    mobile TEXT,
    guest_count INTEGER,
    category TEXT,
    food_rating INTEGER,
    service_rating INTEGER,
    behaviour_rating INTEGER,
    date TEXT
)
""")
conn.commit()

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---------------- LOGIN ----------------
def login():
    st.markdown("<h1 style='text-align:center;'>🍽️ Restaurant Intelligence CRM</h1>", unsafe_allow_html=True)
    st.subheader("Login To Continue")

    role = st.selectbox("Login As", ["Admin", "Staff"])
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if role == "Admin" and password == "admin123":
            st.session_state.logged_in = True
            st.session_state.role = "Admin"
            st.rerun()
        elif role == "Staff" and password == "staff123":
            st.session_state.logged_in = True
            st.session_state.role = "Staff"
            st.rerun()
        else:
            st.error("Wrong Credentials")

# ---------------- STAFF PANEL ----------------
def staff_panel():
    st.title("📝 Guest Entry Panel")

    name = st.text_input("Guest Name")
    mobile = st.text_input("Mobile Number")
    guest_count = st.number_input("Number of Guests", 1, 20)
    category = st.selectbox("Category", ["Dine-In", "Delivery", "Takeaway"])

    food = st.slider("Food Rating", 1, 5)
    service = st.slider("Service Rating", 1, 5)
    behaviour = st.slider("Behaviour Rating", 1, 5)

    if st.button("Save Entry"):
        c.execute("""
        INSERT INTO visits(name, mobile, guest_count, category,
        food_rating, service_rating, behaviour_rating, date)
        VALUES (?,?,?,?,?,?,?,?)
        """, (name, mobile, guest_count, category,
              food, service, behaviour,
              datetime.now().strftime("%Y-%m-%d")))
        conn.commit()

        st.success("Entry Saved Successfully ✅")
        st.balloons()

    if st.button("Logout"):
        st.session_state.logged_in=False
        st.rerun()

# ---------------- ADMIN PANEL ----------------
def admin_panel():

    st.title("📊 Restaurant Intelligence Dashboard")

    if st.button("Logout"):
        st.session_state.logged_in=False
        st.rerun()

    df = pd.read_sql_query("SELECT * FROM visits", conn)

    if df.empty:
        st.warning("No Data Available")
        return

    total_guests = df["guest_count"].sum()
    total_visits = len(df)

    repeat = df.groupby("mobile").size()
    repeat_customers = repeat[repeat > 1].count()
    repeat_percent = (repeat_customers / repeat.count()) * 100 if repeat.count() > 0 else 0

    df["avg_rating"] = (
        df["food_rating"] +
        df["service_rating"] +
        df["behaviour_rating"]
    ) / 3

    avg_rating = df["avg_rating"].mean()

    today = datetime.now().strftime("%Y-%m-%d")
    today_count = df[df["date"] == today]["guest_count"].sum()
    total_previous = df[df["date"] != today]["guest_count"].sum()

    growth = 0
    if total_previous > 0:
        growth = ((today_count - total_previous) / total_previous) * 100

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Guests", total_guests)
    col2.metric("Repeat %", f"{repeat_percent:.1f}%")
    col3.metric("Avg Rating ⭐", f"{avg_rating:.2f}")
    col4.metric("Today Growth %", f"{growth:.1f}%")

    st.divider()

    st.subheader("📊 Category Distribution")
    category_data = df.groupby("category")["guest_count"].sum()
    st.bar_chart(category_data)

    st.divider()

    st.subheader("🏆 VIP Customers (3+ Visits)")
    vip = repeat[repeat >= 3]
    st.write(vip)

    st.subheader("⚠ Low Rating Alert")
    low = df[df["avg_rating"] <= 2.5]
    st.dataframe(low)

    st.subheader("🧠 Smart Insights")

    if repeat_percent < 20:
        st.warning("Customer retention is low. Improve repeat experience.")
    if avg_rating < 3:
        st.error("Average rating is low. Service attention required.")
    if growth > 10:
        st.success("Strong growth trend detected 🚀")

# ---------------- ROUTER ----------------
if not st.session_state.logged_in:
    login()
else:
    if st.session_state.role == "Admin":
        admin_panel()
    else:
        staff_panel()
