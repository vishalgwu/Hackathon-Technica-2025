
#  Global Income & Demographic Insights Dashboard  
### Streamlit · World Bank Data · RAG , LLM Analytics

A research-grade, interactive dashboard built to explore **global income, inequality, fragility, gender, and demographic patterns** using **World Bank datasets**.  
The project blends **data visualization** with a **Retrieval-Augmented Generation (RAG)** system so users can directly *ask questions* and receive answers grounded in the data.

---

## 🔍 Project Motivation

The World Bank dataset (~150MB across two Excel files) contains rich variables:

- `countryname`, `year`, `decile`, `Income_Level`, `Income`
- `regionname`, `fragile`, `gender`, `Demographic`, `Resource`, etc.

Such multidimensional data is difficult to explore with traditional dashboards.  
This project solves that by offering:

- Interactive analytics  
- A “Chat with the Data” LLM agent  
- Clean, research-ready visualizations  
- Transparent, grounded insights  

---

## 🎯 Problem We Address

> **How do we make global inequality and demographic patterns easy to explore without code?**

### Our solution:
- Streamlit dashboard for rich visual analysis  
- RAG engine for natural-language Q&A  
- Vector search over text-converted data  
- LLM reasoning supported by retrieval context  

---

## 📁 Dataset Source

All data comes from the **World Bank Open Data Portal**.  
We use two large Excel files containing income levels, deciles, regions, fragility, and demographic attributes.

---

## 🧠 System Architecture (Short)

```text
World Bank Excel → ETL → Clean Data → Text Chunks
        → Embeddings → Vector Store → RAG Engine → Streamlit
🗂️ Repository Structure
bash
Copy code
.
├── data/                # raw & cleaned World Bank files
├── etl/                 # cleaning, chunking, preprocessing
├── rag/                 # embeddings + retrieval pipeline
├── app/                 # Streamlit dashboard
├── notebooks/           # EDA & prototyping
├── requirements.txt
└── README.md
🚀 Features
✔ Interactive Visualizations

Income distribution (deciles, regions)

Fragility vs income

Gender & demographic comparisons

Time-series trends

✔ Ask-the-Data (LLM + RAG)
Users can ask questions such as:

“Income trends in South Asia after 2010?”

“Compare fragile vs non-fragile income levels.”

“Which region has the highest top-decile growth?”

The system retrieves relevant slices of data and generates accurate, grounded summaries.

🧩 How to Run
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Prepare data:

bash
Copy code
python etl/01_load_and_clean.py
python etl/03_build_text_chunks.py
Build embeddings:

bash
Copy code
python rag/embeddings.py
Launch dashboard:

bash
Copy code
streamlit run app/streamlit_app.py
📈 Example Use Cases
Policy analysts: Compare fragile-state income evolution.

Students: Explore gender/demographic shifts.

Researchers: Study inequality using decile-level data.

Anyone: “Talk to the dataset” using natural language.

🚀 Future Enhancements
Forecasting (Prophet, LSTM)

Deeper inequality metrics (Gini, Theil)

Multi-turn conversational agent

Cloud deployment (Streamlit Cloud / AWS)
