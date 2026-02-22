import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Restaurant Intelligence CRM", layout="wide")

# ---------- SESSION STORAGE ----------
if "data" not in st.session_state:
    st.session_state.data = []

# ---------- SIDEBAR ----------
st.sidebar.title("Menu")
menu = st.sidebar.radio("", ["Staff Entry", "Feedback Form", "Dashboard"])

# =========================================================
# ================== STAFF ENTRY ==========================
# =========================================================

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
        st.success("✅ Entry Saved Successfully!")

# =========================================================
# ================== FEEDBACK FORM ========================
# =========================================================

elif menu == "Feedback Form":

    st.title("Guest Feedback Form")

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
            st.success("🎉 Thank you for your feedback!")

    else:
        if mobile_search != "":
            st.warning("No entry found for this number.")

# =========================================================
# ================== DASHBOARD ============================
# =========================================================

elif menu == "Dashboard":

    st.title("Admin Dashboard")

    if len(st.session_state.data) == 0:
        st.info("No data available yet.")
    else:

        df = pd.DataFrame(st.session_state.data)

        total_guests = df["Guest Count"].sum()
        total_entries = len(df)

        avg_rating = df["Rating"].dropna().mean()
        if pd.isna(avg_rating):
            avg_rating = 0

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Entries", total_entries)
        col2.metric("Total Guests Served", total_guests)
        col3.metric("Average Rating ⭐", round(avg_rating, 2))

        # Low Rating Alert
        low_ratings = df[df["Rating"] <= 2]

        if not low_ratings.empty:
            st.error("⚠ Low Rating Alert! Immediate Action Required")

        st.subheader("All Entries")
        st.dataframe(df)

        # Order Source Analysis
        st.subheader("Order Source Distribution")
        source_count = df["Order Source"].value_counts()
        st.bar_chart(source_count)
