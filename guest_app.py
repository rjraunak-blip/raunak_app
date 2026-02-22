import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Restaurant Intelligence CRM", layout="wide")

# ---------------- LOGIN SYSTEM ----------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

def login():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if username == "admin" and password == "1234":
            st.session_state.logged_in = True
            st.session_state.role = "admin"

        elif username == "staff" and password == "1234":
            st.session_state.logged_in = True
            st.session_state.role = "staff"

        else:
            st.error("Invalid Credentials")

if not st.session_state.logged_in:
    login()
    st.stop()

# ---------------- LOGOUT BUTTON ----------------

st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False}))

# ---------------- DATA STORAGE ----------------

if "data" not in st.session_state:
    st.session_state.data = []

# ---------------- MENU ----------------

if st.session_state.role == "admin":
    menu = st.sidebar.radio("Menu", ["Staff Entry", "Feedback Form", "Dashboard"])
else:
    menu = st.sidebar.radio("Menu", ["Staff Entry"])

# ===================================================
# ================= STAFF ENTRY =====================
# ===================================================

if menu == "Staff Entry":

    st.title("Staff Entry Panel")

    guest_name = st.text_input("Guest Name")
    mobile = st.text_input("Mobile Number")
    guest_count = st.number_input("Number of Guests", min_value=1, step=1)

    order_source = st.selectbox(
        "Order Source",
        ["Zomato", "Swiggy", "Easy Dinner", "Party"]
    )

    if st.button("Save Entry"):

        entry = {
            "Date": datetime.datetime.now(),
            "Guest Name": guest_name,
            "Mobile": mobile,
            "Guest Count": guest_count,
            "Order Source": order_source,
            "Rating": None,
            "Suggestion": None
        }

        st.session_state.data.append(entry)

        feedback_link = f"https://your-app-link.streamlit.app/?mobile={mobile}"

        whatsapp_link = f"https://wa.me/91{mobile}?text=Thank you for visiting! Please give your feedback here: {feedback_link}"

        st.success("Entry Saved!")
        st.markdown(f"[Send Feedback on WhatsApp]({whatsapp_link})")

# ===================================================
# ================= FEEDBACK FORM ===================
# ===================================================

elif menu == "Feedback Form":

    st.title("Guest Feedback")

    mobile_search = st.text_input("Enter Mobile Number")

    found = None
    for item in st.session_state.data:
        if item["Mobile"] == mobile_search:
            found = item
            break

    if found:

        rating = st.slider("Rate Your Experience ⭐", 1, 5)
        suggestion = st.text_area("Any Suggestions?")

        if st.button("Submit Feedback"):
            found["Rating"] = rating
            found["Suggestion"] = suggestion
            st.success("Thank You For Your Feedback!")

    else:
        if mobile_search != "":
            st.warning("No record found")

# ===================================================
# ================= DASHBOARD =======================
# ===================================================

elif menu == "Dashboard":

    st.title("Admin Dashboard")

    if len(st.session_state.data) == 0:
        st.info("No data available.")
    else:

        df = pd.DataFrame(st.session_state.data)

        total_entries = len(df)
        total_guests = df["Guest Count"].sum()
        avg_rating = df["Rating"].dropna().mean()

        if pd.isna(avg_rating):
            avg_rating = 0

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Entries", total_entries)
        col2.metric("Total Guests", total_guests)
        col3.metric("Avg Rating", round(avg_rating, 2))

        low_ratings = df[df["Rating"] <= 2]

        if not low_ratings.empty:
            st.error("Low Rating Alert! Immediate Attention Required!")

        st.dataframe(df)

        st.subheader("Order Source Analysis")
        st.bar_chart(df["Order Source"].value_counts())
