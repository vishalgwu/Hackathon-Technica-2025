import streamlit as st
import pandas as pd
import requests
import json
import plotly.express as px

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

    # Shared function for LLM
    def ask_agent(question: str):
        res = requests.post(f"{BACKEND_URL}/query", json={"question": question})
        if res.status_code == 200:
            return res.json()
        return {"answer": "Backend error", "matches": []}

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
    # SPENDING PATTERNS AGENT — FULLY UPGRADED
    # ----------------------
    with tab3:
        st.subheader("📈 Spending Patterns Agent")

        spend_df = transactions_df.copy()
        spend_df["total_amount"] = pd.to_numeric(spend_df["total_amount"], errors="coerce")

        # ---------------- Extract Vendor Names ----------------
        def extract_vendor(row):
            try:
                items = row["items"]
                if isinstance(items, str):
                    items = json.loads(items)
                return items[0].get("description", "Unknown")[:40]
            except:
                return "Unknown"

        spend_df["vendor_name"] = spend_df.apply(extract_vendor, axis=1)

        # ---------------- Category Mapping ----------------
        CATEGORY_MAP = {
            "7-Eleven": "Convenience",
            "McDonald's": "Food",
            "Whole Foods": "Groceries",
            "Walmart": "Groceries",
            "Target": "Retail",
            "Uber": "Travel",
            "Lyft": "Travel",
            "Shell": "Gas",
            "Exxon": "Gas",
            "Grubhub": "Delivery",
            "Amazon": "Online Shopping"
        }

        def detect_category(vendor):
            for key, cat in CATEGORY_MAP.items():
                if key.lower() in vendor.lower():
                    return cat
            return "Other"

        spend_df["category"] = spend_df["vendor_name"].apply(detect_category)

        # ---------------- Fix Dates ----------------
        if "date" in spend_df.columns:
            spend_df["date_str"] = spend_df["date"].astype(str)
            spend_df["date_parsed"] = pd.to_datetime(
                spend_df["date_str"] + "/2024",
                format="%m/%d/%Y",
                errors="coerce"
            )
        else:
            spend_df["date_parsed"] = pd.NaT

        # ---------------- KPI Cards ----------------
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

        # ---------------- Spending Over Time ----------------
        st.markdown("### 📆 Spending Over Time")
        time_df = spend_df.dropna(subset=["date_parsed", "total_amount"]).sort_values("date_parsed")
        if not time_df.empty:
            st.line_chart(time_df.set_index("date_parsed")["total_amount"])
        else:
            st.info("No valid dates to plot.")

        # ---------------- Top 10 Transactions ----------------
        st.markdown("### 💳 Top 10 Transactions")

        top_df = spend_df.sort_values("total_amount", ascending=False).head(10)
        st.bar_chart(top_df.set_index("vendor_name")["total_amount"])

        st.markdown("---")

        # ---------------- Spending by Category ----------------
        st.markdown("### 🥧 Spending by Category")

        cat_df = spend_df.groupby("category")["total_amount"].sum().sort_values(ascending=False)

        # Bar Chart
        st.bar_chart(cat_df)

        # Pie Chart (Plotly)
        fig = px.pie(
            cat_df,
            values=cat_df.values,
            names=cat_df.index,
            title="Spending Distribution by Category",
            color_discrete_sequence=px.colors.sequential.Blues
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # ---------------- LLM Query ----------------
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
