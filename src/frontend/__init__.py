import streamlit as st
import pandas as pd
import requests
import json

st.set_page_config(page_title="Finance AI Assistant", layout="wide")

BACKEND_URL = "http://127.0.0.1:8000"

st.title("💸 AI Finance Assistant (Hackathon 2025)")
st.write("Upload your statement and interact with different finance agents.")

# -----------------------------------------------------
# FILE UPLOAD
# -----------------------------------------------------
uploaded = st.file_uploader("Upload PDF / Image", type=["pdf", "png", "jpg", "jpeg"])

transactions_df = None

if uploaded:
    st.info("Processing… Please wait.")
    files = {"file": uploaded}

    try:
        resp = requests.post(f"{BACKEND_URL}/process", files=files)
    except Exception:
        st.error("Backend not reachable. Start uvicorn first.")
        st.stop()

    if resp.status_code == 200:
        parsed = resp.json()["transactions"]
        transactions_df = pd.DataFrame(parsed)
        st.success("File processed successfully!")

        with st.expander("📊 View Parsed Transactions"):
            st.dataframe(transactions_df)
    else:
        st.error("Processing failed. Check backend logs.")
        st.stop()


# -----------------------------------------------------
# AGENT TABS
# -----------------------------------------------------
if transactions_df is not None:

    tab1, tab2, tab3, tab4 = st.tabs([
        "🧾 Summary Agent",
        "💸 Tax Deduction Agent",
        "📈 Spending Patterns Agent",
        "⚖️ Compliance Agent"
    ])

    # Shared function for queries
    def ask_agent(question: str):
        res = requests.post(f"{BACKEND_URL}/query", json={"question": question})
        if res.status_code == 200:
            return res.json()
        return {"answer": "Backend error", "matches": []}

    # Helper to render answer + (optional) retrieved docs
    def render_answer(ans):
        st.markdown(ans["answer"])
        with st.expander("🔍 View retrieved receipts / context"):
            st.json(ans["matches"])

    # ----------------------
    # SUMMARY AGENT
    # ----------------------
    with tab1:
        st.subheader("🧾 Summary Agent")
        q = st.text_input("Ask a question:", key="summary_q")
        if q:
            ans = ask_agent(q)
            render_answer(ans)

    # ----------------------
    # TAX AGENT
    # ----------------------
    with tab2:
        st.subheader("💸 Tax Deduction Agent")
        q = st.text_input("Ask tax-related question:", key="tax_q")
        if q:
            ans = ask_agent(f"Tax analysis: {q}")
            render_answer(ans)

    # ----------------------
    # SPENDING PATTERNS AGENT + DASHBOARD
    # ----------------------
    with tab3:
        st.subheader("📈 Spending Patterns Agent")

        # ---------- Data prep for charts ----------
        spend_df = transactions_df.copy()

        # ensure numeric
        spend_df["total_amount"] = pd.to_numeric(spend_df["total_amount"], errors="coerce")

        # try to convert dates like "10/09" -> 2024-10-09 (fake year, just for plotting)
        if "date" in spend_df.columns:
            spend_df["date_str"] = spend_df["date"].astype(str)
            spend_df["date_parsed"] = pd.to_datetime(
                spend_df["date_str"] + "/2024",  # assume same year
                format="%m/%d/%Y",
                errors="coerce"
            )
        else:
            spend_df["date_parsed"] = pd.NaT

        # ---------- KPI row ----------
        total_spent = spend_df["total_amount"].sum()
        avg_spent = spend_df["total_amount"].mean()
        n_txn = len(spend_df)
        max_txn = spend_df["total_amount"].max()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Spent", f"${total_spent:,.2f}")
        c2.metric("Avg Transaction", f"${avg_spent:,.2f}")
        c3.metric("Number of Transactions", n_txn)
        c4.metric("Largest Transaction", f"${max_txn:,.2f}")

        st.markdown("---")

        # ---------- Chart 1: Spending over time ----------
        st.markdown("### 📆 Spending Over Time")

        time_df = spend_df.dropna(subset=["total_amount"])
        if time_df["date_parsed"].notna().any():
            time_df = time_df.dropna(subset=["date_parsed"]).sort_values("date_parsed")
            time_df = time_df[["date_parsed", "total_amount"]]
            time_df = time_df.set_index("date_parsed")
            st.line_chart(time_df["total_amount"])
        else:
            st.info("Date information not available in a parseable format.")

        # ---------- Chart 2: Top transactions ----------
        st.markdown("### 💳 Top 10 Transactions")

        top_df = spend_df.sort_values("total_amount", ascending=False).head(10)
        # use index as label (or could later add merchant parsing)
        top_df_display = top_df[["total_amount"]]
        st.bar_chart(top_df_display)

        st.markdown("---")

        # ---------- LLM question box ----------
        q = st.text_input("Ask spending-related question:", key="spend_q")
        if q:
            ans = ask_agent(f"Spending analysis: {q}")
            render_answer(ans)

    # ----------------------
    # COMPLIANCE AGENT
    # ----------------------
    with tab4:
        st.subheader("⚖️ Compliance Agent")
        q = st.text_input("Ask compliance question:", key="comp_q")
        if q:
            ans = ask_agent(f"Compliance check: {q}")
            render_answer(ans)
