import os, re, uuid
from io import BytesIO
from typing import Dict, Any, List
from fastapi import FastAPI, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from docx import Document
from dotenv import load_dotenv, find_dotenv
from cognee import add, search
from openai import OpenAI

# ── env & clients ───────────────────────────────────────────────
load_dotenv(find_dotenv())
os.environ.setdefault("COGNEE_DATA_DIR", os.path.abspath("./cognee_data"))
os.makedirs(os.getenv("COGNEE_DATA_DIR"), exist_ok=True)

OPENAI = OpenAI() if os.getenv("OPENAI_API_KEY") else None
CHAT_MODEL = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")

app = FastAPI(title="HSG MBA Chatbot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=False
)

# ── tiny in-memory session store (no auth) ──────────────────────
SESSIONS: Dict[str, Dict[str, Any]] = {}
# SESSIONS[session_id] = {
#   "cv_text": "<full cv text>",
#   "history": [{"role":"user","content":"..."},{"role":"assistant","content":"..."}]
# }

# ── helpers ─────────────────────────────────────────────────────
def docx_to_text(buf: bytes) -> str:
    doc = Document(BytesIO(buf))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def summarize_cv(cv_text: str) -> str:
    # ultra-cheap summary: extract key lines (education, experience, language, tests)
    lines = [l.strip() for l in cv_text.splitlines() if l.strip()]
    keep = [l for l in lines if re.search(r"(education|experience|english|gmat|gre|ea|bsc|msc|master|bachelor)", l, re.I)]
    head = "\n".join(keep[:30])
    return head if head else cv_text[:1200]

def pull_text(hit: Any) -> str:
    if isinstance(hit, dict):
        return hit.get("text") or hit.get("content") or str(hit)
    return getattr(hit, "text", None) or getattr(hit, "content", None) or str(hit)

def build_messages(user_question: str, cv_summary: str, policy_snippets: List[str]) -> List[Dict[str, str]]:
    policy = "\n\n---\n".join(f"[{i+1}] {s}" for i, s in enumerate(policy_snippets))
    system = (
        "You are an admissions assistant for the HSG Full-Time MBA. "
        "Answer strictly using the CV summary and policy snippets. "
        "If something is not present, say 'Not found in CV/policy'. "
        "Cite snippet numbers like [1], [2] when referring to policy."
    )
    user = (
        f"Applicant CV (summary):\n{cv_summary}\n\n"
        f"Policy snippets:\n{policy if policy_snippets else '(none)'}\n\n"
        f"Question: {user_question}\n"
        f"Answer in 2–4 sentences, concise."
    )
    return [{"role":"system","content":system},{"role":"user","content":user}]

# ── preload policy (RAG knowledge base) ─────────────────────────
POLICY_DOC = os.path.join(os.path.dirname(__file__), "HSG-MBA-application-requirements.docx")

@app.on_event("startup")
async def preload_policy():
    if os.path.exists(POLICY_DOC):
        text = docx_to_text(open(POLICY_DOC, "rb").read())
        try:
            await add(text)   # ingest once
            print("[startup] Policy ingested.")
        except Exception as e:
            print("[startup] Ingestion error:", e)
    else:
        print(f"[startup] Policy doc not found: {POLICY_DOC}")

# ── endpoints ───────────────────────────────────────────────────
@app.post("/upload")
async def upload(file: UploadFile):
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(400, "Only .docx files are supported")
    buf = await file.read()
    cv_text = docx_to_text(buf)
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {"cv_text": cv_text, "history": []}
    # Optional: also ingest the CV text, so /search can find it
    try: _ = await add(f"[SESSION:{session_id}]\n{cv_text}")
    except: pass
    return {"ok": True, "session_id": session_id}

@app.post("/chat")
async def chat(
    session_id: str = Body(..., embed=True),
    message: str = Body(..., embed=True),
    top_k: int = Body(6, embed=True)
):
    # 0) session check
    sess = SESSIONS.get(session_id)
    if not sess:
        raise HTTPException(404, "Session not found. Upload a CV first.")
    cv_text = sess["cv_text"]
    cv_summary = summarize_cv(cv_text)

    # 1) retrieve supporting policy snippets
    try:
        hits = await search(query_text=message, top_k=top_k)  # Cognee v0.3.6 signature
        hits = hits if isinstance(hits, (list, tuple)) else [hits]
        snippets = [pull_text(h) for h in hits if h]
        snippets = [s for s in snippets if isinstance(s, str) and s.strip()][:top_k]
    except Exception as e:
        snippets = [f"(retrieval failed: {type(e).__name__})"]

    # 2) generate answer (LLM) or fallback
    if OPENAI:
        msgs = build_messages(message, cv_summary, snippets)
        resp = OPENAI.chat.completions.create(model=CHAT_MODEL, messages=msgs, temperature=0)
        answer = resp.choices[0].message.content.strip()
    else:
        # offline fallback: show best snippet & echo
        answer = f"(No LLM configured) Closest policy snippet:\n{snippets[0] if snippets else '(none)'}"

    # 3) keep short history (last 10)
    sess["history"].append({"role":"user","content":message})
    sess["history"].append({"role":"assistant","content":answer})
    sess["history"] = sess["history"][-10:]

    return {"ok": True, "answer": answer, "snippets": snippets, "session_id": session_id}

@app.post("/reset")
async def reset(session_id: str = Body(..., embed=True)):
    SESSIONS.pop(session_id, None)
    return {"ok": True}

@app.get("/")
def read_root():
    return FileResponse("static/graph_after_cognify").html