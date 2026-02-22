import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd
import qrcode
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import TableStyle
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

c.execute("""CREATE TABLE IF NOT EXISTS branches(
branch_name TEXT PRIMARY KEY
)""")

c.execute("""CREATE TABLE IF NOT EXISTS guests(
id TEXT PRIMARY KEY,
name TEXT,
mobile TEXT,
branch TEXT,
created_by TEXT,
pax INTEGER,
date TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS feedback(
mobile TEXT,
branch TEXT,
overall INTEGER,
staff INTEGER,
food INTEGER,
service INTEGER,
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
              ("admin",hash_pass("admin123"),"admin",
               "Head Office",1,1,1))
    conn.commit()

# ================= THEME =================
if "dark" not in st.session_state:
    st.session_state.dark=False

if st.sidebar.button("🌗 Toggle Dark Mode"):
    st.session_state.dark=not st.session_state.dark

if st.session_state.dark:
    st.markdown("""
        <style>
        body {background-color:#111;color:white;}
        </style>
    """,unsafe_allow_html=True)

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

    col1,col2,col3=st.columns(3)

    col1.metric("Total Guests",len(df))
    col2.metric("Total PAX",
                df["pax"].sum() if not df.empty else 0)
    col3.metric("Avg Rating",
                round(fb["overall"].mean(),2)
                if not fb.empty else 0)

    # Complaint Alert
    low=fb[fb["overall"]<=2]
    if not low.empty:
        st.error("⚠️ Low Rating Alert!")

# ================= GUEST ENTRY =================
if menu=="Guest Entry" and user[4]==1:

    st.subheader("Add Guest")

    name=st.text_input("Name")
    mobile=st.text_input("Mobile")
    pax=st.number_input("PAX",1)

    if st.button("Add"):
        gid=generate_id(name,mobile)
        c.execute("INSERT INTO guests VALUES (?,?,?,?,?,?,?)",
                  (gid,name,mobile,user[3],
                   user[0],pax,str(datetime.date.today())))
        conn.commit()
        st.success("Guest Added")

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

        url=f"https://yourapp.streamlit.app/?feedback=table{table}&branch={user[3]}"

        img=qrcode.make(url)
        img.save("qr.png")
        st.image("qr.png")

# ================= PDF REPORT =================
if menu=="Reports":

    if st.button("Generate Monthly Report"):

        doc=SimpleDocTemplate("report.pdf")
        elements=[]
        styles=getSampleStyleSheet()

        df=pd.read_sql_query(
            "SELECT * FROM guests WHERE branch=?",
            conn,params=(user[3],))

        elements.append(Paragraph("CARNIVLE Monthly Report",
                                  styles["Heading1"]))
        elements.append(Spacer(1,0.5*inch))

        data=[df.columns.tolist()]+df.values.tolist()
        t=Table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.grey),
            ('GRID',(0,0),(-1,-1),1,colors.black)
        ]))

        elements.append(t)
        doc.build(elements)

        with open("report.pdf","rb") as f:
            st.download_button("Download Report",f,"report.pdf")

# ================= ADMIN =================
if menu=="Admin Panel" and user[2]=="admin":

    tab1,tab2=st.tabs(["Create Staff","Access Control"])

    with tab1:
        st.subheader("Add Staff")

        new_user=st.text_input("Username")
        new_pass=st.text_input("Password")
        role=st.selectbox("Role",["staff","manager"])
        branch=st.text_input("Branch")

        if st.button("Create Staff"):
            c.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)",
                      (new_user,hash_pass(new_pass),
                       role,branch,1,0,0))
            conn.commit()
            st.success("Created")

    with tab2:
        st.subheader("Access Control")

        all_users=pd.read_sql_query(
            "SELECT * FROM users",conn)

        st.dataframe(all_users)

        sel=st.text_input("Username to Modify")
        add=st.checkbox("Can Add Guest")
        view=st.checkbox("Can View All Data")
        download=st.checkbox("Can Download")

        if st.button("Update Access"):
            c.execute("""UPDATE users SET
                      can_add_guest=?,
                      can_view_all=?,
                      can_download=?
                      WHERE username=?""",
                      (int(add),int(view),
                       int(download),sel))
            conn.commit()
            st.success("Access Updated")
