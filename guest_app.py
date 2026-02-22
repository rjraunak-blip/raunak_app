import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd

st.set_page_config(page_title="CARNIVLE Enterprise", layout="wide")

# ================= DATABASE =================
DB = "carnivle_pro.db"
conn = sqlite3.connect(DB, check_same_thread=False)
c = conn.cursor()

# Users table
c.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
password TEXT,
role TEXT,
branch TEXT,
can_delete INTEGER DEFAULT 0
)
""")

# Guests table
c.execute("""
CREATE TABLE IF NOT EXISTS guests(
id TEXT PRIMARY KEY,
name TEXT,
mobile TEXT,
category TEXT,
branch TEXT,
created_by TEXT,
pax INTEGER,
visit_date TEXT,
feedback_given INTEGER DEFAULT 0,
edit_count INTEGER DEFAULT 0
)
""")

# Feedback table
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
    return hashlib.md5(str(datetime.datetime.now()).encode()).hexdigest()[:8]

# Default Admin
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users VALUES (?,?,?,?,?)",
              ("admin", hash_pass("admin123"),
               "admin", "Head Office", 1))
    conn.commit()

# ================= LOGIN =================
if "user" not in st.session_state:

    st.title("Login Panel")

    users_df = pd.read_sql_query(
        "SELECT username FROM users", conn)

    user_list = users_df["username"].tolist()

    selected_user = st.selectbox("Select ID", user_list)
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        c.execute("SELECT * FROM users WHERE username=?",
                  (selected_user,))
        user = c.fetchone()

        if user and user[1] == hash_pass(password):
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Wrong Password")

    st.stop()

user = st.session_state.user

st.sidebar.write("Logged in as:", user[0])
st.sidebar.write("Role:", user[2])

if st.sidebar.button("Logout"):
    del st.session_state["user"]
    st.rerun()

# ================= MENU =================
menu = st.sidebar.radio("Menu",
["Dashboard","Add Guest","My Entries","Feedback","Admin Panel"])

# ================= DASHBOARD =================
if menu == "Dashboard":

    df = pd.read_sql_query("SELECT * FROM guests", conn)

    st.metric("Total Guests", len(df))
    st.metric("Repeat Customers",
              df["mobile"].duplicated().sum())

# ================= ADD GUEST =================
if menu == "Add Guest":

    st.subheader("Add Guest")

    name = st.text_input("Name")
    mobile = st.text_input("Mobile")
    category = st.selectbox("Category",
                            ["Walk-in","Zomato","Swiggy",
                             "EazyDiner","Party","VIP"])
    pax = st.number_input("PAX", 1)
    visit_date = st.date_input("Visit Date")

    if st.button("Save Guest"):
        gid = generate_id()

        c.execute("""
        INSERT INTO guests VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (gid,name,mobile,category,
         user[3],user[0],pax,
         str(visit_date),0,0))

        conn.commit()
        st.success("Guest Saved")

# ================= MY ENTRIES =================
if menu == "My Entries":

    df = pd.read_sql_query(
        "SELECT * FROM guests WHERE created_by=?",
        conn, params=(user[0],))

    st.dataframe(df)

    st.download_button(
        "Download Excel",
        df.to_csv(index=False),
        "my_entries.csv"
    )

# ================= FEEDBACK =================
if menu == "Feedback":

    st.subheader("Customer Feedback")

    mobile = st.text_input("Mobile")
    name = st.text_input("Name")
    rating = st.slider("Rating",1,5)
    comment = st.text_area("Comment")

    if st.button("Submit Feedback"):
        c.execute("INSERT INTO feedback VALUES (?,?,?,?,?)",
                  (mobile,name,rating,
                   comment,str(datetime.date.today())))

        c.execute("UPDATE guests SET feedback_given=1 WHERE mobile=?",
                  (mobile,))
        conn.commit()

        st.success("Feedback Submitted")

# ================= ADMIN PANEL =================
if menu == "Admin Panel" and user[2] == "admin":

    tab1, tab2, tab3 = st.tabs(
        ["Create Staff","All Guests","All Feedback"])

    # Create Staff
    with tab1:
        new_user = st.text_input("Staff ID")
        new_pass = st.text_input("Password")
        branch = st.text_input("Branch")

        if st.button("Create Staff"):
            c.execute("INSERT INTO users VALUES (?,?,?,?,?)",
                      (new_user,
                       hash_pass(new_pass),
                       "staff",
                       branch,
                       0))
            conn.commit()
            st.success("Staff Created")

    # All Guests
    with tab2:
        df = pd.read_sql_query("SELECT * FROM guests", conn)
        st.dataframe(df)

        delete_id = st.text_input("Guest ID to Delete")

        if st.button("Delete Guest"):
            c.execute("DELETE FROM guests WHERE id=?",
                      (delete_id,))
            conn.commit()
            st.success("Deleted")

    # All Feedback
    with tab3:
        fb = pd.read_sql_query("SELECT * FROM feedback", conn)
        st.dataframe(fb)
