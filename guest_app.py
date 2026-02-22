import streamlit as st
import sqlite3
import hashlib
import datetime

st.set_page_config(page_title="Carnivale System", layout="wide")

# ================= DATABASE =================
conn = sqlite3.connect("carnivale.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users(
uid TEXT,
username TEXT,
password TEXT,
can_add INTEGER,
can_view INTEGER
)""")

c.execute("""CREATE TABLE IF NOT EXISTS guests(
gid TEXT,
name TEXT,
mobile TEXT,
category TEXT,
pax INTEGER,
added_by TEXT,
date TEXT,
feedback_done INTEGER
)""")

c.execute("""CREATE TABLE IF NOT EXISTS feedback(
mobile TEXT,
rating INTEGER,
comment TEXT,
date TEXT
)""")

conn.commit()

# ================= DEFAULT ADMIN =================
admin_pass = hashlib.md5("admin123".encode()).hexdigest()
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users VALUES (?,?,?,?,?)",
              ("1","admin",admin_pass,1,1))
    conn.commit()

# ================= SESSION =================
if "login" not in st.session_state:
    st.session_state.login=False
if "user" not in st.session_state:
    st.session_state.user=None

# ================= PUBLIC FEEDBACK =================
params = st.query_params
if "feedback" in params:
    mobile = params["feedback"]
    st.title("Guest Feedback")

    rating = st.slider("Rate Us (1-5)",1,5)
    comment = st.text_area("Comment")

    if st.button("Submit"):
        c.execute("INSERT INTO feedback VALUES (?,?,?,?)",
                  (mobile,rating,comment,str(datetime.date.today())))
        c.execute("UPDATE guests SET feedback_done=1 WHERE mobile=?",
                  (mobile,))
        conn.commit()
        st.success("Thank You ❤️")
        st.stop()

# ================= LOGIN =================
def login_user(username,password):
    hashed=hashlib.md5(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username,hashed))
    return c.fetchone()

if not st.session_state.login:

    st.title("Login")

    c.execute("SELECT username FROM users")
    all_users=[u[0] for u in c.fetchall()]

    selected_user=st.selectbox("Select ID",all_users)
    password=st.text_input("Password",type="password")

    if st.button("Login"):
        user=login_user(selected_user,password)
        if user:
            st.session_state.login=True
            st.session_state.user=user
            st.rerun()
        else:
            st.error("Wrong Password")

    st.stop()

user=st.session_state.user

# ================= LOGOUT =================
col1,col2=st.columns([8,1])
with col2:
    if st.button("Logout"):
        st.session_state.login=False
        st.session_state.user=None
        st.rerun()

menu=st.sidebar.selectbox("Menu",
                          ["Add Guest","Dashboard","Manage Staff"])

# ================= ADD GUEST =================
if menu=="Add Guest" and user[3]==1:

    st.subheader("Fast Guest Entry")

    with st.form("guest_form",clear_on_submit=True):

        name=st.text_input("Guest Name")
        mobile=st.text_input("Mobile")
        category=st.selectbox("Category",
                              ["Walk-In","Zomato",
                               "Swiggy","VIP","Party"])
        pax=st.number_input("PAX",min_value=1,step=1)

        submit=st.form_submit_button("Add Guest")

        if submit:

            if name=="" or mobile=="":
                st.warning("Name & Mobile Required")
            else:

                c.execute("SELECT * FROM guests WHERE mobile=?",(mobile,))
                repeat=c.fetchone()

                if repeat:
                    st.warning("⚠ Repeat Guest Detected")

                gid=hashlib.md5(
                    (name+mobile+
                     str(datetime.datetime.now())
                     ).encode()).hexdigest()[:8]

                c.execute("INSERT INTO guests VALUES (?,?,?,?,?,?,?,?)",
                          (gid,name,mobile,category,pax,
                           user[1],
                           str(datetime.date.today()),0))
                conn.commit()

                base=st.secrets.get("BASE_URL","")

                link=f"{base}/?feedback={mobile}"

                st.success("Guest Added")

                if base!="":
                    st.markdown(
                        f"[Send WhatsApp Feedback](https://wa.me/{mobile}?text=Thank%20you%20for%20visiting!%20Please%20share%20feedback:%20{link})"
                    )

# ================= DASHBOARD =================
if menu=="Dashboard" and user[4]==1:

    st.subheader("Dashboard")

    selected_date=st.date_input("Select Date",
                                 datetime.date.today())

    c.execute("SELECT * FROM guests WHERE date=?",
              (str(selected_date),))
    rows=c.fetchall()

    st.write("Total Guests:",len(rows))

    for r in rows:
        st.write(
            r[1],"|",r[2],
            "|",r[3],
            "| PAX:",r[4],
            "| Added By:",r[5],
            "| Feedback:",
            "Done" if r[7]==1 else "Pending"
        )

# ================= MANAGE STAFF =================
if menu=="Manage Staff" and user[1]=="admin":

    st.subheader("Create Staff")

    new_user=st.text_input("Username")
    new_pass=st.text_input("Password")
    can_add=st.checkbox("Can Add Guest")
    can_view=st.checkbox("Can View Dashboard")

    if st.button("Create"):
        hashed=hashlib.md5(new_pass.encode()).hexdigest()
        uid=hashlib.md5(new_user.encode()).hexdigest()[:6]
        c.execute("INSERT INTO users VALUES (?,?,?,?,?)",
                  (uid,new_user,hashed,
                   1 if can_add else 0,
                   1 if can_view else 0))
        conn.commit()
        st.success("Staff Created")

    st.divider()
    st.subheader("Delete Staff")

    c.execute("SELECT username FROM users WHERE username!='admin'")
    staff=[s[0] for s in c.fetchall()]

    del_user=st.selectbox("Select Staff",staff)

    if st.button("Delete Staff"):
        c.execute("DELETE FROM users WHERE username=?",(del_user,))
        conn.commit()
        st.success("Deleted")
