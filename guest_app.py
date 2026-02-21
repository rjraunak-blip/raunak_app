import streamlit as st
import sqlite3
import pandas as pd
import qrcode
from io import BytesIO
from datetime import datetime

# ---------------- DATABASE ---------------- #

conn = sqlite3.connect("crm.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS visits(
id INTEGER PRIMARY KEY AUTOINCREMENT,
visit_id TEXT,
date TEXT,
guest_name TEXT,
mobile TEXT,
guest_count INTEGER,
category TEXT,
staff TEXT,
food_rating INTEGER DEFAULT 0,
service_rating INTEGER DEFAULT 0,
behaviour_rating INTEGER DEFAULT 0,
edit_count INTEGER DEFAULT 0
)
""")

conn.commit()

# ---------------- USERS ---------------- #

USERS = {
"staff1": {"password":"1111","role":"staff"},
"admin": {"password":"admin123","role":"admin"}
}

# ---------------- SESSION ---------------- #

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user = None

# ---------------- LOGIN ---------------- #

def login():
    st.title("Restaurant CRM Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USERS and USERS[u]["password"] == p:
            st.session_state.logged_in=True
            st.session_state.role=USERS[u]["role"]
            st.session_state.user=u
            st.rerun()
        else:
            st.error("Wrong Login")

# ---------------- QR ---------------- #

def make_qr(link):
    qr = qrcode.make(link)
    buf = BytesIO()
    qr.save(buf)
    return buf.getvalue()

# ---------------- REVIEW PAGE ---------------- #

def review_page(visit_id):
    st.title("Guest Feedback Form")

    food = st.slider("Food Quality ⭐",1,5)
    service = st.slider("Service ⭐",1,5)
    behaviour = st.slider("Staff Behaviour ⭐",1,5)

    if st.button("Submit Feedback"):
        cursor.execute("""
        UPDATE visits SET
        food_rating=?,
        service_rating=?,
        behaviour_rating=?
        WHERE visit_id=?
        """,(food,service,behaviour,visit_id))
        conn.commit()
        st.success("Thank You For Feedback ❤️")

# ---------------- STAFF PANEL ---------------- #

def staff_panel():

    st.title("Staff Panel")

    if st.button("Logout"):
        st.session_state.logged_in=False
        st.rerun()

    st.subheader("Create Guest Entry")

    name = st.text_input("Guest Name")
    mobile = st.text_input("Mobile")
    count = st.number_input("Guest Count",1)
    cat = st.selectbox("Category",
    ["Swiggy","Zomato","EazyDiner","Party","Walk-In"])

    if st.button("Save Entry"):

        visit_id = "V"+datetime.now().strftime("%Y%m%d%H%M%S")

        cursor.execute("""
        INSERT INTO visits
        (visit_id,date,guest_name,mobile,guest_count,category,staff)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
        visit_id,
        datetime.now().strftime("%Y-%m-%d"),
        name,
        mobile,
        count,
        cat,
        st.session_state.user
        ))

        conn.commit()

        st.success("Entry Saved")

        review_link = f"?review={visit_id}"
        qr = make_qr(review_link)
        st.image(qr, caption="Scan For Feedback")

    df = pd.read_sql_query(
    "SELECT * FROM visits WHERE staff=?",
    conn,
    params=(st.session_state.user,)
    )

    st.subheader("My Entries")
    st.dataframe(df)

    if not df.empty:
        st.metric("Total Guests", df["guest_count"].sum())

    st.download_button(
    "Download My Data",
    df.to_csv(index=False),
    "staff_data.csv"
    )

# ---------------- ADMIN PANEL ---------------- #

def admin_panel():

    st.title("Admin Dashboard")

    if st.button("Logout"):
        st.session_state.logged_in=False
        st.rerun()

    df = pd.read_sql_query("SELECT * FROM visits", conn)

    st.dataframe(df)

    if not df.empty:

        st.metric("Total Guests", df["guest_count"].sum())

        # VIP Detection
        st.subheader("VIP Customers (5+ Visits)")
        vip = df.groupby("mobile").size()
        vip = vip[vip>=5]
        st.write(vip)

        # Low Rating Alert
        st.subheader("Low Rating Alert")
        low = df[
        (df["food_rating"]<=2) |
        (df["service_rating"]<=2) |
        (df["behaviour_rating"]<=2)
        ]
        st.dataframe(low)

        # Staff Performance %
        st.subheader("Staff Performance %")

        df["avg_rating"] = (
        df["food_rating"]+
        df["service_rating"]+
        df["behaviour_rating"]
        )/3

        performance = df.groupby("staff")["avg_rating"].mean()

        performance_percent = (performance/5)*100

        st.write(performance_percent)

# ---------------- ROUTER ---------------- #

params = st.query_params
review_id = params.get("review")

if review_id:
    review_page(review_id)
else:
    if not st.session_state.logged_in:
        login()
    else:
        if st.session_state.role=="staff":
            staff_panel()
        else:
            admin_panel()

