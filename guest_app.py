import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd
import urllib.parse

st.set_page_config(page_title="CARNIVLE Enterprise", layout="wide")

DB = "carnivle_enterprise.db"
conn = sqlite3.connect(DB, check_same_thread=False)
c = conn.cursor()

# ================= DATABASE =================

c.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
password TEXT,
role TEXT,
can_add INTEGER,
can_edit INTEGER,
can_export INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS guests(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
mobile TEXT,
category TEXT,
staff TEXT,
pax INTEGER,
visit_date TEXT,
edit_count INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS feedback(
id INTEGER PRIMARY KEY AUTOINCREMENT,
mobile TEXT,
name TEXT,
rating INTEGER,
comment TEXT,
date TEXT
)
""")

conn.commit()

# ================= DEFAULT ADMIN =================

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users VALUES (?,?,?,?,?,?)",
              ("admin", hash_pass("admin123"),
               "admin", 1, 1, 1))
    conn.commit()

# ================= PUBLIC FEEDBACK =================

params = st.query_params
if "feedback" in params:

    mobile = params["feedback"]

    guest = pd.read_sql_query(
        "SELECT * FROM guests WHERE mobile=? ORDER BY id DESC LIMIT 1",
        conn, params=(mobile,)
    )

    st.title("Customer Feedback")

    if guest.empty:
        st.error("Guest not found")
        st.stop()

    name = guest.iloc[0]["name"]

    st.write("Guest:", name)
    st.write("Mobile:", mobile)

    rating = st.slider("Rating", 1, 5)
    comment = st.text_area("Comment")

    if st.button("Submit"):
        c.execute("INSERT INTO feedback VALUES (?,?,?,?,?)",
                  (None, mobile, name, rating,
                   comment, str(datetime.date.today())))
        conn.commit()
        st.success("Thank you ❤️")
    st.stop()

# ================= LOGIN =================

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:

    st.title("CARNIVLE Enterprise Login")

    users = pd.read_sql_query("SELECT username FROM users", conn)
    user_list = users["username"].tolist()

    username = st.selectbox("Select ID", user_list)
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        data = c.fetchone()
        if data and data[1] == hash_pass(password):
            st.session_state.login = True
            st.session_state.user = data
            st.rerun()
        else:
            st.error("Wrong Password")

    st.stop()

user = st.session_state.user

# ================= SIDEBAR =================

st.sidebar.write("Logged in as:", user[0])
menu = st.sidebar.radio("Menu",
                        ["Dashboard",
                         "Guest Entry",
                         "My Guests",
                         "Admin Panel"])

if st.sidebar.button("Logout"):
    st.session_state.login = False
    st.rerun()

# ================= DASHBOARD =================

if menu == "Dashboard":

    df = pd.read_sql_query("SELECT * FROM guests", conn)
    fb = pd.read_sql_query("SELECT * FROM feedback", conn)

    st.metric("Total Guests", len(df))
    st.metric("Total Feedback", len(fb))

    repeat = df["mobile"].value_counts()
    repeat_count = len(repeat[repeat > 1])
    st.metric("Repeat Customers", repeat_count)

# ================= GUEST ENTRY =================

if menu == "Guest Entry" and user[3] == 1:

    st.subheader("Add Guest")

    name = st.text_input("Name")
    mobile = st.text_input("Mobile")
    category = st.selectbox("Category",
                             ["Walk-in","Zomato",
                              "Swiggy","EazyDinner",
                              "Party","VIP"])
    pax = st.number_input("PAX", 1)
    visit_date = st.date_input("Visit Date")

    if st.button("Save Guest"):

        c.execute("""INSERT INTO guests
                     (name,mobile,category,staff,pax,visit_date)
                     VALUES (?,?,?,?,?,?)""",
                  (name,mobile,category,user[0],
                   pax,str(visit_date)))
        conn.commit()

        feedback_link = f"https://YOUR-APP-LINK.streamlit.app/?feedback={mobile}"

        message = urllib.parse.quote(
            f"Thank you for visiting.\nPlease give feedback:\n{feedback_link}"
        )

        whatsapp_url = f"https://wa.me/91{mobile}?text={message}"

        st.success("Guest Saved")
        st.markdown(f"[Send Feedback on WhatsApp]({whatsapp_url})")

# ================= MY GUESTS =================

if menu == "My Guests":

    df = pd.read_sql_query(
        "SELECT * FROM guests WHERE staff=?",
        conn, params=(user[0],)
    )

    st.dataframe(df)

    if user[5] == 1:
        st.download_button("Download Excel",
                           df.to_csv(index=False),
                           "my_guests.csv")

# ================= ADMIN PANEL =================

if menu == "Admin Panel" and user[2] == "admin":

    tab1, tab2, tab3 = st.tabs(
        ["Create Staff", "All Guests", "Feedback"]
    )

    with tab1:
        new_user = st.text_input("New Username")
        new_pass = st.text_input("Password")
        can_add = st.checkbox("Can Add Guest")
        can_edit = st.checkbox("Can Edit Once")
        can_export = st.checkbox("Can Export")

        if st.button("Create Staff"):
            c.execute("INSERT INTO users VALUES (?,?,?,?,?,?)",
                      (new_user,
                       hash_pass(new_pass),
                       "staff",
                       int(can_add),
                       int(can_edit),
                       int(can_export)))
            conn.commit()
            st.success("Staff Created")

    with tab2:
        all_df = pd.read_sql_query("SELECT * FROM guests", conn)
        st.dataframe(all_df)

        delete_id = st.number_input("Delete Guest ID", 0)

        if st.button("Delete Guest"):
            c.execute("DELETE FROM guests WHERE id=?",
                      (delete_id,))
            conn.commit()
            st.success("Deleted")

    with tab3:
        fb_df = pd.read_sql_query("SELECT * FROM feedback", conn)
        st.dataframe(fb_df)
