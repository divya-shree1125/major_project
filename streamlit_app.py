import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import pandas as pd
import datetime
import os

# Google Fit API Scopes
SCOPES = ["https://www.googleapis.com/auth/fitness.activity.read"]

# Initialize session state for authentication
if "credentials" not in st.session_state:
    st.session_state.credentials = None

# Title
st.title("Google Fit Fitness Tracker")

# Sidebar
menu = st.sidebar.selectbox("Menu", ["Authenticate", "View Fitness Data"])

# Authenticate with Google Fit API
if menu == "Authenticate":
    st.header("Authenticate with Google")
    if not st.session_state.credentials:
        st.write("Click the button below to authenticate with Google Fit API.")

        if st.button("Authenticate"):
            # OAuth flow
            flow = Flow.from_client_secrets_file(
                "client_secrets.json",  # Your Google client secrets file
                scopes=SCOPES,
                redirect_uri="http://localhost:8501"
            )
            auth_url, _ = flow.authorization_url(prompt="consent")
            st.write("Please open the link below in a new tab to authorize access:")
            st.write(auth_url)

            # Enter authorization code
            code = st.text_input("Enter the authorization code:")
            if code:
                flow.fetch_token(code=code)
                st.session_state.credentials = flow.credentials
                st.success("Authentication successful!")

# Fetch and display fitness data
if menu == "View Fitness Data":
    st.header("Your Fitness Data")

    if not st.session_state.credentials:
        st.warning("Please authenticate first!")
    else:
        # Build Google Fit API client
        service = build("fitness", "v1", credentials=st.session_state.credentials)

        # Query fitness data
        now = datetime.datetime.utcnow().isoformat() + "Z"  # Current time in ISO 8601
        yesterday = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).isoformat() + "Z"

        # Aggregate request body
        body = {
            "aggregateBy": [
                {"dataTypeName": "com.google.step_count.delta"}
            ],
            "bucketByTime": {"durationMillis": 86400000},  # Daily buckets
            "startTimeMillis": int((datetime.datetime.utcnow() - datetime.timedelta(days=7)).timestamp() * 1000),
            "endTimeMillis": int(datetime.datetime.utcnow().timestamp() * 1000),
        }

        # Request aggregated data
        response = service.users().dataset().aggregate(userId="me", body=body).execute()

        # Process and display data
        steps_data = []
        for bucket in response.get("bucket", []):
            start_time = datetime.datetime.fromtimestamp(int(bucket["startTimeMillis"]) / 1000)
            end_time = datetime.datetime.fromtimestamp(int(bucket["endTimeMillis"]) / 1000)
            steps = 0
            for dataset in bucket.get("dataset", []):
                for point in dataset.get("point", []):
                    steps += point.get("value", [])[0].get("intVal", 0)
            steps_data.append({"Date": start_time.date(), "Steps": steps})

        # Create DataFrame
        df = pd.DataFrame(steps_data)

        # Display data
        st.subheader("Steps Count (Last 7 Days)")
        if df.empty:
            st.write("No data available.")
        else:
            st.line_chart(df.set_index("Date"))
            st.dataframe(df)