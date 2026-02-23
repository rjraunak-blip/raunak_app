import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Hospitality CRM System", layout="wide")

# ---------------- DATABASE ---------------- #

conn = sqlite3.connect("hospitality.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS guests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    mobile TEXT,
    category TEXT,
    visit_date TEXT,
    staff_name TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guest_name TEXT,
    mobile TEXT,
    rating INTEGER,
    service TEXT,
    food TEXT,
    behaviour TEXT,
    comment TEXT,
    date TEXT
)
""")

conn.commit()

# ---------------- SIDEBAR NAVIGATION ---------------- #

st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go To", ["Guest Entry", "Feedback Form", "Admin Panel"])

# ---------------- GUEST ENTRY ---------------- #

if page == "Guest Entry":

    st.title("📝 Visitor Entry Form")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Guest Name")
        mobile = st.text_input("Mobile Number")

    with col2:
        category = st.selectbox("Visit Type", ["Restaurant", "Banquet", "Event", "Other"])
        staff = st.text_input("Staff Name")

    if st.button("Submit Entry"):
        if name and mobile and staff:
            c.execute("""
            INSERT INTO guests (name, mobile, category, visit_date, staff_name)
            VALUES (?, ?, ?, ?, ?)
            """, (name, mobile, category, datetime.now().date(), staff))
            conn.commit()
            st.success("Entry Saved Successfully ✅")
        else:
            st.error("Please fill all required fields")

# ---------------- FEEDBACK ---------------- #

elif page == "Feedback Form":

    st.title("⭐ Guest Feedback Form")

    guest_name = st.text_input("Guest Name")
    mobile = st.text_input("Mobile Number")

    rating = st.slider("Overall Rating", 1, 5)

    col1, col2, col3 = st.columns(3)

    with col1:
        service = st.selectbox("Service", ["Excellent", "Good", "Average", "Poor"])
    with col2:
        food = st.selectbox("Food", ["Excellent", "Good", "Average", "Poor"])
    with col3:
        behaviour = st.selectbox("Behaviour", ["Excellent", "Good", "Average", "Poor"])

    comment = st.text_area("Additional Comments")

    if st.button("Submit Feedback"):
        if guest_name and mobile:
            c.execute("""
            INSERT INTO feedback 
            (guest_name, mobile, rating, service, food, behaviour, comment, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (guest_name, mobile, rating, service, food, behaviour, comment, datetime.now().date()))
            conn.commit()
            st.success("Thank You For Your Feedback ❤️")
        else:
            st.error("Please fill required fields")

# ---------------- ADMIN PANEL ---------------- #

elif page == "Admin Panel":

    st.title("🔐 Admin Login")
    password = st.text_input("Enter Admin Password", type="password")

    if password == "admin123":

        st.success("Login Successful ✅")

        st.subheader("📅 Today's Entries")
        today_data = pd.read_sql_query("""
        SELECT * FROM guests
        WHERE visit_date = date('now')
        """, conn)
        st.dataframe(today_data)

        st.subheader("📊 Visit Category Summary")
        category_data = pd.read_sql_query("""
        SELECT category, COUNT(*) as Total
        FROM guests
        GROUP BY category
        """, conn)
        st.dataframe(category_data)
        st.bar_chart(category_data.set_index("category"))

        st.subheader("🔁 Repeat Guests")
        repeat_data = pd.read_sql_query("""
        SELECT name, mobile, COUNT(*) as Visits
        FROM guests
        GROUP BY mobile
        HAVING Visits > 1
        """, conn)
        st.dataframe(repeat_data)

        st.subheader("👨‍💼 Staff Performance")
        staff_data = pd.read_sql_query("""
        SELECT staff_name, COUNT(*) as Total_Entries
        FROM guests
        GROUP BY staff_name
        """, conn)
        st.dataframe(staff_data)
        st.bar_chart(staff_data.set_index("staff_name"))

        st.subheader("⭐ Feedback Overview")
        feedback_data = pd.read_sql_query("""
        SELECT * FROM feedback
        """, conn)
        st.dataframe(feedback_data)

        rating_data = pd.read_sql_query("""
        SELECT rating, COUNT(*) as Total
        FROM feedback
        GROUP BY rating
        """, conn)

        if not rating_data.empty:
            st.bar_chart(rating_data.set_index("rating"))

    elif password != "":
        st.error("Wrong Password ❌")
