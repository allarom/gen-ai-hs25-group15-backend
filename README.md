# 🧠 gen-ai-hs25-group15

This application powers the **HSG MBA CV Screening RAG system** — it parses uploaded CVs, This app implements a Retrieval-Augmented Generation (RAG) chatbot that helps applicants check whether they meet the admission requirements for the University of St. Gallen Full-Time MBA program.

It uses the Cognee framework for knowledge ingestion, semantic memory, and graph visualization — without needing any additional databases or orchestration layers.

---

## 📦 Environment Configuration

A `.env` file should be placed in the **root directory** (same level as `README.MD`) and include:

```env
OPENAI_API_KEY=your_api_key
LLM_API_KEY=${OPENAI_API_KEY}
COGNEE_DATA_DIR=./cognee_data
LLM_MODEL_NAME=gpt-4o-mini
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

`cd app`
`uvicorn main:app --reload`
(you may encounter problems if you run it not from the app folder)


Or to specify a custom port (e.g., 8080):

`uvicorn main:app --reload --port 8080`


You should see output similar to:

INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

🌐 Access the API

Once the server is running, open your browser at:

👉 `http://127.0.0.1:8000/docs`

This will display the interactive Swagger UI, where you can test the available endpoints:

`/chat` — upload a CV and and ask questions about eligibility. For example: "Can I apply for MBA programm?"
Click on /chat, Try it out, upload docx CV and enter question. Click on execute. You can enter multiple questions. Offtopic questions will be not answered.

We provide CVs for testing, eligible and non eligible in app/test-files folder

`/reset` - clears state of the app, if for example requirement file was changed

Knowledge visualization requirements:
`http://127.0.0.1:8000/static/graph_after_cognify.html`
