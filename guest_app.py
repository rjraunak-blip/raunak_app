import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd
import qrcode
import os

st.set_page_config(page_title="Carnivle Pro", layout="wide")

DB="carnivle.db"
conn=sqlite3.connect(DB,check_same_thread=False)
c=conn.cursor()

# ---------------- DATABASE ----------------

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
category TEXT,
vip INTEGER,
branch TEXT,
created_by TEXT,
pax INTEGER,
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

# ---------------- UTIL ----------------

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def generate_id(name,mobile):
    return hashlib.md5((name+mobile+str(datetime.datetime.now())).encode()).hexdigest()[:8]

# default admin
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users VALUES (?,?,?,?)",
              ("admin",hash_pass("admin123"),"admin","Head Office"))
    conn.commit()

# ---------------- FEEDBACK DIRECT PAGE ----------------

query=st.query_params

if "feedback" in query:

    branch=query.get("branch","")

    st.title("⭐ Guest Feedback Form")

    mobile=st.text_input("Mobile Number")

    overall=st.slider("Overall Rating",1,5)
    food=st.slider("Food Rating",1,5)
    service=st.slider("Service Rating",1,5)
    staff=st.slider("Staff Behaviour",1,5)

    comment=st.text_area("Comment")

    if st.button("Submit Feedback"):
        c.execute("INSERT INTO feedback VALUES (?,?,?,?,?,?,?,?)",
                  (mobile,branch,overall,food,
                   service,staff,comment,
                   str(datetime.date.today())))
        conn.commit()
        st.success("Thank You ❤️")
        st.stop()

# ---------------- LOGIN ----------------

if "login" not in st.session_state:
    st.session_state.login=False

if not st.session_state.login:

    st.title("Carnivle Pro Login")

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

st.sidebar.write("User:",user[0])
st.sidebar.write("Role:",user[2])
st.sidebar.write("Branch:",user[3])

menu=st.sidebar.radio("Menu",
["Dashboard","Guest Entry","QR Generator","Feedback Data","Admin Panel"])

if st.sidebar.button("Logout"):
    st.session_state.login=False
    st.rerun()

# ---------------- DASHBOARD ----------------

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
                df["vip"].sum() if not df.empty else 0)
    col4.metric("Avg Rating",
                round(fb["overall"].mean(),2)
                if not fb.empty else 0)

# ---------------- GUEST ENTRY ----------------

if menu=="Guest Entry":

    st.subheader("Add Guest")

    name=st.text_input("Name")
    mobile=st.text_input("Mobile")
    category=st.selectbox("Category",
        ["Walk-in","Zomato","Swiggy","EasyDiner","Party","VIP"])
    pax=st.number_input("PAX",1)

    if st.button("Add Guest"):

        vip=1 if category=="VIP" else 0

        gid=generate_id(name,mobile)

        c.execute("INSERT INTO guests VALUES (?,?,?,?,?,?,?,?,?)",
                  (gid,name,mobile,category,vip,
                   user[3],user[0],pax,
                   str(datetime.date.today())))
        conn.commit()

        st.success("Guest Added")

# ---------------- QR ----------------

if menu=="QR Generator":

    table=st.text_input("Table Number")

    if st.button("Generate QR"):

        base_url="https://rjraunakapp.streamlit.app"  # apna link
        url=f"{base_url}?feedback=table{table}&branch={user[3]}"

        img=qrcode.make(url)
        img.save("qr.png")

        st.image("qr.png")
        st.markdown(f"[Click Here For Feedback]({url})")

# ---------------- FEEDBACK DATA ----------------

if menu=="Feedback Data":

    fb=pd.read_sql_query(
        "SELECT * FROM feedback WHERE branch=?",
        conn,params=(user[3],))

    st.dataframe(fb)

    if not fb.empty:
        st.download_button("Download Excel",
                           fb.to_csv(index=False),
                           "feedback.csv")

# ---------------- ADMIN ----------------

if menu=="Admin Panel" and user[2]=="admin":

    st.subheader("Create Staff")

    new_user=st.text_input("Username")
    new_pass=st.text_input("Password")
    branch_name=st.text_input("Branch Name")

    if st.button("Create Staff"):
        c.execute("INSERT INTO users VALUES (?,?,?,?)",
                  (new_user,
                   hash_pass(new_pass),
                   "staff",
                   branch_name))
        conn.commit()
        st.success("Staff Created")
