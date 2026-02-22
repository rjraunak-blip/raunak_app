import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd
import urllib.parse

st.set_page_config(page_title="CARNIVLE ENTERPRISE", layout="wide")

DB="carnivle_enterprise.db"
conn=sqlite3.connect(DB,check_same_thread=False)
c=conn.cursor()

# ---------------- DATABASE ----------------

c.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
password TEXT,
role TEXT,
branch TEXT,
can_add INTEGER,
can_edit INTEGER,
can_delete INTEGER,
can_download INTEGER
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
visit_date TEXT,
edited INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS feedback(
mobile TEXT,
guest_name TEXT,
branch TEXT,
rating INTEGER,
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
    c.execute("""INSERT INTO users VALUES (?,?,?,?,?,?,?,?)""",
              ("admin",hash_pass("admin123"),"admin",
               "Head Office",1,1,1,1))
    conn.commit()

# ---------------- FEEDBACK PAGE ----------------

query=st.query_params

if "feedback" in query:
    st.title("⭐ Guest Feedback")

    mobile=st.text_input("Mobile Number")
    guest=pd.read_sql_query(
        "SELECT name FROM guests WHERE mobile=? ORDER BY visit_date DESC",
        conn,params=(mobile,))

    if not guest.empty:
        guest_name=guest.iloc[0]["name"]
        st.write("Guest:",guest_name)
    else:
        guest_name=st.text_input("Your Name")

    rating=st.slider("Overall Rating",1,5)
    comment=st.text_area("Comment")

    if st.button("Submit"):
        c.execute("INSERT INTO feedback VALUES (?,?,?,?,?,?)",
                  (mobile,guest_name,"Head Office",
                   rating,comment,str(datetime.date.today())))
        conn.commit()
        st.success("Thank You ❤️")
        st.stop()

# ---------------- LOGIN ----------------

if "login" not in st.session_state:
    st.session_state.login=False

if not st.session_state.login:
    st.title("CARNIVLE ENTERPRISE LOGIN")

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
role=user[2]

# ---------------- SIDEBAR ----------------

st.sidebar.write("User:",user[0])
st.sidebar.write("Role:",role)

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

menu=st.sidebar.radio("Menu",
["Dashboard","Guest Entry","My Guests","Feedback","Admin Panel"])

# ---------------- DASHBOARD ----------------

if menu=="Dashboard":

    df=pd.read_sql_query("SELECT * FROM guests",conn)
    fb=pd.read_sql_query("SELECT * FROM feedback",conn)

    col1,col2,col3=st.columns(3)

    col1.metric("Total Guests",len(df))
    col2.metric("Repeat Guests",
                df[df["repeat_count"]>1].shape[0] if not df.empty else 0)
    col3.metric("Avg Rating",
                round(fb["rating"].mean(),2) if not fb.empty else 0)

# ---------------- GUEST ENTRY ----------------

if menu=="Guest Entry" and user[4]==1:

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

        c.execute("""INSERT INTO guests
        (id,name,mobile,category,repeat_count,
         branch,created_by,pax,visit_date,edited)
         VALUES (?,?,?,?,?,?,?,?,?,?)""",
         (gid,name,mobile,category,repeat_count,
          user[3],user[0],pax,str(visit_date),0))

        conn.commit()

        st.success(f"Guest Added (Visit #{repeat_count})")

        feedback_link="https://YOUR-APP-LINK.streamlit.app/?feedback=1"
        message=f"Thank you {name} ❤️\nPlease give feedback:\n{feedback_link}"
        encoded=urllib.parse.quote(message)
        whatsapp=f"https://wa.me/91{mobile}?text={encoded}"

        st.markdown(f"[📲 Send WhatsApp Feedback]({whatsapp})")

# ---------------- MY GUESTS ----------------

if menu=="My Guests":

    df=pd.read_sql_query(
        "SELECT * FROM guests WHERE created_by=?",
        conn,params=(user[0],))

    st.dataframe(df)

    if user[7]==1:
        st.download_button("Download Excel",
                           df.to_csv(index=False),
                           "my_guests.csv")

# ---------------- FEEDBACK VIEW ----------------

if menu=="Feedback":
    fb=pd.read_sql_query("SELECT * FROM feedback",conn)
    st.dataframe(fb)

# ---------------- ADMIN PANEL ----------------

if menu=="Admin Panel":

    if role!="admin":
        st.error("Admin Only")
        st.stop()

    tab1,tab2,tab3=st.tabs(["Create Staff","All Guests","Repeat Guests"])

    # ---- CREATE STAFF ----
    with tab1:
        new_user=st.text_input("Username")
        new_pass=st.text_input("Password")
        branch=st.text_input("Branch")

        can_add=st.checkbox("Can Add Guest",True)
        can_edit=st.checkbox("Can Edit Guest",True)
        can_delete=st.checkbox("Can Delete Guest",False)
        can_download=st.checkbox("Can Download Excel",True)

        if st.button("Create Staff"):
            try:
                c.execute("""INSERT INTO users VALUES (?,?,?,?,?,?,?,?)""",
                          (new_user,
                           hash_pass(new_pass),
                           "staff",
                           branch,
                           int(can_add),
                           int(can_edit),
                           int(can_delete),
                           int(can_download)))
                conn.commit()
                st.success("Staff Created")
            except:
                st.error("Username Already Exists")

    # ---- ALL GUESTS ----
    with tab2:
        df=pd.read_sql_query("SELECT * FROM guests",conn)
        st.dataframe(df)

        delete_id=st.text_input("Guest ID to Delete")

        if st.button("Delete Guest"):
            c.execute("DELETE FROM guests WHERE id=?",(delete_id,))
            conn.commit()
            st.success("Deleted")

    # ---- REPEAT REPORT ----
    with tab3:
        repeat_df=pd.read_sql_query(
            "SELECT name,mobile,repeat_count,visit_date FROM guests WHERE repeat_count>1",
            conn)
        st.dataframe(repeat_df)
