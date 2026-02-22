import streamlit as st
import sqlite3
import hashlib
import datetime

st.set_page_config(page_title="Carnivale Guest System", layout="wide")

# ================= DATABASE =================
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users(
id TEXT,
username TEXT,
password TEXT,
can_add_guest INTEGER,
can_view_dashboard INTEGER
)""")

c.execute("""CREATE TABLE IF NOT EXISTS guests(
gid TEXT,
name TEXT,
mobile TEXT,
category TEXT,
added_by TEXT,
pax INTEGER,
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
admin_user = "admin"
admin_pass = hashlib.md5("admin123".encode()).hexdigest()

c.execute("SELECT * FROM users WHERE username=?", (admin_user,))
if not c.fetchone():
    c.execute("INSERT INTO users VALUES (?,?,?,?,?)",
              ("1", admin_user, admin_pass, 1, 1))
    conn.commit()

# ================= LOGIN =================
if "login" not in st.session_state:
    st.session_state.login = False
if "user" not in st.session_state:
    st.session_state.user = None

def login_user(username, password):
    hashed = hashlib.md5(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hashed))
    return c.fetchone()

# ================= FEEDBACK PUBLIC =================
query_params = st.query_params

if "feedback" in query_params:

    mobile = query_params["feedback"]

    st.title("Carnivale Feedback")

    rating = st.slider("Rate Us (1-5)", 1, 5)
    comment = st.text_area("Your Feedback")

    if st.button("Submit Feedback"):

        c.execute("INSERT INTO feedback VALUES (?,?,?,?)",
                  (mobile, rating, comment, str(datetime.date.today())))
        c.execute("UPDATE guests SET feedback_done=1 WHERE mobile=?",
                  (mobile,))
        conn.commit()

        st.success("Thank you for your feedback ❤️")
        st.stop()

# ================= LOGIN PAGE =================
if not st.session_state.login:

    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state.login = True
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Invalid Credentials")

    st.stop()

user = st.session_state.user

menu = st.sidebar.selectbox("Menu",
                             ["Add Guest",
                              "Dashboard",
                              "Manage Staff"])

# ================= ADD GUEST =================
if menu == "Add Guest" and user[3] == 1:

    st.subheader("Fast Guest Entry")

    with st.form("guest_form", clear_on_submit=True):

        name = st.text_input("Guest Name")
        mobile = st.text_input("Mobile")
        category = st.selectbox(
            "Category",
            ["Walk-In","Zomato","Swiggy",
             "Eazy Dinner","Party","VIP"]
        )
        pax = st.number_input("PAX", min_value=1, step=1)

        submit = st.form_submit_button("Add Guest")

        if submit:

            if name == "" or mobile == "":
                st.warning("Name & Mobile required")
            else:

                gid = hashlib.md5(
                    (name+mobile+str(datetime.datetime.now())
                     ).encode()).hexdigest()[:8]

                c.execute("INSERT INTO guests VALUES (?,?,?,?,?,?,?,?)",
                          (gid,name,mobile,category,
                           user[0],pax,
                           str(datetime.date.today()),0))
                conn.commit()

                base_url = st.secrets.get("BASE_URL","")

                link = f"{base_url}/?feedback={mobile}"

                st.success("Guest Added")

                if base_url != "":
                    st.markdown(f"""
                    📲 **Send WhatsApp Link**  
                    [Click to Send](https://wa.me/{mobile}?text=Thank%20you%20for%20visiting%20Carnivale!%20Please%20share%20feedback:%20{link})
                    """)

# ================= DASHBOARD =================
if menu == "Dashboard" and user[4] == 1:

    st.subheader("Today Guests")

    today = str(datetime.date.today())

    c.execute("SELECT * FROM guests WHERE date=?",(today,))
    rows = c.fetchall()

    st.write("Total Guests Today:", len(rows))

    for r in rows:
        st.write(
            r[1],
            "|",
            r[2],
            "|",
            r[3],
            "| PAX:", r[5],
            "| Feedback:",
            "Done" if r[7]==1 else "Pending"
        )

# ================= MANAGE STAFF =================
if menu == "Manage Staff" and user[1] == "admin":

    st.subheader("Create Staff")

    new_user = st.text_input("Staff Username")
    new_pass = st.text_input("Staff Password")
    can_add = st.checkbox("Can Add Guest")
    can_view = st.checkbox("Can View Dashboard")

    if st.button("Create Staff"):

        if new_user == "" or new_pass == "":
            st.warning("Enter details")
        else:
            hashed = hashlib.md5(new_pass.encode()).hexdigest()

            c.execute("INSERT INTO users VALUES (?,?,?,?,?)",
                      (hashlib.md5(new_user.encode()).hexdigest()[:6],
                       new_user,
                       hashed,
                       1 if can_add else 0,
                       1 if can_view else 0))
            conn.commit()

            st.success("Staff Created")

    st.divider()
    st.subheader("Existing Staff")

    c.execute("SELECT username FROM users WHERE username!='admin'")
    staff = c.fetchall()

    for s in staff:
        st.write(s[0])
