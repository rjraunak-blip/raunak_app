import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd
import qrcode
import os

st.set_page_config(page_title="CARNIVLE Enterprise Pro", layout="wide")

DB="carnivle_pro.db"
conn=sqlite3.connect(DB,check_same_thread=False)
c=conn.cursor()

# ================= DATABASE =================
c.execute("""CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
password TEXT,
role TEXT,
branch TEXT,
can_add_guest INTEGER,
can_view_all INTEGER,
can_download INTEGER
)""")

c.execute("""CREATE TABLE IF NOT EXISTS guests(
id TEXT PRIMARY KEY,
name TEXT,
mobile TEXT,
category TEXT,
branch TEXT,
created_by TEXT,
pax INTEGER,
date TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS feedback(
mobile TEXT,
branch TEXT,
overall INTEGER,
comment TEXT,
date TEXT
)""")

conn.commit()

# ================= UTIL =================
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def generate_id(name,mobile):
    return hashlib.md5((name+mobile+str(datetime.datetime.now())).encode()).hexdigest()[:8]

# Default Admin
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)",
              ("admin",hash_pass("admin123"),
               "admin","Head Office",1,1,1))
    conn.commit()

# ================= LOGIN =================
if "login" not in st.session_state:
    st.session_state.login=False

if not st.session_state.login:
    st.title("🍽 CARNIVLE Enterprise Pro")
    u=st.text_input("Username")
    p=st.text_input("Password",type="password")

    if st.button("Login"):
        c.execute("SELECT * FROM users WHERE username=?",(u,))
        data=c.fetchone()
        if data and data[1]==hash_pass(p):
            st.session_state.login=True
            st.session_state.user=data
            st.rerun()
        else:
            st.error("Invalid Login")
    st.stop()

user=st.session_state.user

st.sidebar.write(f"User: {user[0]}")
st.sidebar.write(f"Role: {user[2]}")
st.sidebar.write(f"Branch: {user[3]}")

menu=st.sidebar.radio("Menu",
["Dashboard","Guest Entry","Leaderboard",
 "QR Generator","Reports","Admin Panel"])

if st.sidebar.button("Logout"):
    st.session_state.login=False
    st.rerun()

# ================= DASHBOARD =================
if menu=="Dashboard":

    df=pd.read_sql_query(
        "SELECT * FROM guests WHERE branch=?",
        conn,params=(user[3],))

    fb=pd.read_sql_query(
        "SELECT * FROM feedback WHERE branch=?",
        conn,params=(user[3],))

    col1,col2,col3,col4=st.columns(4)

    col1.metric("Total Guests",len(df))
    col2.metric("Total PAX",
                df["pax"].sum() if not df.empty else 0)
    col3.metric("VIP Guests",
                len(df[df["category"]=="VIP Guest"]) if not df.empty else 0)
    col4.metric("Avg Rating",
                round(fb["overall"].mean(),2)
                if not fb.empty else 0)

    # Low rating alert
    if not fb.empty:
        low=fb[fb["overall"]<=2]
        if not low.empty:
            st.error("⚠️ Low Rating Alert Detected!")

# ================= GUEST ENTRY =================
if menu=="Guest Entry" and user[4]==1:

    st.subheader("Add Guest")

    with st.form("guest_form",clear_on_submit=True):

        col1,col2=st.columns(2)

        with col1:
            name=st.text_input("Guest Name")
            mobile=st.text_input("Mobile")

        with col2:
            pax=st.number_input("PAX",1)
            category=st.selectbox("Category",
                ["Walk-In","Swiggy","Zomato",
                 "EazyDiner","Party","VIP Guest"])

        submit=st.form_submit_button("Add Guest")

        if submit:
            gid=generate_id(name,mobile)
            c.execute("INSERT INTO guests VALUES (?,?,?,?,?,?,?,?)",
                      (gid,name,mobile,category,
                       user[3],user[0],pax,
                       str(datetime.date.today())))
            conn.commit()
            st.success("Guest Added Successfully")

# ================= LEADERBOARD =================
if menu=="Leaderboard":

    df=pd.read_sql_query(
        "SELECT created_by, COUNT(*) as total FROM guests GROUP BY created_by",
        conn)

    st.subheader("🏆 Staff Leaderboard")
    st.dataframe(df.sort_values("total",ascending=False))

# ================= QR =================
if menu=="QR Generator":

    table=st.text_input("Table Number")

    if st.button("Generate QR"):

        url=f"https://rjraunakapp.streamlit.app/?feedback=table{table}&branch={user[3]}"

        img=qrcode.make(url)
        img.save("qr.png")
        st.image("qr.png")

# ================= REPORT =================
if menu=="Reports" and user[6]==1:

    df=pd.read_sql_query(
        "SELECT * FROM guests WHERE branch=?",
        conn,params=(user[3],))

    st.dataframe(df)

    st.download_button(
        "Download Excel",
        df.to_csv(index=False),
        "guest_data.csv"
    )

# ================= ADMIN =================
if menu=="Admin Panel" and user[2]=="admin":

    st.subheader("Create Staff")

    new_user=st.text_input("Username")
    new_pass=st.text_input("Password")
    branch=st.text_input("Branch")

    if st.button("Create Staff"):
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)",
                  (new_user,hash_pass(new_pass),
                   "staff",branch,1,0,0))
        conn.commit()
        st.success("Staff Created")

    st.subheader("All Users")
    all_users=pd.read_sql_query("SELECT * FROM users",conn)
    st.dataframe(all_users)
