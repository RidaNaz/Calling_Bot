import streamlit as st
import requests
from datetime import datetime

# FastAPI backend URL
BACKEND_URL = "http://localhost:8000/api/v1/voice/schedule"

st.title("📅 Appointment Scheduler")

# User Input Form
with st.form("appointment_form"):
    name = st.text_input("Name")
    phone_number = st.text_input("Phone Number")
    email = st.text_input("Email")
    appointment_date = st.date_input("Appointment Date", datetime.now())
    appointment_time = st.time_input("Appointment Time", datetime.now().time())
    submit_button = st.form_submit_button("Schedule Appointment")

if submit_button:
    if name and email:
        # Combine date and time into ISO format
        appointment_datetime = datetime.combine(appointment_date, appointment_time).isoformat()

        # Prepare data for FastAPI
        data = {
            "name": name,
            "email": email,
            "phone_number": phone_number,
            "appointment_time": appointment_datetime
        }

        try:
            # Send POST request to FastAPI
            response = requests.post(BACKEND_URL, json=data)
            if response.status_code == 200:
                result = response.json()
                st.success("✅ Appointment Scheduled Successfully!")
                st.markdown(f"**[View Appointment Here]({result['link']})**", unsafe_allow_html=True)
            else:
                st.error("❌ Failed to schedule appointment. Please try again.")
        except Exception as e:
            st.error(f"🚨 Error: {e}")
    else:
        st.warning("⚠️ Please fill in all the fields.")