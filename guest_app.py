import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Carnivle CRM PRO", layout="wide")

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
repeat_count INTEGER,
branch TEXT,
created_by TEXT,
pax INTEGER,
visit_date TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS feedback(
mobile TEXT,
guest_name TEXT,
branch TEXT,
overall INTEGER,
food INTEGER,
service INTEGER,
staff INTEGER,
comment TEXT,
feedback_date TEXT
)
""")

conn.commit()

# ---------------- UTIL ----------------

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def generate_id(name,mobile):
    return hashlib.md5((name+mobile+str(datetime.datetime.now())).encode()).hexdigest()[:8]

# Default Admin
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users VALUES (?,?,?,?)",
              ("admin",hash_pass("admin123"),"admin","Head Office"))
    conn.commit()

# ---------------- FEEDBACK PAGE ----------------

query=st.query_params

if "feedback" in query:
    branch=query.get("branch","")

    st.title("⭐ Guest Feedback")

    mobile=st.text_input("Mobile Number")

    # guest name auto fetch
    guest=pd.read_sql_query(
        "SELECT name FROM guests WHERE mobile=? ORDER BY visit_date DESC",
        conn,params=(mobile,))

    if not guest.empty:
        guest_name=guest.iloc[0]["name"]
        st.write("Guest:",guest_name)
    else:
        guest_name=st.text_input("Your Name")

    overall=st.slider("Overall",1,5)
    food=st.slider("Food",1,5)
    service=st.slider("Service",1,5)
    staff=st.slider("Staff Behaviour",1,5)
    comment=st.text_area("Comment")

    if st.button("Submit"):
        c.execute("INSERT INTO feedback VALUES (?,?,?,?,?,?,?,?,?)",
                  (mobile,guest_name,branch,
                   overall,food,service,staff,
                   comment,str(datetime.date.today())))
        conn.commit()
        st.success("Thank You ❤️")
        st.stop()

# ---------------- LOGIN ----------------

if "login" not in st.session_state:
    st.session_state.login=False

if not st.session_state.login:
    st.title("Carnivle CRM Login")
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

menu=st.sidebar.radio("Menu",
["Dashboard","Guest Entry","My Guests","Feedback Data","Admin Panel"])

# ---------------- DASHBOARD ----------------

if menu=="Dashboard":

    df=pd.read_sql_query("SELECT * FROM guests",conn)
    fb=pd.read_sql_query("SELECT * FROM feedback",conn)

    col1,col2,col3=st.columns(3)

    col1.metric("Total Guests",len(df))
    col2.metric("Repeat Guests",
                df[df["repeat_count"]>1].shape[0] if not df.empty else 0)
    col3.metric("Avg Rating",
                round(fb["overall"].mean(),2) if not fb.empty else 0)

# ---------------- GUEST ENTRY ----------------

if menu=="Guest Entry":

    name=st.text_input("Guest Name")
    mobile=st.text_input("Mobile")
    category=st.selectbox("Category",
        ["Walk-in","Zomato","Swiggy","EasyDiner","Party","VIP"])
    pax=st.number_input("PAX",1)

    visit_date=st.date_input("Visit Date",datetime.date.today())

    if st.button("Add Guest"):

        old=pd.read_sql_query(
            "SELECT * FROM guests WHERE mobile=?",
            conn,params=(mobile,))

        repeat_count=len(old)+1

        gid=generate_id(name,mobile)

        c.execute("INSERT INTO guests VALUES (?,?,?,?,?,?,?,?,?)",
                  (gid,name,mobile,category,
                   repeat_count,user[3],user[0],
                   pax,str(visit_date)))
        conn.commit()

        st.success(f"Guest Added (Visit #{repeat_count})")

        feedback_link=f"https://rjraunakapp.streamlit.app/?feedback=1&branch={user[3]}"
        message=f"Thank you {name} ❤️\nPlease give feedback:\n{feedback_link}"
        encoded=urllib.parse.quote(message)
        whatsapp_url=f"https://wa.me/91{mobile}?text={encoded}"

        st.markdown(f"[📲 Send WhatsApp Feedback]({whatsapp_url})")

# ---------------- MY GUESTS ----------------

if menu=="My Guests":

    df=pd.read_sql_query(
        "SELECT * FROM guests WHERE created_by=?",
        conn,params=(user[0],))

    filter_date=st.date_input("Filter Date")
    df=df[df["visit_date"]==str(filter_date)]

    st.dataframe(df)

    st.download_button("Download Excel",
                       df.to_csv(index=False),
                       "my_guests.csv")

# ---------------- FEEDBACK DATA ----------------

if menu=="Feedback Data":

    fb=pd.read_sql_query("SELECT * FROM feedback",conn)
    st.dataframe(fb)

# ---------------- ADMIN PANEL ----------------

if menu=="Admin Panel" and user[2]=="admin":

    st.subheader("Repeat Guests Report")

    repeat_df=pd.read_sql_query(
        "SELECT name,mobile,repeat_count,visit_date,created_by FROM guests WHERE repeat_count>1",
        conn)

    st.dataframe(repeat_df)

    st.subheader("All Guests")
    st.dataframe(pd.read_sql_query("SELECT * FROM guests",conn))

    st.subheader("All Feedback")
    st.dataframe(pd.read_sql_query("SELECT * FROM feedback",conn))
