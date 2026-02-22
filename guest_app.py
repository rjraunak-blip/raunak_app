import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd
import os

st.set_page_config(page_title="Enterprise CRM", layout="wide")

DB = "carnivle_pro.db"
conn = sqlite3.connect(DB, check_same_thread=False)
c = conn.cursor()

# ================= DATABASE =================

c.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
password TEXT,
role TEXT,
branch TEXT,
can_add_guest INTEGER,
can_edit_guest INTEGER,
can_delete_guest INTEGER,
can_download INTEGER,
can_view_all INTEGER,
can_view_feedback INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS guests(
id TEXT PRIMARY KEY,
name TEXT,
mobile TEXT,
category TEXT,
branch TEXT,
created_by TEXT,
pax INTEGER,
date TEXT,
edited INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS feedback(
mobile TEXT,
name TEXT,
rating INTEGER,
comment TEXT,
date TEXT
)
""")

conn.commit()

# ================= UTIL =================

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def generate_id():
    return hashlib.md5(str(datetime.datetime.now()).encode()).hexdigest()[:10]

# Default Admin
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("""
    INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?)
    """,(
        "admin",
        hash_pass("admin123"),
        "admin",
        "HeadOffice",
        1,1,1,1,1,1
    ))
    conn.commit()

# ================= SESSION =================

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("Enterprise CRM Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        c.execute("SELECT * FROM users WHERE username=?", (u,))
        user = c.fetchone()
        if user and user[1] == hash_pass(p):
            st.session_state.login = True
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Invalid Login")
    st.stop()

user = st.session_state.user

# Logout
if st.sidebar.button("Logout"):
    st.session_state.login = False
    st.rerun()

st.sidebar.write("User:", user[0])
st.sidebar.write("Role:", user[2])

menu = st.sidebar.radio("Menu", [
    "Dashboard",
    "Guest Entry",
    "Feedback",
    "Admin Panel"
])

# ================= DASHBOARD =================

if menu == "Dashboard":

    if user[8] == 1:
        df = pd.read_sql_query("SELECT * FROM guests", conn)
    else:
        df = pd.read_sql_query(
            "SELECT * FROM guests WHERE created_by=?",
            conn, params=(user[0],)
        )

    st.subheader("Guest Data")

    date_filter = st.date_input("Filter by Date", None)

    if date_filter:
        df = df[df["date"] == str(date_filter)]

    st.dataframe(df)

    st.metric("Total Guests", len(df))
    st.metric("Total PAX", df["pax"].sum() if not df.empty else 0)

    # Repeat detection
    repeat = df["mobile"].value_counts()
    repeat_customers = repeat[repeat > 1].count()
    st.metric("Repeat Customers", repeat_customers)

    if user[7] == 1:
        st.download_button(
            "Download Excel",
            df.to_csv(index=False),
            "guest_data.csv"
        )

# ================= GUEST ENTRY =================

if menu == "Guest Entry" and user[4] == 1:

    st.subheader("Add Guest")

    name = st.text_input("Guest Name")
    mobile = st.text_input("Mobile Number")
    category = st.selectbox("Category",
        ["Walk-In","Swiggy","Zomato","EazyDiner","Party","VIP"])
    pax = st.number_input("PAX", 1)
    entry_date = st.date_input("Entry Date", datetime.date.today())

    if st.button("Add Guest"):
        gid = generate_id()
        c.execute("""
        INSERT INTO guests VALUES (?,?,?,?,?,?,?,?,0)
        """,(
            gid,name,mobile,category,
            user[3],user[0],pax,
            str(entry_date)
        ))
        conn.commit()
        st.success("Guest Added")

# ================= FEEDBACK =================

if menu == "Feedback":

    st.subheader("Customer Feedback")

    mobile = st.text_input("Mobile Number")
    name = st.text_input("Name")
    rating = st.slider("Rating",1,5)
    comment = st.text_area("Comment")

    if st.button("Submit Feedback"):
        c.execute("""
        INSERT INTO feedback VALUES (?,?,?,?,?)
        """,(
            mobile,name,rating,comment,
            str(datetime.date.today())
        ))
        conn.commit()
        st.success("Feedback Submitted")

    if user[9] == 1:
        fb = pd.read_sql_query("SELECT * FROM feedback", conn)
        st.dataframe(fb)

# ================= ADMIN PANEL =================

if menu == "Admin Panel" and user[2] == "admin":

    tab1, tab2 = st.tabs(["Create Staff","Access Control"])

    with tab1:
        st.subheader("Create Staff")

        new_user = st.text_input("Username")
        new_pass = st.text_input("Password")
        branch = st.text_input("Branch")

        if st.button("Create"):
            c.execute("""
            INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?)
            """,(
                new_user,
                hash_pass(new_pass),
                "staff",
                branch,
                1,1,0,1,0,0
            ))
            conn.commit()
            st.success("Staff Created")

    with tab2:
        st.subheader("Access Control")

        users_df = pd.read_sql_query("SELECT * FROM users", conn)
        st.dataframe(users_df)

        selected = st.selectbox(
            "Select User",
            users_df["username"]
        )

        can_add = st.checkbox("Can Add")
        can_edit = st.checkbox("Can Edit")
        can_delete = st.checkbox("Can Delete")
        can_download = st.checkbox("Can Download")
        can_view_all = st.checkbox("Can View All")
        can_view_feedback = st.checkbox("Can View Feedback")

        if st.button("Update Access"):
            c.execute("""
            UPDATE users SET
            can_add_guest=?,
            can_edit_guest=?,
            can_delete_guest=?,
            can_download=?,
            can_view_all=?,
            can_view_feedback=?
            WHERE username=?
            """,(
                int(can_add),
                int(can_edit),
                int(can_delete),
                int(can_download),
                int(can_view_all),
                int(can_view_feedback),
                selected
            ))
            conn.commit()
            st.success("Access Updated")
