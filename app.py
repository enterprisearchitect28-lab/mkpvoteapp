import streamlit as st

st.title("Hackathon Voting App 🎉")

teams = ["MKP Shops", "Category Guard (AI)", "Seller Reviews Insights", "AdTech Self-Funding", "Offer Import Optimizer"]

vote = st.radio("Select your favorite project:", teams)

if st.button("Submit Vote"):
    st.success(f"✅ Thanks for voting for: {vote}")
