import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import urllib.parse as urlparse

# Connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

sheet = client.open("Hackathon_Votes").sheet1

# Parse user token from URL
query_params = st.experimental_get_query_params()
user_id = query_params.get("user", ["anonymous"])[0]

st.title("🛒 Marketplace Initiatives Voting")
st.markdown(f"Welcome, **{user_id}**! Please cast your vote below. ✅ One vote per user.")

initiatives = [
    "AI-powered Category Guard",
    "Seller Review Analytics Dashboard",
    "AdTech Self-Service Funding",
    "Marketplace Shops Expansion",
    "Offer Import Service Optimization"
]

vote = st.radio("Select your favorite initiative:", initiatives)

if st.button("Submit Vote"):
    # Check if user has already voted
    all_votes = sheet.col_values(1)
    if user_id in all_votes:
        st.warning("⚠️ You have already voted!")
    else:
        sheet.append_row([user_id, vote])
        st.success(f"✅ Thanks for voting for: **{vote}**")

# Show live results
st.subheader("📊 Live Results")
votes = sheet.get_all_records()
if votes:
    import pandas as pd
    import matplotlib.pyplot as plt

    df = pd.DataFrame(votes)
    results = df["vote"].value_counts()

    st.bar_chart(results)


