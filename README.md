# 🧠 gen-ai-hs25-group15-backend

This backend powers the **HSG MBA CV Screening RAG system** — it parses uploaded CVs, evaluates eligibility against the University of St. Gallen Full-Time MBA requirements, and provides explainable feedback using the **Cognee** framework.

---

## 📦 Environment Configuration

A `.env` file should be placed in the **root directory** (same level as `README.MD`) and include:

```env
OPENAI_API_KEY=your_openai_api_key_here
LLM_API_KEY=${OPENAI_API_KEY}
COGNEE_DATA_DIR=./cognee_data
LLM_MODEL_NAME=text-embedding-3-small
COGNEE_DISABLE_PDF=1
UNSTRUCTURED_DISABLE_PDF=1
UNSTRUCTURED_USE_LOCAL_INFERENCE=1
```

⚠️ You must provide your own OpenAI API key to enable embedding and question-answering functionality.

🧰 Setting up the Python Environment
1️⃣ Create and activate a virtual environment

macOS / Linux

```
python3 -m venv .venv
source .venv/bin/activate
```


Windows (PowerShell)

```
python -m venv .venv
.venv\Scripts\activate
```

2️⃣ Install dependencies

`pip install -r requirements.txt`

Note: Versions are pinned to avoid conflicts.

🚀 Running the Application

Inside the virtual environment, run:

`uvicorn app.main:app --reload`


Or to specify a custom port (e.g., 8080):

`uvicorn app.main:app --reload --port 8080`


You should see output similar to:

INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

🌐 Access the API

Once the server is running, open your browser at:

👉 `http://127.0.0.1:8000/docs`

This will display the interactive Swagger UI, where you can test the available endpoints:

`/screen` — upload a CV and check eligibility

Knowledge visualization:
`http://127.0.0.1:8000/static/graph_after_cognify.html`
