project:
  name: "AI Finance Assistant – Hackathon 2025"
  description: |
    A complete AI-powered finance assistant that extracts transactions from PDFs/Images,
    performs vector search over parsed data, and answers financial questions through
    a multi-agent system. Includes Streamlit dashboard, FastAPI backend, and RAG pipeline.

  features:
    - Upload PDF/Image bank statements
    - OCR + Parsing → Structured transactions
    - Vector Search (RAG)
    - Summary Agent
    - Tax Deduction Agent
    - Spending Patterns Dashboard
    - Compliance/Fraud Agent
    - LLM-driven natural language querying
    - Plotly charts + KPIs

  tech_stack:
    frontend:
      - Streamlit
      - Plotly
    backend:
      - FastAPI
      - Uvicorn
    ai_models:
      - Google Gemini API
      - OpenAI GPT-4o-mini
    vector_search:
      - Sentence Transformers MiniLM embeddings
      - Qdrant
    data_processing:
      - Pandas
      - OCR parsing
    visualization:
      - Streamlit charts
      - Plotly express

installation:
  clone_repo: |
    git clone https://github.com/<your-username>/Hackathon-Technica-2025.git
    cd Hackathon-Technica-2025

  create_venv: |
    python -m venv hack
    hack\Scripts\activate  # Windows
    # Alternatively for macOS/Linux:
    # source hack/bin/activate

  install_requirements: |
    pip install -r req.txt

  env_file: |
    OPENAI_API_KEY=your_key_here
    GEMINI_API_KEY=your_key_here

run_app:
  backend: |
    uvicorn src.backend.dispatcher:app --reload
  backend_urls:
    - http://127.0.0.1:8000
    - http://127.0.0.1:8000/docs

  frontend: |
    streamlit run src/frontend/app.py
  frontend_url: http://localhost:8501

multi_agent_system:
  summary_agent: |
    Provides clean summarization of transactions, balances, and spending patterns.

  tax_agent: |
    Identifies tax-deductible expenses (meals, travel, work-related items).

  spending_patterns_agent: |
    Generates KPIs, spending over time, category distribution, and top transactions.
    Supports natural-language questions.

  compliance_agent: |
    Flags suspicious or unusual transactions using rule-based + LLM reasoning.

rag_pipeline:
  steps:
    - Parse user PDF/Image into raw text
    - Convert raw text → structured rows
    - Build vector documents with metadata
    - Store embeddings locally
    - Query vector DB when user asks a question
    - Add retrieved context to the LLM prompt
    - Return final AI-reasoned answer

api_endpoints:
  - path: "/process"
    method: "POST"
    description: "Uploads PDF/Image → Returns parsed transactions"

  - path: "/query"
    method: "POST"
    description: "RAG + LLM reasoning. All agents operate through this endpoint."

deployment_options:
  recommended:
    - Fly.io
    - Render
    - Cloudflare Pages + Workers
    - AWS EC2

  notes: |
    The Streamlit frontend and FastAPI backend can be deployed
    together on a single VM or separately on different services.

testing:
  run_tests: |
    python test.py
    python test_gemini.py

future_improvements:
  - Add authentication (JWT)
  - Add multi-user support
  - Connect to Postgres database
  - Add real-time notifications
  - Implement GPT-4o / R1 reasoning
  - Build mobile dashboard version










author:
  name: "Vishal Fulsundar"
  affiliation: "MS Data Science, George Washington University"
  interests:
    - AI/ML Engineering
    - Multi-Agent Systems
    - RAG Architectures
    - Applied Machine Learning
