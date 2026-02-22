import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Carnivle CRM Pro", layout="wide")

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

# ---------------- FEEDBACK PAGE ----------------

query=st.query_params

if "feedback" in query:
    branch=query.get("branch","")

    st.title("⭐ Guest Feedback")

    mobile=st.text_input("Mobile")

    overall=st.slider("Overall Rating",1,5)
    food=st.slider("Food",1,5)
    service=st.slider("Service",1,5)
    staff=st.slider("Staff Behaviour",1,5)
    comment=st.text_area("Comment")

    if st.button("Submit"):
        c.execute("INSERT INTO feedback VALUES (?,?,?,?,?,?,?,?)",
                  (mobile,branch,overall,food,
                   service,staff,comment,
                   str(datetime.date.today())))
        conn.commit()
        st.success("Thank you ❤️")
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

st.sidebar.write("User:",user[0])
st.sidebar.write("Role:",user[2])

menu=st.sidebar.radio("Menu",
["Dashboard","Guest Entry","My Guests","Feedback Data","Admin Panel"])

if st.sidebar.button("Logout"):
    st.session_state.login=False
    st.rerun()

# ---------------- DASHBOARD ----------------

if menu=="Dashboard":

    if user[2]=="admin":
        df=pd.read_sql_query("SELECT * FROM guests",conn)
        fb=pd.read_sql_query("SELECT * FROM feedback",conn)
    else:
        df=pd.read_sql_query("SELECT * FROM guests WHERE created_by=?",
                             conn,params=(user[0],))
        fb=pd.read_sql_query("SELECT * FROM feedback WHERE branch=?",
                             conn,params=(user[3],))

    col1,col2,col3=st.columns(3)

    col1.metric("Total Guests",len(df))
    col2.metric("Repeat Customers",
                df[df["repeat_count"]>1].shape[0] if not df.empty else 0)
    col3.metric("Avg Rating",
                round(fb["overall"].mean(),2) if not fb.empty else 0)

    if not fb.empty:
        low=fb[fb["overall"]<=2]
        if not low.empty:
            st.error("⚠ Low Rating Alert!")

# ---------------- GUEST ENTRY ----------------

if menu=="Guest Entry":

    name=st.text_input("Guest Name")
    mobile=st.text_input("Mobile Number")
    category=st.selectbox("Category",
        ["Walk-in","Zomato","Swiggy","EasyDiner","Party","VIP"])
    pax=st.number_input("PAX",1)

    if st.button("Add Guest"):

        # repeat detect
        old=pd.read_sql_query(
            "SELECT * FROM guests WHERE mobile=?",
            conn,params=(mobile,))

        repeat_count=len(old)+1

        gid=generate_id(name,mobile)

        c.execute("INSERT INTO guests VALUES (?,?,?,?,?,?,?, ?,?)",
                  (gid,name,mobile,category,
                   repeat_count,
                   user[3],user[0],pax,
                   str(datetime.date.today())))
        conn.commit()

        st.success(f"Guest Added (Visit #{repeat_count})")

        # WhatsApp link
        base_url="https://rjraunakapp.streamlit.app"
        feedback_link=f"{base_url}?feedback=1&branch={user[3]}"

        message=f"Thank you {name} for visiting us ❤️\nPlease give your feedback:\n{feedback_link}"
        encoded=urllib.parse.quote(message)

        whatsapp_url=f"https://wa.me/91{mobile}?text={encoded}"

        st.markdown(f"[📲 Send WhatsApp Feedback]({whatsapp_url})")

# ---------------- MY GUESTS ----------------

if menu=="My Guests":

    df=pd.read_sql_query(
        "SELECT * FROM guests WHERE created_by=?",
        conn,params=(user[0],))

    st.dataframe(df)

    if not df.empty:
        st.download_button("Download Excel",
                           df.to_csv(index=False),
                           "my_guests.csv")

# ---------------- FEEDBACK DATA ----------------

if menu=="Feedback Data":

    if user[2]=="admin":
        fb=pd.read_sql_query("SELECT * FROM feedback",conn)
    else:
        fb=pd.read_sql_query("SELECT * FROM feedback WHERE branch=?",
                             conn,params=(user[3],))

    st.dataframe(fb)

# ---------------- ADMIN ----------------

if menu=="Admin Panel" and user[2]=="admin":

    st.subheader("Create Staff")

    new_user=st.text_input("Username")
    new_pass=st.text_input("Password")
    branch=st.text_input("Branch")

    if st.button("Create Staff"):
        c.execute("INSERT INTO users VALUES (?,?,?,?)",
                  (new_user,hash_pass(new_pass),
                   "staff",branch))
        conn.commit()
        st.success("Staff Created")

    st.subheader("All Guests")

    df=pd.read_sql_query("SELECT * FROM guests",conn)
    st.dataframe(df)

    if st.button("Delete All Guests"):
        c.execute("DELETE FROM guests")
        conn.commit()
        st.success("All Data Deleted")
