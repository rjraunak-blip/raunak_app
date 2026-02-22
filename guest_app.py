import streamlit as st
import sqlite3
import pandas as pd
import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="Carnivale Feedback System", layout="wide")

conn = sqlite3.connect("data.db", check_same_thread=False)
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
branch TEXT,
can_export INTEGER,
can_add INTEGER)""")

c.execute("""CREATE TABLE IF NOT EXISTS guests(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
mobile TEXT,
category TEXT,
guest_count INTEGER,
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

# Default admin
if not c.execute("SELECT * FROM admins").fetchone():
    c.execute("INSERT INTO admins (username,password) VALUES (?,?)", ("admin", "admin123"))
    conn.commit()

BASE_URL = "https://your-app-url.streamlit.app"

# ---------------- LOGIN ----------------

if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.title("🔐 Login")

    role = st.selectbox("Login As", ["Admin", "Staff"])
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")

    if st.button("Login"):

        if role == "Admin":
            data = c.execute("SELECT * FROM admins WHERE username=? AND password=?", (user, pw)).fetchone()
            if data:
                st.session_state.role = "admin"
                st.rerun()

        if role == "Staff":
            data = c.execute("SELECT * FROM staff WHERE username=? AND password=?", (user, pw)).fetchone()
            if data:
                st.session_state.role = "staff"
                st.session_state.staff = user
                st.session_state.branch = data[3]
                st.session_state.can_export = data[4]
                st.session_state.can_add = data[5]
                st.rerun()

    st.stop()

# Logout
if st.sidebar.button("Logout"):
    st.session_state.role = None
    st.rerun()

# ---------------- ADMIN PANEL ----------------

if st.session_state.role == "admin":

    st.title("👑 Admin Dashboard")

    tab1, tab2, tab3 = st.tabs(["Create Staff", "View Feedback", "Analytics"])

    # Create Staff with Access Control
    with tab1:
        u = st.text_input("Staff Username")
        p = st.text_input("Password")
        b = st.text_input("Branch")

        can_add = st.checkbox("Can Add Guests", value=True)
        can_export = st.checkbox("Can Export Data", value=True)

        if st.button("Create Staff"):
            c.execute("""INSERT INTO staff 
            (username,password,branch,can_export,can_add)
            VALUES (?,?,?,?,?)""",
                      (u, p, b, int(can_export), int(can_add)))
            conn.commit()
            st.success("Staff Created Successfully")

    # View Feedback
    with tab2:
        fb = pd.read_sql_query("SELECT * FROM feedback", conn)
        if not fb.empty:
            st.dataframe(fb)

            low = fb[fb["overall"] <= 2]
            if not low.empty:
                st.error("⚠ Complaint Alert")
                st.dataframe(low)

    # Analytics
    with tab3:
        fb = pd.read_sql_query("SELECT * FROM feedback", conn)
        if not fb.empty:
            fb["month"] = pd.to_datetime(fb["date"]).dt.month
            monthly = fb.groupby("month")["overall"].mean()

            fig = plt.figure()
            monthly.plot()
            st.pyplot(fig)

            repeat = fb.groupby("mobile")["overall"].mean()
            st.subheader("Repeat Guest Satisfaction")
            st.dataframe(repeat)

# ---------------- STAFF PANEL ----------------

if st.session_state.role == "staff":

    st.title("👨‍💼 Staff Panel")

    if st.session_state.can_add:

        with st.form("guest_form", clear_on_submit=True):

            name = st.text_input("Guest Name")
            mobile = st.text_input("Mobile Number")

            category = st.selectbox("Category", [
                "Regular",
                "Party",
                "Zomato",
                "VIP",
                "Easy Dinner",
                "Corporate Party",
                "Walk-in"
            ])

            guest_count = st.number_input("Number of Guests", min_value=1, step=1)

            date = st.date_input("Visit Date", datetime.date.today())

            submit = st.form_submit_button("Add Guest")

            if submit:
                c.execute("""INSERT INTO guests 
                (name,mobile,category,guest_count,branch,staff,date)
                VALUES (?,?,?,?,?,?,?)""",
                          (name, mobile, category, guest_count,
                           st.session_state.branch,
                           st.session_state.staff,
                           str(date)))
                conn.commit()

                link = f"{BASE_URL}?feedback={mobile}&branch={st.session_state.branch}"
                whatsapp = f"https://wa.me/{mobile}?text=Please give your valuable feedback {link}"

                st.success("Guest Added Successfully")
                st.markdown(f"[📲 Send WhatsApp Feedback Link]({whatsapp})")

    today = str(datetime.date.today())

    staff_data = pd.read_sql_query("""
    SELECT * FROM guests 
    WHERE staff=? AND date=?""",
                                    conn,
                                    params=(st.session_state.staff, today))

    if not staff_data.empty:
        st.subheader("Today's Entries")
        st.dataframe(staff_data)

        if st.session_state.can_export:
            csv = staff_data.to_csv(index=False).encode()
            st.download_button("Download Excel", csv,
                               "staff_data.csv", "text/csv")

# ---------------- FEEDBACK PAGE ----------------

query = st.query_params

if "feedback" in query:

    mobile = query["feedback"]
    branch = query.get("branch", "Main")

    st.title("🍽 Carnivale Feedback")

    guest_data = pd.read_sql_query(
        "SELECT name FROM guests WHERE mobile=? ORDER BY date DESC LIMIT 1",
        conn, params=(mobile,)
    )

    guest_name = guest_data.iloc[0]["name"] if not guest_data.empty else ""

    with st.form("feedback_form"):

        food = st.slider("Food Quality ⭐", 1, 5, 4)
        service = st.slider("Service ⭐", 1, 5, 4)
        behaviour = st.slider("Staff Behaviour ⭐", 1, 5, 4)
        cleanliness = st.slider("Cleanliness ⭐", 1, 5, 4)
        ambience = st.slider("Ambience ⭐", 1, 5, 4)
        overall = st.slider("Overall Experience ⭐", 1, 5, 4)
        nps = st.slider("Recommend us? (0-10)", 0, 10, 8)
        comment = st.text_area("Additional Comments")

        if st.form_submit_button("Submit Feedback"):

            c.execute("""INSERT INTO feedback
            (guest_name,mobile,branch,
            food,service,behaviour,
            cleanliness,ambience,overall,
            nps,comment,date)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (guest_name, mobile, branch,
                       food, service, behaviour,
                       cleanliness, ambience, overall,
                       nps, comment,
                       str(datetime.date.today())))
            conn.commit()

            st.success("Thank You ❤️")
            st.balloons()

    st.stop()
