import streamlit as st
import sqlite3
import pandas as pd
import datetime
import hashlib

st.set_page_config(page_title="Guest Management System", layout="wide")

# ---------------- DATABASE ---------------- #

conn = sqlite3.connect("carnival_pro.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
password TEXT,
role TEXT,
branch TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS guests(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
mobile TEXT,
category TEXT,
staff TEXT,
branch TEXT,
pax INTEGER,
date TEXT,
edited INTEGER DEFAULT 0
)""")

c.execute("""CREATE TABLE IF NOT EXISTS feedback(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
mobile TEXT,
rating INTEGER,
comment TEXT,
date TEXT
)""")

conn.commit()

# ---------------- PASSWORD HASH ---------------- #

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

# Create default admin
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users VALUES (?,?,?,?)",
              ("admin", hash_pass("admin123"), "admin", "main"))
    conn.commit()

# ---------------- LOGOUT ---------------- #

def logout():
    st.session_state.clear()
    st.rerun()

# ---------------- LOGIN ---------------- #

if "user" not in st.session_state:

    st.title("Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            c.execute("SELECT * FROM users WHERE username=?",
                      (username,))
            user = c.fetchone()

            if user and user[1] == hash_pass(password):
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

# ---------------- LOGGED USER ---------------- #

user = st.session_state.user
role = user[2]
branch = user[3]

st.sidebar.write(f"Logged in as: {user[0]} ({role})")
st.sidebar.button("Logout", on_click=logout)

# ---------------- FEEDBACK PAGE ---------------- #

query_params = st.query_params

if "feedback" in query_params:

    st.title("Guest Feedback Form")

    with st.form("feedback_form"):
        name = st.text_input("Your Name")
        mobile = st.text_input("Mobile Number")
        rating = st.slider("Rating", 1, 5)
        comment = st.text_area("Comment")
        submit = st.form_submit_button("Submit Feedback")

        if submit:
            c.execute("INSERT INTO feedback (name,mobile,rating,comment,date) VALUES (?,?,?,?,?)",
                      (name, mobile, rating, comment,
                       str(datetime.date.today())))
            conn.commit()
            st.success("Thank You for Feedback ❤️")

    st.stop()

# ---------------- STAFF PANEL ---------------- #

if role == "staff":

    st.title("Staff Panel")

    with st.form("guest_entry"):
        name = st.text_input("Guest Name")
        mobile = st.text_input("Mobile")
        category = st.selectbox("Category", ["Walk-in", "VIP", "Online"])
        pax = st.number_input("PAX", min_value=1)
        submit = st.form_submit_button("Add Guest")

        if submit:
            today = str(datetime.date.today())

            c.execute("SELECT COUNT(*) FROM guests WHERE mobile=?",
                      (mobile,))
            repeat = c.fetchone()[0]

            c.execute("""INSERT INTO guests
            (name,mobile,category,staff,branch,pax,date)
            VALUES (?,?,?,?,?,?,?)""",
                      (name, mobile, category,
                       user[0], branch, pax, today))
            conn.commit()

            feedback_link = "https://rjraunakapp.streamlit.app/?feedback=1"

            whatsapp_link = f"https://wa.me/91{mobile}?text=Thank%20you%20for%20visiting.%20Please%20give%20feedback:%20{feedback_link}"

            if repeat > 0:
                st.warning("Repeat Customer ⚠️")

            st.success("Guest Added Successfully")
            st.markdown(f"[Send Feedback WhatsApp]({whatsapp_link})")

    st.subheader("My Entries")

    df = pd.read_sql_query(
        f"SELECT * FROM guests WHERE staff='{user[0]}'",
        conn)

    st.dataframe(df)

    st.download_button("Download Excel",
                       df.to_csv(index=False),
                       file_name="my_entries.csv")

# ---------------- ADMIN PANEL ---------------- #

if role == "admin":

    st.title("Admin Panel")

    tab1, tab2, tab3 = st.tabs(
        ["All Guests", "Staff Management", "Feedback"])

    # -------- ALL GUESTS -------- #

    with tab1:

        df = pd.read_sql_query("SELECT * FROM guests", conn)

        st.dataframe(df)

        st.download_button("Download Excel",
                           df.to_csv(index=False),
                           file_name="all_guests.csv")

        delete_id = st.number_input("Delete Guest ID",
                                    min_value=0)

        if st.button("Delete Guest"):
            c.execute("DELETE FROM guests WHERE id=?",
                      (delete_id,))
            conn.commit()
            st.success("Deleted")

    # -------- STAFF MANAGEMENT -------- #

    with tab2:

        st.subheader("Create Staff")

        new_user = st.text_input("Staff Username")
        new_pass = st.text_input("Staff Password",
                                 type="password")
        branch_name = st.text_input("Branch")

        if st.button("Create Staff"):
            try:
                c.execute("INSERT INTO users VALUES (?,?,?,?)",
                          (new_user,
                           hash_pass(new_pass),
                           "staff",
                           branch_name))
                conn.commit()
                st.success("Staff Created")
            except:
                st.error("Username already exists")

        st.subheader("All Users")
        users_df = pd.read_sql_query(
            "SELECT username,role,branch FROM users",
            conn)
        st.dataframe(users_df)

    # -------- FEEDBACK -------- #

    with tab3:

        feedback_df = pd.read_sql_query(
            "SELECT * FROM feedback",
            conn)

        st.dataframe(feedback_df)

        st.download_button("Download Feedback",
                           feedback_df.to_csv(index=False),
                           file_name="feedback.csv")
