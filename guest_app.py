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
guest_count INTEGER,
category TEXT,
staff TEXT,
edit_count INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reviews (
visit_id TEXT,
food_rating INTEGER,
behaviour_rating INTEGER
)
""")

conn.commit()

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

# ---------------- QR ---------------- #

def generate_qr(data):
    qr = qrcode.make(data)
    buf = BytesIO()
    qr.save(buf)
    buf.seek(0)
    return buf

# ---------------- MAIN ---------------- #

def main_app():

    role = st.session_state.role
    user = st.session_state.user

    st.title("Professional Restaurant CRM")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    menu = ["Add Guest","Edit Guest","Review","Export Excel"]

    if role == "admin":
        menu += ["Admin Dashboard"]

    choice = st.sidebar.selectbox("Menu", menu)

    # -------- ADD GUEST -------- #

    if choice == "Add Guest":

        name = st.text_input("Guest Name")
        mobile = st.text_input("Guest Mobile")
        guest_count = st.number_input("Number of Guest", min_value=1)
        category = st.selectbox("Category",
        ["Swiggy","Zomato","EazyDiner","Party","Walk-In"])

        if st.button("Create Entry"):

            visit_id = f"VST{datetime.now().strftime('%Y%m%d%H%M%S')}"

            cursor.execute("""
            INSERT INTO visits
            VALUES (?,?,?,?,?,?,?,0)
            """,(visit_id,
                 datetime.now().strftime("%Y-%m-%d"),
                 name,
                 mobile,
                 guest_count,
                 category,
                 user))
            conn.commit()

            st.success("Guest Entry Created")
            st.write("Visit ID:", visit_id)

            qr = generate_qr(visit_id)
            st.image(qr, caption="Scan For Review")

    # -------- EDIT GUEST -------- #

    if choice == "Edit Guest":

        vid = st.text_input("Enter Visit ID")

        if vid:
            df = pd.read_sql_query("SELECT * FROM visits WHERE visit_id=?", conn, params=(vid,))
            if not df.empty:

                edit_count = df.iloc[0]["edit_count"]

                if role == "staff" and edit_count >= 1:
                    admin_pass = st.text_input("Admin Password Required", type="password")
                    if admin_pass != "1234":
                        st.warning("Admin Approval Needed")
                        return

                name = st.text_input("Guest Name", df.iloc[0]["guest_name"])
                mobile = st.text_input("Mobile", df.iloc[0]["mobile"])
                guest_count = st.number_input("Guest Count", value=int(df.iloc[0]["guest_count"]))
                category = st.selectbox("Category",
                ["Swiggy","Zomato","EazyDiner","Party","Walk-In"],
                index=["Swiggy","Zomato","EazyDiner","Party","Walk-In"].index(df.iloc[0]["category"]))

                if st.button("Update Entry"):
                    cursor.execute("""
                    UPDATE visits
                    SET guest_name=?, mobile=?, guest_count=?, category=?, edit_count=edit_count+1
                    WHERE visit_id=?
                    """,(name,mobile,guest_count,category,vid))
                    conn.commit()
                    st.success("Updated Successfully")

    # -------- REVIEW -------- #

    if choice == "Review":

        vid = st.text_input("Enter Visit ID for Review")

        if vid:
            food = st.slider("Food Rating",1,5)
            behaviour = st.slider("Staff Behaviour",1,5)

            if st.button("Submit Review"):
                cursor.execute("INSERT INTO reviews VALUES (?,?,?)",(vid,food,behaviour))
                conn.commit()
                st.success("Review Submitted")

    # -------- EXPORT -------- #

    if choice == "Export Excel":
        df = pd.read_sql_query("SELECT * FROM visits", conn)
        st.dataframe(df)
        st.download_button("Download Excel",
                           df.to_csv(index=False),
                           "guest_data.csv")

    # -------- ADMIN DASHBOARD -------- #

    if choice == "Admin Dashboard" and role == "admin":

        st.header("Admin Dashboard")

        visits = pd.read_sql_query("SELECT * FROM visits", conn)
        reviews = pd.read_sql_query("SELECT * FROM reviews", conn)

        if not reviews.empty:
            merged = pd.merge(visits, reviews, on="visit_id")

            st.subheader("Staff Behaviour %")
            perf = merged.groupby("staff")["behaviour_rating"].mean()
            perf = (perf/5*100).round(2)
            st.dataframe(perf)

            st.subheader("Low Rating Alert (<3)")
            low = merged[merged["behaviour_rating"] < 3]
            st.dataframe(low)

        st.subheader("VIP Customers (3+ visits)")
        vip = visits["mobile"].value_counts()
        vip = vip[vip >= 3]
        st.dataframe(vip)

# ---------------- FLOW ---------------- #

if st.session_state.logged_in:
    main_app()
else:
    login()
