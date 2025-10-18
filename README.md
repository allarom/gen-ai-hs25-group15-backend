# gen-ai-hs25-group15-backend
For Visual Studio to specify your environment
python3 -m venv .venv   
source .venv/bin/activate        # macOS/Linux
# or
.venv\Scripts\activate           # Windows PowerShell

pip install -r requirements.txt (list of packages with versions, was conflicting)

Run FastAPI locally
Inside the virtual environment, run:

uvicorn app.main:app --reload

or if you want to specify another port : uvicorn app.main:app --reload --PORT 8080
You’ll see something like:

INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)


Check http://127.0.0.1:8000/docs to see different endpoints