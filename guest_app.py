import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd

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
branch TEXT,
created_by TEXT,
category TEXT,
pax INTEGER,
vip INTEGER,
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

    with st.form("login_form"):
        u=st.text_input("Username")
        p=st.text_input("Password",type="password")
        login_btn=st.form_submit_button("Login")

    if login_btn:
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
st.sidebar.write(f"Branch: {user[3]}")

menu=st.sidebar.radio("Menu",["Dashboard","Guest Entry"])

if st.sidebar.button("Logout"):
    st.session_state.login=False
    st.rerun()

# ================= DASHBOARD =================

if menu=="Dashboard":

    df=pd.read_sql_query(
        "SELECT * FROM guests WHERE branch=?",
        conn,params=(user[3],))

    col1,col2,col3=st.columns(3)

    col1.metric("Total Guests",len(df))
    col2.metric("Total PAX",
                df["pax"].sum() if not df.empty else 0)
    col3.metric("VIP Guests",
                df["vip"].sum() if not df.empty else 0)

    st.dataframe(df)

# ================= GUEST ENTRY =================

if menu=="Guest Entry" and user[4]==1:

    st.subheader("Add Guest")

    with st.form("guest_form", clear_on_submit=True):

        col1,col2=st.columns(2)

        with col1:
            name=st.text_input("Guest Name")
            mobile=st.text_input("Mobile")

        with col2:
            category=st.selectbox(
                "Category",
                ["Walk-in","Zomato","Swiggy",
                 "EazyDiner","Party","VIP Guest"]
            )
            pax=st.number_input("PAX",1)

        submit=st.form_submit_button("Add Guest")

    if submit:

        vip=1 if category=="VIP Guest" else 0
        gid=generate_id(name,mobile)

        c.execute("""
        INSERT INTO guests
        (id,name,mobile,branch,created_by,
         category,pax,vip,date)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (gid,name,mobile,user[3],user[0],
         category,pax,vip,
         str(datetime.date.today())))

        conn.commit()

        st.success("Guest Added Successfully ✅")
