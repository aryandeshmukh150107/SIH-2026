import sys #vasundhara
import os
from pathlib import Path

# Ensure we can import text_cleaner when running directly or as a module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))          # .../ml/preprocessing
_ML_DIR   = os.path.dirname(_THIS_DIR)                          # .../ml
_SENTIMENT_DIR = os.path.join(_ML_DIR, "sentiment")             # .../ml/sentiment
if _SENTIMENT_DIR not in sys.path:
    sys.path.insert(0, _SENTIMENT_DIR)

# Try to import the sentiment pipeline (safe — lazy init, no sys.exit at module level)
try:
    from run_sentiment_pipeline import run_pipeline as _run_pipeline
    _sentiment_ready = True
    _sentiment_error = ""
except Exception as _e:
    _sentiment_ready = False
    _sentiment_error = str(_e)
    print("[WARNING] Sentiment pipeline not available:", _e)

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from text_cleaner import clean_text

app = FastAPI(title="SIH Text Preprocessor API")

# Enable CORS so the browser can make requests to this API from index.html
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow any origin for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CleanRequest(BaseModel):
    text: str

class CleanResponse(BaseModel):
    cleaned_text: str

@app.post("/clean", response_model=CleanResponse)
def clean_text_endpoint(request: CleanRequest):
    """Clean the submitted text before it is saved to Supabase."""
    cleaned = clean_text(request.text)
    return CleanResponse(cleaned_text=cleaned)


@app.post("/run-sentiment", include_in_schema=True)
def run_sentiment_endpoint(background_tasks: BackgroundTasks):
    """
    Triggers the sentiment pipeline in the background.
    Fetches all unscored rows from Supabase and writes sentiment_score
    and sentiment_type back. Returns immediately; processing happens async.
    Requires SUPABASE_URL and SUPABASE_SERVICE_KEY env vars to be set.
    """
    if not _sentiment_ready:
        return JSONResponse(
            status_code=503,
            content={"error": "Sentiment pipeline not available", "detail": _sentiment_error}
        )
    background_tasks.add_task(_run_pipeline)
    return {"status": "ok", "message": "Sentiment pipeline started in background"}


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"


@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")

if __name__ == "__main__":
    import uvicorn
    # reload=False: reload mode conflicts with background tasks and model loading
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
