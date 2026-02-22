import streamlit as st
import sqlite3
import pandas as pd
import datetime
import base64
import matplotlib.pyplot as plt

st.set_page_config(page_title="Carnivale Feedback System",layout="wide")

conn = sqlite3.connect("data.db",check_same_thread=False)
c = conn.cursor()

# ---------------- DATABASE ----------------

c.execute("""CREATE TABLE IF NOT EXISTS admins(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
password TEXT)""")

c.execute("""CREATE TABLE IF NOT EXISTS staff(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
password TEXT,
branch TEXT)""")

c.execute("""CREATE TABLE IF NOT EXISTS guests(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
mobile TEXT,
branch TEXT,
staff TEXT,
date TEXT)""")

c.execute("""CREATE TABLE IF NOT EXISTS feedback(
id INTEGER PRIMARY KEY AUTOINCREMENT,
guest_name TEXT,
mobile TEXT,
branch TEXT,
food INTEGER,
service INTEGER,
behaviour INTEGER,
cleanliness INTEGER,
ambience INTEGER,
overall INTEGER,
nps INTEGER,
comment TEXT,
date TEXT)""")

conn.commit()

# Create default admin
admin_exist = c.execute("SELECT * FROM admins").fetchall()
if not admin_exist:
    c.execute("INSERT INTO admins (username,password) VALUES (?,?)",("admin","admin123"))
    conn.commit()

BASE_URL = "https://your-app-url.streamlit.app"

# ---------------- LOGIN SYSTEM ----------------

if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:

    st.title("🔐 Login Panel")
    role = st.selectbox("Login As",["Admin","Staff"])
    user = st.text_input("Username")
    pw = st.text_input("Password",type="password")

    if st.button("Login"):

        if role=="Admin":
            data = c.execute("SELECT * FROM admins WHERE username=? AND password=?",(user,pw)).fetchone()
            if data:
                st.session_state.role="admin"
                st.rerun()

        if role=="Staff":
            data = c.execute("SELECT * FROM staff WHERE username=? AND password=?",(user,pw)).fetchone()
            if data:
                st.session_state.role="staff"
                st.session_state.staff=user
                st.session_state.branch=data[3]
                st.rerun()

    st.stop()

# Logout
if st.sidebar.button("Logout"):
    st.session_state.role=None
    st.rerun()

# ---------------- ADMIN DASHBOARD ----------------

if st.session_state.role=="admin":

    st.title("👑 Admin Dashboard")

    tab1,tab2,tab3 = st.tabs(["Create Staff","View Feedback","Analytics"])

    # Create Staff
    with tab1:
        u = st.text_input("Staff Username")
        p = st.text_input("Password")
        b = st.text_input("Branch")
        if st.button("Create Staff"):
            c.execute("INSERT INTO staff (username,password,branch) VALUES (?,?,?)",(u,p,b))
            conn.commit()
            st.success("Staff Created")

    # View Feedback
    with tab2:
        fb = pd.read_sql_query("SELECT * FROM feedback",conn)

        if not fb.empty:
            st.dataframe(fb)

            low = fb[fb["overall"]<=2]
            if not low.empty:
                st.error("⚠ Low Rating Found")
                st.dataframe(low)

    # Analytics
    with tab3:
        fb = pd.read_sql_query("SELECT * FROM feedback",conn)
        if not fb.empty:
            fb["month"]=pd.to_datetime(fb["date"]).dt.month
            monthly = fb.groupby("month")["overall"].mean()

            fig = plt.figure()
            monthly.plot()
            st.pyplot(fig)

            # Repeat guest compare
            repeat = fb.groupby("mobile")["overall"].mean()
            st.subheader("Repeat Guest Satisfaction")
            st.dataframe(repeat)

# ---------------- STAFF DASHBOARD ----------------

if st.session_state.role=="staff":

    st.title("👨‍💼 Staff Panel")

    with st.form("guest_form",clear_on_submit=True):

        name = st.text_input("Guest Name")
        mobile = st.text_input("Mobile Number")
        submit = st.form_submit_button("Add Guest")

        if submit:
            c.execute("INSERT INTO guests (name,mobile,branch,staff,date) VALUES (?,?,?,?,?)",
                      (name,mobile,st.session_state.branch,st.session_state.staff,str(datetime.date.today())))
            conn.commit()

            link = f"{BASE_URL}?feedback={mobile}&branch={st.session_state.branch}"

            whatsapp = f"https://wa.me/{mobile}?text=Please give your valuable feedback {link}"

            st.success("Guest Added")
            st.markdown(f"[Send WhatsApp Feedback Link]({whatsapp})")

    # Staff Daily Data
    today = str(datetime.date.today())
    staff_data = pd.read_sql_query(
        "SELECT * FROM guests WHERE staff=? AND date=?",
        conn,
        params=(st.session_state.staff,today)
    )

    if not staff_data.empty:
        st.subheader("Today's Entries")
        st.dataframe(staff_data)

        csv = staff_data.to_csv(index=False).encode()
        st.download_button("Download Excel",csv,"staff_data.csv","text/csv")

# ---------------- FEEDBACK PAGE ----------------

query = st.query_params

if "feedback" in query:

    mobile = query["feedback"]
    branch = query.get("branch","Main")

    st.title("🍽 Carnivale Restaurant Feedback")

    guest_data = pd.read_sql_query(
        "SELECT name FROM guests WHERE mobile=? ORDER BY date DESC LIMIT 1",
        conn,params=(mobile,)
    )

    guest_name = guest_data.iloc[0]["name"] if not guest_data.empty else ""

    st.write("Guest:",guest_name)
    st.write("Branch:",branch)

    with st.form("feedback_form"):

        food = st.select_slider("Food Quality ⭐",
                                options=[1,2,3,4,5],value=4)

        service = st.select_slider("Service ⭐",
                                   options=[1,2,3,4,5],value=4)

        behaviour = st.select_slider("Staff Behaviour ⭐",
                                     options=[1,2,3,4,5],value=4)

        cleanliness = st.select_slider("Cleanliness ⭐",
                                        options=[1,2,3,4,5],value=4)

        ambience = st.select_slider("Ambience ⭐",
                                     options=[1,2,3,4,5],value=4)

        overall = st.select_slider("Overall Experience ⭐",
                                    options=[1,2,3,4,5],value=4)

        nps = st.slider("How likely are you to recommend us? (0-10)",
                        0,10,8)

        comment = st.text_area("Additional Comments")

        submit = st.form_submit_button("Submit Feedback")

        if submit:

            c.execute("""INSERT INTO feedback
            (guest_name,mobile,branch,
            food,service,behaviour,
            cleanliness,ambience,overall,
            nps,comment,date)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (guest_name,mobile,branch,
             food,service,behaviour,
             cleanliness,ambience,overall,
             nps,comment,
             str(datetime.date.today())))

            conn.commit()

            st.success("Thank You ❤️")
            st.balloons()

    st.stop()
