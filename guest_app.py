import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Title + Name Side me
col1, col2 = st.columns([4,1])

with col1:
    st.title("Guest Entry System")

with col2:
    st.write("App by RJ_RANAK")


file_name = "guest_data.xlsx"


# File create if not exist
if not os.path.exists(file_name):

    df = pd.DataFrame(columns=[
    "Date",
    "Guest Name",
    "Mobile",
    "Category",
    "Guest Count",
    "Repeat Customer"
    ])

    df.to_excel(file_name,index=False)


df = pd.read_excel(file_name)



st.header("Add Guest")


name = st.text_input("Guest Name")

mobile = st.text_input("Mobile Number")


category = st.selectbox("Category",[
"Swiggy",
"Zomato",
"Walkin",
"EazyDiner",
"Party"
])


guest_count = st.number_input(
"Number of Guest",
min_value=1,
step=1
)


repeat = st.selectbox(
"Repeat Customer",
["No","Yes"]
)



if st.button("Add Guest"):

    new_row = pd.DataFrame([{

    "Date":datetime.now().strftime("%d-%m-%Y"),

    "Guest Name":name,

    "Mobile":mobile,

    "Category":category,

    "Guest Count":guest_count,

    "Repeat Customer":repeat

    }])


    df = pd.concat([df,new_row],ignore_index=True)

    df.to_excel(file_name,index=False)

    st.success("Guest Added Successfully")



st.header("Guest List")

st.dataframe(df)



st.header("Report")


total_guest = df["Guest Count"].sum()

swiggy = df[df["Category"]=="Swiggy"]["Guest Count"].sum()

zomato = df[df["Category"]=="Zomato"]["Guest Count"].sum()

repeat_count = df[df["Repeat Customer"]=="Yes"]["Guest Count"].sum()



st.write("Total Guest =",total_guest)

st.write("Swiggy Guest =",swiggy)

st.write("Zomato Guest =",zomato)

st.write("Repeat Customer Guest =",repeat_count)



# Excel Download

with open(file_name,"rb") as file:

    st.download_button(

    "Download Excel",

    file,

    "guest_data.xlsx"

    )