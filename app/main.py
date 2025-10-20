import os
import traceback
from io import BytesIO
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from docx import Document
from pathlib import Path
from cognee import add, search, cognify, prune
import openai
from cognee.api.v1.visualize.visualize import visualize_graph

 # .env should be placed in root of repo
def load_env():
    repo_root = Path(__file__).resolve().parents[1]
    dotenv_path = repo_root / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=False)
        print(f"[env] loaded {dotenv_path}")

    # you need API keys for LLM 
    print("[env] OPENAI_API_KEY set:", bool(os.getenv("OPENAI_API_KEY")))
    print("[env] LLM_API_KEY set:", bool(os.getenv("LLM_API_KEY")))

load_env()

data_dir = './cognee_data'
study_requirements_file = 'HSG-MBA-application-requirements.docx' 

# FastAPI initialization
app = FastAPI(title="Group15 Eligibility API")

# Helpers
def docx_to_text(file_bytes: bytes) -> str:
    file_stream = BytesIO(file_bytes)
    doc = Document(file_stream)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

# Path to your requirements file 
study_requirements_file = os.path.join(
    os.path.dirname(__file__), study_requirements_file
)
# Ingest requirements once at startup 
@app.on_event("startup")
async def preload_requirements():
    print(f"[Startup] Loading requirements from {study_requirements_file}")
    if not os.path.exists(study_requirements_file):
        print(f"[WARN] Could not find {study_requirements_file}")
        return

    with open(study_requirements_file, "rb") as f:
        buf = f.read()

    text = docx_to_text(buf)

    # Ingest into Cognee knowledge base
    try:
        # Create a clean slate for cognee -- reset data and system state
        await prune.prune_data()
        await prune.prune_system(metadata=True)

        # Add content, from Cognee’s perspective, this string is a document
        result = await add(text)

         # Process with LLMs to build the knowledge graph
         # All documents are chunked, entities are extracted, 
         # relationships are made, and summaries are generated. 
        await cognify()
        await visualize_graph("./graph_after_cognify.html")
        # # Add memory algorithms to the graph
        # await memify()
        print('ingest result', result)
        print("[Startup] Requirements ingested into Cognee successfully.")
        
    except Exception as e:
        print(f"[Startup ERROR] Failed to ingest requirements: {e}")

@app.post("/screen")
async def screen(file: UploadFile):
    try:
        if not file.filename.lower().endswith(".docx"):
            raise HTTPException(400, "Only .docx supported")

        buf = await file.read()
        text = docx_to_text(buf)

        # Retrieve relevant requirements from knowledge base
        # search — Queries the knowledge graph using vector similarity 
        # and graph traversal to find relevant information and return contextual results.
        results = await search(
            query_text=text,
            top_k=3
        )
        print('results', results)
        retrieved_text = "\n".join(results)
        
        # Augment LLM generation
        prompt = f"""
        MBA Requirements:
        {retrieved_text}

        Applicant CV:
        {text}

        Does the applicants CV meet the requirements to start application? List missing criteria. 
        """
        client = openai.OpenAI()  # or openai.AsyncOpenAI() if you want async

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        return {
            "ok": True,
            "verdict": response.choices[0].message.content
        }

    except HTTPException:
        raise
    except Exception as e:
        print("SCREEN ERROR:", repr(e))
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": type(e).__name__, "detail": str(e)[:500]},
        )
