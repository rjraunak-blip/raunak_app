import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd

st.set_page_config(page_title="Carnivale Enterprise", layout="wide")

# ================= DATABASE =================
conn = sqlite3.connect("carnivale.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
password TEXT,
role TEXT,
can_view_all INTEGER
)""")

c.execute("""CREATE TABLE IF NOT EXISTS guests(
id TEXT PRIMARY KEY,
name TEXT,
mobile TEXT,
category TEXT,
pax INTEGER,
added_by TEXT,
date TEXT,
feedback INTEGER DEFAULT 0
)""")

c.execute("""CREATE TABLE IF NOT EXISTS feedback(
mobile TEXT,
name TEXT,
rating INTEGER,
comment TEXT,
date TEXT
)""")

conn.commit()

# ================= DEFAULT ADMIN =================
if not c.execute("SELECT * FROM users WHERE username='admin'").fetchone():
    c.execute("INSERT INTO users VALUES (?,?,?,?)",
              ("admin",
               hashlib.md5("admin123".encode()).hexdigest(),
               "admin",1))
    conn.commit()

# ================= SESSION =================
if "login" not in st.session_state:
    st.session_state.login=False
if "user" not in st.session_state:
    st.session_state.user=None

# ================= PUBLIC FEEDBACK =================
params = st.query_params
if "fb" in params:
    mobile = params["fb"]
    st.title("Guest Feedback")

    rating = st.slider("Rating (1-5)",1,5)
    comment = st.text_area("Comment")

    if st.button("Submit"):
        guest = c.execute("SELECT name FROM guests WHERE mobile=?",
                          (mobile,)).fetchone()

        if guest:
            c.execute("INSERT INTO feedback VALUES (?,?,?,?,?)",
                      (mobile,guest[0],rating,comment,
                       str(datetime.date.today())))
            c.execute("UPDATE guests SET feedback=1 WHERE mobile=?",
                      (mobile,))
            conn.commit()
            st.success("Thank You ❤️")
        else:
            st.error("Guest Not Found")

    st.stop()

# ================= LOGIN =================
def login(u,p):
    hashed=hashlib.md5(p.encode()).hexdigest()
    return c.execute("SELECT * FROM users WHERE username=? AND password=?",
                     (u,hashed)).fetchone()

if not st.session_state.login:

    st.title("Login")

    users=[u[0] for u in c.execute("SELECT username FROM users").fetchall()]
    selected=st.selectbox("Select ID",users)
    password=st.text_input("Password",type="password")

    if st.button("Login"):
        user=login(selected,password)
        if user:
            st.session_state.login=True
            st.session_state.user=user
            st.rerun()
        else:
            st.error("Wrong Password")

    st.stop()

user=st.session_state.user

# ================= LOGOUT =================
if st.sidebar.button("Logout"):
    st.session_state.login=False
    st.session_state.user=None
    st.rerun()

menu = st.sidebar.selectbox("Menu",
                            ["Add Guest","My Entries",
                             "Dashboard","Manage Staff"])

# ================= ADD GUEST =================
if menu=="Add Guest":

    st.subheader("Add Guest")

    with st.form("guest_form", clear_on_submit=True):
        name=st.text_input("Name")
        mobile=st.text_input("Mobile")
        category=st.selectbox("Category",
                              ["Walk-in","Zomato",
                               "Swiggy","VIP","Party"])
        pax=st.number_input("PAX",1)
        submit=st.form_submit_button("Add")

        if submit and name and mobile:

            repeat = c.execute(
                "SELECT COUNT(*) FROM guests WHERE mobile=?",
                (mobile,)).fetchone()[0]

            gid=hashlib.md5(
                (name+mobile+
                 str(datetime.datetime.now())
                 ).encode()).hexdigest()[:8]

            c.execute("INSERT INTO guests VALUES (?,?,?,?,?,?,?,?)",
                      (gid,name,mobile,category,pax,
                       user[0],
                       str(datetime.date.today()),0))
            conn.commit()

            st.success("Guest Added")

            if repeat>0:
                st.warning("⚠ Repeat Guest")

            base=st.secrets["BASE_URL"]
            link=f"{base}/?fb={mobile}"

            whatsapp=f"https://wa.me/{mobile}?text=Thank%20you%20for%20visiting!%20Please%20give%20feedback:%20{link}"

            st.markdown(f"[Send WhatsApp Feedback]({whatsapp})")

# ================= MY ENTRIES (STAFF) =================
if menu=="My Entries":

    today=str(datetime.date.today())

    df=pd.read_sql_query(
        "SELECT * FROM guests WHERE added_by=? AND date=?",
        conn,params=(user[0],today))

    st.write("Today Entries:",len(df))
    st.dataframe(df)

    st.download_button("Download Today Excel",
                       df.to_csv(index=False),
                       file_name="today_entries.csv")

# ================= DASHBOARD (ADMIN) =================
if menu=="Dashboard" and user[2]=="admin":

    st.subheader("Admin Dashboard")

    df=pd.read_sql_query("SELECT * FROM guests",conn)
    fb=pd.read_sql_query("SELECT * FROM feedback",conn)

    st.metric("Total Guests",len(df))

    repeat=df.groupby("mobile").size()
    repeat_count=len(repeat[repeat>1])
    st.metric("Repeat Guests",repeat_count)

    st.metric("Feedback Received",len(fb))

    st.subheader("Repeat Guest List")
    st.dataframe(df[df.mobile.isin(repeat[repeat>1].index)])

    st.subheader("Feedback Details")
    st.dataframe(fb)

# ================= MANAGE STAFF =================
if menu=="Manage Staff" and user[2]=="admin":

    st.subheader("Create Staff")

    new_user=st.text_input("Username")
    new_pass=st.text_input("Password")

    if st.button("Create Staff"):
        c.execute("INSERT INTO users VALUES (?,?,?,?)",
                  (new_user,
                   hashlib.md5(new_pass.encode()).hexdigest(),
                   "staff",0))
        conn.commit()
        st.success("Staff Created")

    st.subheader("All Staff")
    staff=pd.read_sql_query(
        "SELECT username FROM users WHERE role='staff'",
        conn)
    st.dataframe(staff)
