import streamlit as st
import pandas as pd
import os
import hashlib
import datetime
import io

st.set_page_config(page_title="CARNIVLE CRM", layout="wide")

DATA_FILE = "guest_data.csv"
FEEDBACK_FILE = "feedback_data.csv"

# ================== FEEDBACK DIRECT PAGE ==================
query_params = st.query_params

if "feedback" in query_params:

    guest_mobile = query_params["feedback"]

    st.markdown("""
        <h1 style='text-align:center;color:#E63946;'>
        🍽 CARNIVLE
        </h1>
        <h3 style='text-align:center;'>
        We Value Your Experience
        </h3>
        <hr>
    """, unsafe_allow_html=True)

    if os.path.exists(FEEDBACK_FILE):
        feedback_df = pd.read_csv(FEEDBACK_FILE)
    else:
        feedback_df = pd.DataFrame(columns=[
            "guest_mobile","overall","staff",
            "food","service","comment","date"
        ])

    # Prevent duplicate feedback
    if guest_mobile in feedback_df["guest_mobile"].values:
        st.success("✅ Feedback already submitted. Thank You ❤️")
        st.stop()

    st.subheader("⭐ Overall Experience")
    overall = st.slider("",1,5,4)

    col1,col2 = st.columns(2)

    with col1:
        st.subheader("👨‍🍳 Staff Behaviour")
        staff = st.slider(" ",1,5,4)

        st.subheader("🍽 Food Quality")
        food = st.slider("  ",1,5,4)

    with col2:
        st.subheader("🛎 Service Quality")
        service = st.slider("   ",1,5,4)

    comment = st.text_area("💬 Additional Comments")

    if st.button("Submit Feedback"):

        new_feedback = {
            "guest_mobile": guest_mobile,
            "overall": overall,
            "staff": staff,
            "food": food,
            "service": service,
            "comment": comment,
            "date": datetime.date.today()
        }

        feedback_df = pd.concat(
            [feedback_df, pd.DataFrame([new_feedback])]
        )

        feedback_df.to_csv(FEEDBACK_FILE, index=False)

        st.markdown("""
            <h2 style='text-align:center;color:green;'>
            🎉 Thank You For Visiting CARNIVLE!
            </h2>
        """, unsafe_allow_html=True)

        st.balloons()
        st.snow()
        st.stop()

    st.stop()

# ================= LOGIN SYSTEM =================
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "staff1": {"password": "staff123", "role": "staff"},
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.markdown("""
        <h1 style='text-align:center;color:#E63946;'>
        🍽 CARNIVLE
        </h1>
        <h3 style='text-align:center;'>CRM & Guest Management System</h3>
        <hr>
    """, unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and password == users[username]["password"]:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = users[username]["role"]
            st.rerun()
        else:
            st.error("Invalid Login")

    st.stop()

# ================= LOAD DATA =================
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "id","name","mobile","category",
        "pax","date","created_by","edit_count"
    ])

if os.path.exists(FEEDBACK_FILE):
    feedback_df = pd.read_csv(FEEDBACK_FILE)
else:
    feedback_df = pd.DataFrame(columns=[
        "guest_mobile","overall","staff",
        "food","service","comment","date"
    ])

# ================= SIDEBAR =================
st.sidebar.title("🍽 CARNIVLE CRM")

menu = st.sidebar.radio(
    "Navigation",
    ["Guest Entry","Dashboard","Admin Panel"]
)

st.sidebar.write(f"Logged in as: {st.session_state.username}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ==========================================================
# ================= GUEST ENTRY ============================
# ==========================================================
if menu == "Guest Entry":

    st.title("📝 Guest Entry")

    name = st.text_input("Guest Name")
    mobile = st.text_input("Mobile Number")

    category = st.selectbox("Category",[
        "Walk-In","Swiggy","Zomato","EasyDiner","Party"
    ])

    pax = st.number_input("Number of PAX", min_value=1, step=1)

    date = st.date_input("Visit Date", datetime.date.today())

    if st.button("Submit Entry"):
        new_id = hashlib.md5(
            (name + mobile + str(datetime.datetime.now())).encode()
        ).hexdigest()[:8]

        new_data = {
            "id": new_id,
            "name": name,
            "mobile": mobile,
            "category": category,
            "pax": pax,
            "date": date,
            "created_by": st.session_state.username,
            "edit_count": 0
        }

        df = pd.concat([df, pd.DataFrame([new_data])])
        df.to_csv(DATA_FILE,index=False)

        st.success("Guest Added Successfully")

        feedback_link = f"https://rjraunakapp.streamlit.app/?feedback={mobile}"
        whatsapp_url = f"https://wa.me/{mobile}?text=Thank you for visiting CARNIVLE. Please share feedback: {feedback_link}"

        st.markdown(f"[📲 Send Feedback Link]({whatsapp_url})")

    # Staff Edit (1 time)
    st.subheader("Edit Guest (Only 1 Time)")

    edit_id = st.text_input("Enter Guest ID")

    if edit_id in df["id"].values:
        row = df.index[df["id"]==edit_id][0]

        if df.at[row,"edit_count"] >= 1:
            st.error("Edit limit reached")
        else:
            new_name = st.text_input("New Name", df.at[row,"name"])
            new_mobile = st.text_input("New Mobile", df.at[row,"mobile"])

            if st.button("Update Guest"):
                df.at[row,"name"] = new_name
                df.at[row,"mobile"] = new_mobile
                df.at[row,"edit_count"] += 1
                df.to_csv(DATA_FILE,index=False)
                st.success("Updated Successfully")

    # Staff Excel
    staff_data = df[df["created_by"]==st.session_state.username]

    buffer = io.BytesIO()
    staff_data.to_excel(buffer,index=False)
    buffer.seek(0)

    st.download_button(
        "Download My Excel",
        data=buffer,
        file_name="my_entries.xlsx",
        mime="application/vnd.ms-excel"
    )

# ==========================================================
# ================= DASHBOARD ==============================
# ==========================================================
elif menu == "Dashboard":

    st.title("📊 CARNIVLE Dashboard")

    today = str(datetime.date.today())
    today_df = df[df["date"]==today]

    col1,col2,col3 = st.columns(3)
    col1.metric("Total Guests", len(df))
    col2.metric("Today Guests", len(today_df))
    col3.metric("Total PAX", df["pax"].sum())

    filter_cat = st.selectbox(
        "Filter by Category",
        ["All"] + list(df["category"].unique())
    )

    if filter_cat != "All":
        show_df = df[df["category"]==filter_cat]
    else:
        show_df = df

    st.dataframe(show_df)

# ==========================================================
# ================= ADMIN PANEL ============================
# ==========================================================
elif menu == "Admin Panel":

    if st.session_state.role != "admin":
        st.error("Admin Access Only")
        st.stop()

    st.title("🛠 CARNIVLE Admin Panel")

    st.subheader("All Guest Data")
    st.dataframe(df)

    buffer = io.BytesIO()
    df.to_excel(buffer,index=False)
    buffer.seek(0)

    st.download_button(
        "Download Full Excel",
        data=buffer,
        file_name="all_guest_data.xlsx",
        mime="application/vnd.ms-excel"
    )

    st.subheader("Feedback Data")
    st.dataframe(feedback_df)

    if not feedback_df.empty:
        st.subheader("📊 Feedback Analytics")

        col1,col2,col3,col4 = st.columns(4)
        col1.metric("Overall Avg", round(feedback_df["overall"].mean(),2))
        col2.metric("Staff Avg", round(feedback_df["staff"].mean(),2))
        col3.metric("Food Avg", round(feedback_df["food"].mean(),2))
        col4.metric("Service Avg", round(feedback_df["service"].mean(),2))
