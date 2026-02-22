import streamlit as st
import sqlite3
import pandas as pd
import datetime

st.set_page_config(page_title="Carnivale Enterprise CRM", layout="wide")

# ================= CONFIG =================
BASE_URL = "https://YOUR-APP-NAME.streamlit.app"

# ================= DATABASE =================
conn = sqlite3.connect("enterprise.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS admins(
username TEXT PRIMARY KEY,
password TEXT)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS staff(
username TEXT PRIMARY KEY,
password TEXT,
branch TEXT,
can_export INTEGER,
can_edit INTEGER)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS guests(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
mobile TEXT,
category TEXT,
pax INTEGER,
branch TEXT,
staff TEXT,
date TEXT)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS feedback(
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
date TEXT)
""")

conn.commit()

# Default admin
if not c.execute("SELECT * FROM admins").fetchone():
    c.execute("INSERT INTO admins VALUES (?,?)", ("admin","admin123"))
    conn.commit()

# ================= LOGIN =================
if "role" not in st.session_state:
    st.session_state.role=None

if st.session_state.role is None:
    st.title("🔐 Login")

    role = st.selectbox("Login As", ["Admin","Staff"])
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")

    if st.button("Login"):
        if role=="Admin":
            data=c.execute("SELECT * FROM admins WHERE username=? AND password=?",(user,pw)).fetchone()
            if data:
                st.session_state.role="admin"
                st.session_state.user=user
                st.rerun()

        if role=="Staff":
            data=c.execute("SELECT * FROM staff WHERE username=? AND password=?",(user,pw)).fetchone()
            if data:
                st.session_state.role="staff"
                st.session_state.user=user
                st.session_state.branch=data[2]
                st.session_state.can_export=data[3]
                st.session_state.can_edit=data[4]
                st.rerun()

    st.stop()

# Logout
if st.sidebar.button("Logout"):
    st.session_state.role=None
    st.rerun()

# ================= ADMIN =================
if st.session_state.role=="admin":

    st.title("👑 Admin Dashboard")

    tab1,tab2,tab3 = st.tabs(["Create Staff","Analytics","All Feedback"])

    with tab1:
        st.subheader("Add Staff")
        u=st.text_input("Username")
        p=st.text_input("Password")
        b=st.text_input("Branch")
        export=st.checkbox("Allow Export")
        edit=st.checkbox("Allow Edit")

        if st.button("Create Staff"):
            c.execute("INSERT INTO staff VALUES (?,?,?,?,?)",
                      (u,p,b,int(export),int(edit)))
            conn.commit()
            st.success("Staff Created")

    with tab2:
        df=pd.read_sql_query("SELECT * FROM guests",conn)
        fb=pd.read_sql_query("SELECT * FROM feedback",conn)

        if not df.empty:
            st.metric("Total Guests",len(df))

            repeat=df["mobile"].value_counts()
            repeat=repeat[repeat>1]
            st.metric("Repeat Guests",len(repeat))

        if not fb.empty:
            st.metric("Average Rating",round(fb["overall"].mean(),2))

            low=fb[fb["overall"]<=2]
            if not low.empty:
                st.error("⚠ Low Rating Alert")

            st.subheader("Monthly Rating")
            fb["month"]=pd.to_datetime(fb["date"]).dt.to_period("M")
            st.bar_chart(fb.groupby("month")["overall"].mean())

    with tab3:
        fb=pd.read_sql_query("SELECT * FROM feedback",conn)
        if not fb.empty:
            st.dataframe(fb)

# ================= STAFF =================
if st.session_state.role=="staff":

    st.title("👨‍💼 Staff Panel")

    date_input=st.date_input("Select Date", datetime.date.today())

    with st.form("guest_form", clear_on_submit=True):

        name=st.text_input("Guest Name")
        mobile=st.text_input("Mobile Number")
        category=st.selectbox("Category",
            ["Walk In","Zomato","Swiggy","EazyDiner","Party","VIP"])
        pax=st.number_input("Number of Guests",1)

        submit=st.form_submit_button("Add Guest")

        if submit:
            c.execute("""
            INSERT INTO guests (name,mobile,category,pax,branch,staff,date)
            VALUES (?,?,?,?,?,?,?)
            """,(name,mobile,category,pax,
                 st.session_state.branch,
                 st.session_state.user,
                 str(date_input)))
            conn.commit()

            link=f"{BASE_URL}?feedback={mobile}&branch={st.session_state.branch}"
            whatsapp=f"https://wa.me/{mobile}?text=Thank you for visiting Carnivale ❤️ Please give feedback {link}"

            st.success("Guest Added")
            st.markdown(f"[📲 Send WhatsApp Feedback]({whatsapp})")

    staff_data=pd.read_sql_query(
        "SELECT * FROM guests WHERE staff=? AND date=?",
        conn,
        params=(st.session_state.user,str(date_input))
    )

    if not staff_data.empty:
        st.subheader("Today's Entries")
        st.dataframe(staff_data)

        if st.session_state.can_export:
            csv=staff_data.to_csv(index=False).encode()
            st.download_button("Download Excel",csv,"staff_data.csv")

# ================= FEEDBACK PAGE =================
params=st.query_params

if "feedback" in params:

    mobile=params["feedback"]
    branch=params.get("branch","Main")

    st.title("🍽 Carnivale Feedback")

    guest=pd.read_sql_query(
        "SELECT name FROM guests WHERE mobile=? ORDER BY id DESC LIMIT 1",
        conn,params=(mobile,)
    )

    guest_name=guest.iloc[0]["name"] if not guest.empty else ""

    st.write("Guest:",guest_name)

    def stars(label):
        return st.radio(label,
                        ["⭐","⭐⭐","⭐⭐⭐","⭐⭐⭐⭐","⭐⭐⭐⭐⭐"],
                        horizontal=True)

    with st.form("feedback_form"):
        food=stars("Food")
        service=stars("Service")
        behaviour=stars("Behaviour")
        cleanliness=stars("Cleanliness")
        ambience=stars("Ambience")

        nps=st.slider("Recommend us? (0-10)",0,10,8)
        comment=st.text_area("Comment")

        submit=st.form_submit_button("Submit")

        if submit:

            def convert(s): return s.count("⭐")

            food_i=convert(food)
            service_i=convert(service)
            behaviour_i=convert(behaviour)
            cleanliness_i=convert(cleanliness)
            ambience_i=convert(ambience)

            overall=round((food_i+service_i+behaviour_i+cleanliness_i+ambience_i)/5)

            c.execute("""
            INSERT INTO feedback
            (guest_name,mobile,branch,
             food,service,behaviour,
             cleanliness,ambience,
             overall,nps,comment,date)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (guest_name,mobile,branch,
             food_i,service_i,behaviour_i,
             cleanliness_i,ambience_i,
             overall,nps,comment,
             str(datetime.date.today())))
            conn.commit()

            if overall<=2:
                st.error("⚠ We are sorry! Management will contact you.")
            else:
                st.success("Thank You ❤️")
                st.balloons()

    st.stop()
