import streamlit as st

# App title
st.title("🛒 Voting App(Developed by Marketplace Team using Streamlit)")

st.markdown("Please vote for the best initiative from this Hackathon. ✅ One vote per user.")

# Initiatives list
initiatives = [
    "Marketplace",
    "Customer",
    "Customer Experience",
    "LastMile",
    "OMS",
    "Search",
    "PIM/Catalogue/Promotions"
]

# Radio button for selection
vote = st.radio("Select your favorite initiative:", initiatives)

# Store votes in session (for demo)
if "voted" not in st.session_state:
    st.session_state.voted = False

if st.button("Submit Vote"):
    if st.session_state.voted:
        st.warning("⚠️ You have already voted! One vote per user.")
    else:
        st.session_state.voted = True
        st.success(f"✅ Thanks for voting for: **{vote}**")

st.markdown("---")
st.info("Results will be consolidated by the organizing team.")

