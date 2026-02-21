import streamlit as st
import pandas as pd
import os
from datetime import datetime, date

# ------------------ LOGIN CONFIG ------------------ #

USER_CREDENTIALS = {
    "admin": "1234",
    "ranak": "guest123"
}

# ------------------ SESSION ------------------ #

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ------------------ LOGIN PAGE ------------------ #

def login():
    st.title("Login - Guest Entry System")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.logged_in = True
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid Username or Password")

# ------------------ MAIN APP ------------------ #

def main_app():

    col1, col2 = st.columns([4,1])

    with col1:
        st.title("Guest Entry System")

    with col2:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    file_name = "guest_data.xlsx"

    # Create file if not exist
    if not os.path.exists(file_name):
        df = pd.DataFrame(columns=[
            "Date",
            "Guest Name",
            "Mobile",
            "Category",
            "Guest Count",
            "Repeat Customer"
        ])
        df.to_excel(file_name, index=False)

    df = pd.read_excel(file_name)

    # ------------------ ADD GUEST ------------------ #

    st.header("Add Guest")

    entry_date = st.date_input("Select Date", date.today())
    name = st.text_input("Guest Name")
    mobile = st.text_input("Mobile Number")

    category = st.selectbox("Category", [
        "Swiggy",
        "Zomato",
        "Walkin",
        "EazyDiner",
        "Party"
    ])

    guest_count = st.number_input("Number of Guest", min_value=1, step=1)

    repeat = st.selectbox("Repeat Customer", ["No", "Yes"])

    if st.button("Add Guest"):
        if name == "" or mobile == "":
            st.warning("Please fill all details")
        else:
            new_row = pd.DataFrame([{
                "Date": entry_date,
                "Guest Name": name,
                "Mobile": mobile,
                "Category": category,
                "Guest Count": guest_count,
                "Repeat Customer": repeat
            }])

            df = pd.concat([df, new_row], ignore_index=True)
            df.to_excel(file_name, index=False)
            st.success("Guest Added Successfully")

    # ------------------ VIEW DATA ------------------ #

    st.header("View Date Wise Data")

    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        selected_date = st.date_input("Select Date to View", date.today())
        filtered_df = df[df["Date"] == selected_date]
        st.dataframe(filtered_df)

        # ------------------ REPORT ------------------ #

        st.header("Report (Selected Date)")

        total_guest = filtered_df["Guest Count"].sum()
        swiggy = filtered_df[filtered_df["Category"] == "Swiggy"]["Guest Count"].sum()
        zomato = filtered_df[filtered_df["Category"] == "Zomato"]["Guest Count"].sum()
        repeat_count = filtered_df[filtered_df["Repeat Customer"] == "Yes"]["Guest Count"].sum()

        st.write("Total Guest =", total_guest)
        st.write("Swiggy Guest =", swiggy)
        st.write("Zomato Guest =", zomato)
        st.write("Repeat Customer Guest =", repeat_count)

    # ------------------ DOWNLOAD ------------------ #

    st.header("Download Data")

    with open(file_name, "rb") as file:
        st.download_button("Download Excel", file, "guest_data.xlsx")

# ------------------ APP FLOW ------------------ #

if st.session_state.logged_in:
    main_app()
else:
    login()
