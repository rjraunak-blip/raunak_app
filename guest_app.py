import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd
import os

st.set_page_config(page_title="CARNIVLE Enterprise", layout="wide")

DB="carnivle_pro.db"
conn=sqlite3.connect(DB,check_same_thread=False)
c=conn.cursor()

# ================= DATABASE =================

c.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
password TEXT,
role TEXT,
branch TEXT,
can_add_guest INTEGER,
can_view_all INTEGER,
can_download INTEGER
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

def generate_id(name,mobile):
    return hashlib.md5(
        (name+mobile+str(datetime.datetime.now())).encode()
    ).hexdigest()[:8]

# Default Admin
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)",
              ("admin",hash_pass("admin123"),
               "admin","Head Office",1,1,1))
    conn.commit()

# ================= FEEDBACK PAGE =================

query=st.query_params

if "feedback" in query:

    mobile=query["feedback"]
    branch=query.get("branch","Head Office")

    st.title("🍽 CARNIVLE Feedback")

    overall=st.slider("Overall Experience",1,5,4)
    food=st.slider("Food Quality",1,5,4)
    service=st.slider("Service Quality",1,5,4)
    staff=st.slider("Staff Behaviour",1,5,4)
    comment=st.text_area("Comment")

    if st.button("Submit Feedback"):

        # Prevent duplicate feedback same day
        today=str(datetime.date.today())

        check=c.execute("""
        SELECT * FROM feedback
        WHERE mobile=? AND date=?
        """,(mobile,today)).fetchone()

        if check:
            st.warning("Feedback already submitted today")
        else:
            c.execute("""
            INSERT INTO feedback
            VALUES (?,?,?,?,?,?,?,?)
            """,(mobile,branch,overall,
                 food,service,staff,
                 comment,today))
            conn.commit()

            st.success("Thank you ❤️")
            st.balloons()

    st.stop()

# ================= LOGIN =================

if "login" not in st.session_state:
    st.session_state.login=False

if not st.session_state.login:

    st.title("🍽 CARNIVLE Enterprise")

    with st.form("login"):
        u=st.text_input("Username")
        p=st.text_input("Password",type="password")
        btn=st.form_submit_button("Login")

    if btn:
        data=c.execute("SELECT * FROM users WHERE username=?",(u,)).fetchone()
        if data and data[1]==hash_pass(p):
            st.session_state.login=True
            st.session_state.user=data
            st.rerun()
        else:
            st.error("Invalid Login")

    st.stop()

user=st.session_state.user

# ================= SIDEBAR =================

st.sidebar.title("CARNIVLE")
st.sidebar.write(f"User: {user[0]}")
st.sidebar.write(f"Role: {user[2]}")
st.sidebar.write(f"Branch: {user[3]}")

if user[2]=="admin":
    menu=st.sidebar.radio("Menu",
        ["Dashboard","Guest Entry","Admin Panel"])
else:
    menu=st.sidebar.radio("Menu",
        ["Dashboard","Guest Entry"])

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

    col1,col2,col3=st.columns(3)

    col1.metric("Total Guests",len(df))
    col2.metric("Total PAX",df["pax"].sum() if not df.empty else 0)
    col3.metric("Avg Rating",
                round(fb["overall"].mean(),2)
                if not fb.empty else 0)

    # Low Rating Alert
    low=fb[fb["overall"]<=2]
    if not low.empty:
        st.error("⚠️ Low Rating Alert!")

    st.dataframe(df)

# ================= GUEST ENTRY =================

if menu=="Guest Entry":

    st.subheader("Add Guest")

    with st.form("guest_form",clear_on_submit=True):

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
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (gid,name,mobile,user[3],
         user[0],category,pax,vip,
         str(datetime.date.today())))

        conn.commit()

        st.success("Guest Added ✅")

        # Feedback link generate
        link=f"?feedback={mobile}&branch={user[3]}"
        st.info("Send this link to customer:")
        st.code(link)

# ================= ADMIN =================

if menu=="Admin Panel" and user[2]=="admin":

    st.subheader("Admin Control")

    tab1,tab2=st.tabs(["Create Staff","All Feedback"])

    with tab1:
        new_user=st.text_input("Username")
        new_pass=st.text_input("Password")
        branch=st.text_input("Branch")

        if st.button("Create Staff"):
            c.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)",
                      (new_user,
                       hash_pass(new_pass),
                       "staff",
                       branch,
                       1,0,0))
            conn.commit()
            st.success("Staff Created")

    with tab2:
        st.dataframe(pd.read_sql_query("SELECT * FROM feedback",conn))
