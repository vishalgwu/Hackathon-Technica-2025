import streamlit as st

st.set_page_config(page_title="Hackathon App", page_icon="⚡")

st.title("🚀 Hackathon Technica – Phase 0")

uploaded_file = st.file_uploader(
    "Upload a PDF or Image",
    type=["pdf", "png", "jpg", "jpeg"]
)

if uploaded_file:
    st.success(f"Received file: {uploaded_file.name}")
    st.write(f"Size: {len(uploaded_file.getvalue())} bytes")
else:
    st.info("Please upload a file to test Phase 0.")
