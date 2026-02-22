import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Restaurant CRM", layout="wide")

# ---------- Custom CSS ----------
st.markdown("""
<style>
body {
    background-color: #0E1117;
}
.big-title {
    font-size:30px;
    font-weight:bold;
    color:white;
}
.card {
    padding:20px;
    border-radius:15px;
    background-color:#1c1f26;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
}
</style>
""", unsafe_allow_html=True)

# ---------- Database ----------
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(
        columns=["Name","Mobile","Category","Time","Behaviour","Food","Service","Quality","Comment"]
    )

# ---------- Sidebar ----------
menu = st.sidebar.radio("Menu", ["Staff Entry","Feedback Form","Dashboard"])

# =====================================================
# 1️⃣ STAFF ENTRY
# =====================================================
if menu == "Staff Entry":

    st.markdown("<div class='big-title'>Staff Entry Panel</div>", unsafe_allow_html=True)

    name = st.text_input("Guest Name")
    mobile = st.text_input("Mobile Number")

    category = st.selectbox(
        "Order Source",
        ["Zomato", "Swiggy", "Easy Dinner", "Walk-In", "Party"]
    )

    if st.button("Save Entry"):

        if name and mobile:
            new_row = {
                "Name": name,
                "Mobile": mobile,
                "Category": category,
                "Time": datetime.datetime.now(),
                "Behaviour": "",
                "Food": "",
                "Service": "",
                "Quality": "",
                "Comment": ""
            }

            st.session_state.data = pd.concat(
                [st.session_state.data, pd.DataFrame([new_row])],
                ignore_index=True
            )

            st.success("Entry Saved Successfully ✅")
            st.balloons()

            feedback_link = f"http://localhost:8501/?mobile={mobile}&feedback=1"

            whatsapp_url = f"https://wa.me/91{mobile}?text=Thank%20you%20for%20visiting%20us!%20Please%20share%20your%20feedback:%20{feedback_link}"

            st.markdown(f"### 📲 Send Feedback")
            st.markdown(f"[Click Here to Send WhatsApp]({whatsapp_url})")

        else:
            st.error("Please fill all fields")

# =====================================================
# 2️⃣ FEEDBACK FORM
# =====================================================
elif menu == "Feedback Form":

    st.markdown("<div class='big-title'>Guest Feedback</div>", unsafe_allow_html=True)

    mobile = st.text_input("Enter Your Mobile Number")

    if mobile:

        if mobile in st.session_state.data["Mobile"].values:

            st.subheader("Rate Us ⭐")

            behaviour = st.slider("Behaviour",1,5)
            food = st.slider("Food",1,5)
            service = st.slider("Service",1,5)
            quality = st.slider("Quality",1,5)
            comment = st.text_area("Additional Comments")

            if st.button("Submit Feedback"):

                index = st.session_state.data[
                    st.session_state.data["Mobile"] == mobile
                ].index[0]

                st.session_state.data.at[index,"Behaviour"] = behaviour
                st.session_state.data.at[index,"Food"] = food
                st.session_state.data.at[index,"Service"] = service
                st.session_state.data.at[index,"Quality"] = quality
                st.session_state.data.at[index,"Comment"] = comment

                st.success("Thank you for your feedback ❤️")

        else:
            st.warning("Mobile number not found")

# =====================================================
# 3️⃣ DASHBOARD
# =====================================================
elif menu == "Dashboard":

    st.markdown("<div class='big-title'>Business Dashboard</div>", unsafe_allow_html=True)

    df = st.session_state.data

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Guests", len(df))
    col2.metric("Zomato Orders", len(df[df["Category"]=="Zomato"]))
    col3.metric("Swiggy Orders", len(df[df["Category"]=="Swiggy"]))

    st.dataframe(df)
