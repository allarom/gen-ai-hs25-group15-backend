import os
from getpass import getpass
from io import BytesIO
from pathlib import Path
from cognee import add, search, cognify, prune
from cognee.api.v1.visualize.visualize import visualize_graph
from docx import Document
from dotenv import load_dotenv, set_key
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles


# .env should be placed in root of repo
def load_env():
    repo_root = Path(__file__).resolve().parents[1]
    dotenv_path = repo_root / ".env"

    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=False)
        print(f"[env] loaded {dotenv_path}")

    openai_key = os.getenv("OPENAI_API_KEY")
    llm_key = os.getenv("LLM_API_KEY")

    # Prompt before app starts, so it's synchronous
    if not openai_key and not llm_key:
        print("\n⚠️  No LLM API key found.")
        user_key = getpass("Enter your OpenAI or LLM API key: ").strip()
        if user_key:
            os.environ["OPENAI_API_KEY"] = user_key
            os.environ["LLM_API_KEY"] = user_key

            if not dotenv_path.exists():
                dotenv_path.touch()
            set_key(dotenv_path, "OPENAI_API_KEY", user_key)
            set_key(dotenv_path, "LLM_API_KEY", user_key)
            print(f"[env] ✅ API key saved to {dotenv_path}")
        else:
            print("[env] ❌ No key entered. The app may not start properly.")

    print("[env] OPENAI_API_KEY set:", bool(os.getenv("OPENAI_API_KEY")))
    print("[env] LLM_API_KEY set:", bool(os.getenv("LLM_API_KEY")))


# Call this BEFORE creating FastAPI app
load_env()


data_dir = './cognee_data'
study_requirements_file = 'HSG-MBA-application-requirements.docx'


app = FastAPI(title="Minimal Cognee Chat")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ───────────────────────────────────────────────
# Helper to extract text from uploaded .docx
# ───────────────────────────────────────────────
def docx_to_text(file_bytes: bytes) -> str:
    doc = Document(BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

# ───────────────────────────────────────────────
# Upload + ask in one go
# ───────────────────────────────────────────────
@app.post("/chat")
async def chat(file: UploadFile = File(...), question: str = Form(...)):
    if not file.filename.lower().endswith(".docx"):
        return {"ok": False, "error": "Only .docx files supported"}

    # Extract CV text
    file_bytes = await file.read()
    cv_text = docx_to_text(file_bytes)

    # https://docs.cognee.ai/core-concepts/main-operations/search
    # We input CV text, the question, and context about the role

    # Under the hood, Cognee blends vector similarity, graph structure,
    # and LLM reasoning to return answers with context and provenance.
    results = await search(
        query_text=(
            "You are an admissions assistant for the HSG Full-Time MBA. "
            "Answer strictly using the CV summary and policy. "
            f"This is the applicant's CV: {cv_text}. "
            f"This is the applicant's question: {question}"
        ),
        top_k=3
    )
    # Simple textual answer (Cognee handles the LLM call internally)
    return {"ok": True, "answer": results}

# ───────────────────────────────────────────────
# Example: preload the HSG policy
# ───────────────────────────────────────────────
@app.on_event("startup")
async def preload_policy():
    policy_path = "HSG-MBA-application-requirements.docx"
    # if you are changing requirements file make sure, you are resetting the system
    # await prune.prune_data()
    # await prune.prune_system(metadata=True)

    if os.path.exists(policy_path):
        with open(policy_path, "rb") as f:
            requirements = docx_to_text(f.read())
        
        # https://docs.cognee.ai/core-concepts/main-operations/add
        # takes your files, directories, or raw text, normalizes them into plain text,
        #  and records them into a dataset
        await add(requirements)

        # https://docs.cognee.ai/core-concepts/main-operations/cognify
        # turns plain text into structured knowledge: chunks, embeddings, summaries, nodes,
        # and edges that live in Cognee’s vector and graph stores
        await cognify()

        # you can access the knowledge graph visualization of requirements 
        # at: http://127.0.0.1:8000/static/graph_after_cognify.html
        await visualize_graph("./static/graph_after_cognify.html")
        print("[Startup] Ingested HSG policy for context.")

# to reset the system (data + metadata)
@app.post("/reset")
async def reset():
    await prune.prune_data()
    await prune.prune_system(metadata=True)
    return {"ok": True, "message": "System reset completed."}
