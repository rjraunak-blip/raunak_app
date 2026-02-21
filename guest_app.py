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
rating INTEGER DEFAULT 0,
edit_count INTEGER DEFAULT 0
)
""")

conn.commit()

# ---------------- LOGIN USERS ---------------- #

USERS = {
"staff1": {"password":"1111","role":"staff"},
"admin": {"password":"admin123","role":"admin"}
}

# ---------------- SESSION ---------------- #

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user = None

# ---------------- LOGIN PAGE ---------------- #

def login():
    st.title("Restaurant CRM Login")

    user = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if user in USERS and USERS[user]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = USERS[user]["role"]
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Invalid Login")

# ---------------- QR GENERATOR ---------------- #

def generate_qr(link):
    qr = qrcode.make(link)
    buffer = BytesIO()
    qr.save(buffer)
    return buffer.getvalue()

# ---------------- REVIEW PAGE ---------------- #

def review_page(visit_id):
    st.title("Guest Review")

    rating = st.slider("Rate Staff Behaviour",1,5)
    if st.button("Submit Review"):
        cursor.execute("UPDATE visits SET rating=? WHERE visit_id=?",
                       (rating,visit_id))
        conn.commit()
        st.success("Thank you for review!")

# ---------------- STAFF PANEL ---------------- #

def staff_panel():

    st.title("Staff Panel")
    st.write("Logged in as:", st.session_state.user)

    if st.button("Logout"):
        st.session_state.logged_in=False
        st.rerun()

    st.subheader("Create Entry")

    name = st.text_input("Guest Name", key="name")
    mobile = st.text_input("Guest Mobile", key="mobile")
    guest_count = st.number_input("Number of Guest",1, step=1, key="count")
    category = st.selectbox("Category",
    ["Swiggy","Zomato","EazyDiner","Party","Walk-In"],
    key="cat")

    if st.button("Create Entry"):

        visit_id = f"VST{datetime.now().strftime('%Y%m%d%H%M%S')}"

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
        guest_count,
        category,
        st.session_state.user
        ))

        conn.commit()

        st.success("Guest Entry Created")
        st.write("Visit ID:", visit_id)

        review_link = f"?review={visit_id}"
        qr = generate_qr(review_link)
        st.image(qr, caption="Scan for Review")

        st.session_state.name=""
        st.session_state.mobile=""
        st.session_state.count=1

    # STAFF ENTRIES

    df = pd.read_sql_query(
    "SELECT * FROM visits WHERE staff=?",
    conn,
    params=(st.session_state.user,)
    )

    st.subheader("My Entries")
    st.dataframe(df)

    st.metric("Total Guest Count", df["guest_count"].sum())

    st.download_button(
    "Download My Entries",
    df.to_csv(index=False),
    "my_entries.csv"
    )

# ---------------- ADMIN PANEL ---------------- #

def admin_panel():

    st.title("Admin Dashboard")

    if st.button("Logout"):
        st.session_state.logged_in=False
        st.rerun()

    df = pd.read_sql_query("SELECT * FROM visits", conn)

    st.dataframe(df)

    st.metric("Total Guest", df["guest_count"].sum())

    st.subheader("VIP Customers (5+ visits)")

    vip = df.groupby("mobile").size()
    vip = vip[vip>=5]

    st.write(vip)

    st.subheader("Low Rating Alert")

    low = df[df["rating"]<=2]
    st.dataframe(low)

# ---------------- ROUTER ---------------- #

query_params = st.query_params
review_id = query_params.get("review")

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
