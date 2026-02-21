import streamlit as st
import sqlite3
import pandas as pd
import qrcode
from io import BytesIO
from datetime import datetime
import os

# ---------------- DATABASE SETUP ---------------- #

conn = sqlite3.connect("crm.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS visits (
    visit_id TEXT PRIMARY KEY,
    date TEXT,
    guest_name TEXT,
    mobile TEXT,
    staff TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reviews (
    visit_id TEXT,
    food_rating INTEGER,
    behaviour_rating INTEGER,
    comment TEXT
)
""")

conn.commit()

# Default users
cursor.execute("INSERT OR IGNORE INTO users VALUES ('admin','1234','admin')")
cursor.execute("INSERT OR IGNORE INTO users VALUES ('staff1','1111','staff')")
conn.commit()

# ---------------- LOGIN ---------------- #

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = ""
    st.session_state.user = ""

def login():
    st.title("Restaurant CRM Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (u,p))
        result = cursor.fetchone()

        if result:
            st.session_state.logged_in = True
            st.session_state.role = result[0]
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Invalid Login")

# ---------------- QR GENERATOR ---------------- #

def generate_qr(data):
    qr = qrcode.make(data)
    buf = BytesIO()
    qr.save(buf)
    buf.seek(0)
    return buf

# ---------------- MAIN APP ---------------- #

def main_app():

    st.title("Professional Restaurant CRM")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    role = st.session_state.role
    user = st.session_state.user

    menu = ["Add Visit","Review","Dashboard","Customer Search"]
    choice = st.sidebar.selectbox("Menu", menu)

    # -------- ADD VISIT -------- #

    if choice == "Add Visit":
        st.header("Add Guest Visit")

        name = st.text_input("Guest Name")
        mobile = st.text_input("Mobile")

        if st.button("Create Visit"):

            visit_id = f"VST{datetime.now().strftime('%Y%m%d%H%M%S')}"

            cursor.execute("INSERT INTO visits VALUES (?,?,?,?,?)",
                           (visit_id, datetime.now().strftime("%Y-%m-%d"),
                            name, mobile, user))
            conn.commit()

            review_link = f"?review={visit_id}"

            st.success("Visit Created")
            st.write("Visit ID:", visit_id)

            qr_img = generate_qr(review_link)
            st.image(qr_img, caption="Scan for Review")

    # -------- REVIEW PAGE -------- #

    if choice == "Review":

        review_id = st.text_input("Enter Visit ID")

        if review_id:
            st.header("Submit Review")

            food = st.slider("Food Rating",1,5)
            behaviour = st.slider("Staff Behaviour",1,5)
            comment = st.text_area("Comment")

            if st.button("Submit Review"):
                cursor.execute("INSERT INTO reviews VALUES (?,?,?,?)",
                               (review_id, food, behaviour, comment))
                conn.commit()
                st.success("Review Submitted")

    # -------- DASHBOARD (ADMIN ONLY) -------- #

    if choice == "Dashboard" and role == "admin":

        st.header("Admin Dashboard")

        df_visits = pd.read_sql_query("SELECT * FROM visits", conn)
        df_reviews = pd.read_sql_query("SELECT * FROM reviews", conn)

        if not df_reviews.empty:
            merged = pd.merge(df_visits, df_reviews, on="visit_id")

            st.subheader("Staff Performance")

            staff_perf = merged.groupby("staff")["behaviour_rating"].mean()
            staff_perf = (staff_perf / 5 * 100).round(2)

            st.dataframe(staff_perf)

            st.subheader("Low Ratings (<3)")
            low = merged[merged["behaviour_rating"] < 3]
            st.dataframe(low)

        else:
            st.info("No Reviews Yet")

    # -------- CUSTOMER SEARCH -------- #

    if choice == "Customer Search":
        st.header("Customer History")

        mobile_search = st.text_input("Enter Mobile Number")

        if mobile_search:
            df = pd.read_sql_query(
                "SELECT * FROM visits WHERE mobile=?",
                conn,
                params=(mobile_search,)
            )

            st.dataframe(df)

            if len(df) >= 3:
                st.success("VIP Customer")

# ---------------- FLOW ---------------- #

if st.session_state.logged_in:
    main_app()
else:
    login()
