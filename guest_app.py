import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd

st.set_page_config(page_title="CARNIVLE Enterprise", layout="wide")

DB = "carnivle_pro.db"
conn = sqlite3.connect(DB, check_same_thread=False)
c = conn.cursor()

# ================= DATABASE =================

c.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
password TEXT,
role TEXT,
branch TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS guests(
id TEXT PRIMARY KEY,
name TEXT,
mobile TEXT,
branch TEXT,
created_by TEXT,
category TEXT,
pax INTEGER,
vip INTEGER,
date TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS feedback(
mobile TEXT,
branch TEXT,
overall INTEGER,
food INTEGER,
service INTEGER,
staff INTEGER,
comment TEXT,
date TEXT
)
""")

conn.commit()

# ================= UTIL =================

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def generate_id(name, mobile):
    return hashlib.md5(
        (name + mobile + str(datetime.datetime.now())).encode()
    ).hexdigest()[:8]

# Default Admin
if not c.execute("SELECT * FROM users WHERE username='admin'").fetchone():
    c.execute("INSERT INTO users VALUES (?,?,?,?)",
              ("admin", hash_pass("admin123"), "admin", "Head Office"))
    conn.commit()

# ================= FEEDBACK PAGE =================

query_params = st.query_params

if "feedback" in query_params:

    mobile = query_params["feedback"]
    branch = query_params.get("branch", "Head Office")

    st.title("🍽 CARNIVLE Feedback")

    overall = st.slider("Overall Experience", 1, 5, 4)
    food = st.slider("Food Quality", 1, 5, 4)
    service = st.slider("Service Quality", 1, 5, 4)
    staff = st.slider("Staff Behaviour", 1, 5, 4)
    comment = st.text_area("Comment")

    if st.button("Submit Feedback"):

        today = str(datetime.date.today())

        already = c.execute("""
        SELECT * FROM feedback
        WHERE mobile=? AND date=?
        """, (mobile, today)).fetchone()

        if already:
            st.warning("Feedback already submitted today.")
        else:
            c.execute("""
            INSERT INTO feedback
            VALUES (?,?,?,?,?,?,?,?)
            """, (mobile, branch, overall,
                  food, service, staff,
                  comment, today))
            conn.commit()
            st.success("Thank you ❤️")
            st.balloons()

    st.stop()

# ================= LOGIN =================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.title("🍽 CARNIVLE Enterprise")

    with st.form("login_form_safe"):
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

    if login_button:
        user_data = c.execute(
            "SELECT * FROM users WHERE username=?",
            (username_input,)
        ).fetchone()

        if user_data and user_data[1] == hash_pass(password_input):
            st.session_state.logged_in = True
            st.session_state.current_user = user_data
            st.rerun()
        else:
            st.error("Invalid Login")

    st.stop()

user = st.session_state.current_user

# ================= SIDEBAR =================

st.sidebar.title("CARNIVLE")
st.sidebar.write(f"User: {user[0]}")
st.sidebar.write(f"Role: {user[2]}")
st.sidebar.write(f"Branch: {user[3]}")

if user[2] == "admin":
    menu = st.sidebar.radio("Menu",
                            ["Dashboard", "Guest Entry", "Admin Panel"])
else:
    menu = st.sidebar.radio("Menu",
                            ["Dashboard", "Guest Entry"])

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ================= DASHBOARD =================

if menu == "Dashboard":

    df = pd.read_sql_query(
        "SELECT * FROM guests WHERE branch=?",
        conn, params=(user[3],))

    fb = pd.read_sql_query(
        "SELECT * FROM feedback WHERE branch=?",
        conn, params=(user[3],))

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Guests", len(df))
    col2.metric("Total PAX",
                int(df["pax"].sum()) if not df.empty else 0)
    col3.metric("Avg Rating",
                round(fb["overall"].mean(), 2)
                if not fb.empty else 0)

    if not fb.empty:
        low = fb[fb["overall"] <= 2]
        if not low.empty:
            st.error("⚠️ Low Rating Alert!")

    st.dataframe(df)

# ================= GUEST ENTRY =================

if menu == "Guest Entry":

    st.subheader("Add Guest")

    with st.form("guest_form_safe", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Guest Name")
            mobile = st.text_input("Mobile")

        with col2:
            category = st.selectbox(
                "Category",
                ["Walk-in", "Zomato", "Swiggy",
                 "EazyDiner", "Party", "VIP Guest"]
            )
            pax = st.number_input("PAX", 1)

        submit_guest = st.form_submit_button("Add Guest")

    if submit_guest:

        vip = 1 if category == "VIP Guest" else 0
        gid = generate_id(name, mobile)

        c.execute("""
        INSERT INTO guests
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
                  (gid, name, mobile,
                   user[3], user[0],
                   category, pax, vip,
                   str(datetime.date.today())))
        conn.commit()

        st.success("Guest Added Successfully ✅")

        feedback_link = f"?feedback={mobile}&branch={user[3]}"
        st.info("Send this link to customer:")
        st.code(feedback_link)

# ================= ADMIN PANEL =================

if menu == "Admin Panel" and user[2] == "admin":

    st.subheader("Admin Control")

    tab1, tab2 = st.tabs(["Create Staff", "View Feedback"])

    with tab1:
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password")
        branch_name = st.text_input("Branch Name")

        if st.button("Create Staff"):
            c.execute("INSERT INTO users VALUES (?,?,?,?)",
                      (new_user,
                       hash_pass(new_pass),
                       "staff",
                       branch_name))
            conn.commit()
            st.success("Staff Created")

    with tab2:
        fb_data = pd.read_sql_query(
            "SELECT * FROM feedback", conn)
        st.dataframe(fb_data)
