import streamlit as st
import pandas as pd
import os
import hashlib
import datetime
import io

st.set_page_config(page_title="Enterprise CRM", layout="wide")

DATA_FILE = "guest_data.csv"

# ---------- LOGIN SYSTEM ----------
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "staff1": {"password": "staff123", "role": "staff"},
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Secure Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and password == users[username]["password"]:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = users[username]["role"]
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

# ---------- LOAD DATA ----------
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "id", "name", "mobile", "category",
        "date", "created_by", "edit_count"
    ])

# ---------- SIDEBAR ----------
st.sidebar.title("CRM Panel")
menu = st.sidebar.radio("Navigation",
    ["Guest Entry", "Dashboard", "Admin Panel"]
)

st.sidebar.write(f"Logged in as: {st.session_state.username}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ==========================================================
# ===================== GUEST ENTRY ========================
# ==========================================================
if menu == "Guest Entry":

    st.title("📝 Guest Entry")

    name = st.text_input("Guest Name")
    mobile = st.text_input("Mobile Number")
    category = st.selectbox("Category",
        ["Regular", "VIP", "Corporate", "Other"]
    )
    date = st.date_input("Visit Date", datetime.date.today())

    if st.button("Submit Entry"):
        if name and mobile:
            new_data = {
                "id": hashlib.md5(
                    (name + mobile + str(datetime.datetime.now())).encode()
                ).hexdigest()[:8],
                "name": name,
                "mobile": mobile,
                "category": category,
                "date": date,
                "created_by": st.session_state.username,
                "edit_count": 0
            }

            df = pd.concat([df, pd.DataFrame([new_data])])
            df.to_csv(DATA_FILE, index=False)
            st.success("Guest Added Successfully")

            # WhatsApp Link
            feedback_link = f"https://rjraunakapp.streamlit.app/?feedback={mobile}"
            whatsapp_url = f"https://wa.me/{mobile}?text=Please%20give%20your%20feedback:%20{feedback_link}"
            st.markdown(f"[📲 Send Feedback WhatsApp]({whatsapp_url})")

        else:
            st.error("Fill all fields")

# ==========================================================
# ===================== DASHBOARD ==========================
# ==========================================================
elif menu == "Dashboard":

    st.title("📊 Dashboard")

    today = str(datetime.date.today())
    today_data = df[df["date"] == today]

    col1, col2 = st.columns(2)
    col1.metric("Total Guests", len(df))
    col2.metric("Today Guests", len(today_data))

    category_filter = st.selectbox(
        "Filter by Category",
        ["All"] + list(df["category"].unique())
    )

    if category_filter != "All":
        filtered = df[df["category"] == category_filter]
    else:
        filtered = df

    st.dataframe(filtered)

# ==========================================================
# ===================== ADMIN PANEL ========================
# ==========================================================
elif menu == "Admin Panel":

    if st.session_state.role != "admin":
        st.error("Access Denied")
        st.stop()

    st.title("🛠 Admin Panel")

    st.dataframe(df)

    # Excel Export
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        label="📥 Download Full Excel",
        data=buffer,
        file_name="all_guest_data.xlsx",
        mime="application/vnd.ms-excel"
    )

    # Edit System
    st.subheader("Edit Guest (Admin Only)")

    edit_id = st.text_input("Enter Guest ID to Edit")

    if edit_id in df["id"].values:
        row_index = df.index[df["id"] == edit_id][0]

        new_name = st.text_input("New Name", df.at[row_index, "name"])
        new_mobile = st.text_input("New Mobile", df.at[row_index, "mobile"])
        new_date = st.date_input("New Date",
            pd.to_datetime(df.at[row_index, "date"])
        )

        if st.button("Update"):
            df.at[row_index, "name"] = new_name
            df.at[row_index, "mobile"] = new_mobile
            df.at[row_index, "date"] = new_date
            df.to_csv(DATA_FILE, index=False)
            st.success("Updated Successfully")
