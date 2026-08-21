import sys
import os
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

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

# ---------------------------------------------------------------------------
# Background cron: run sentiment pipeline every 30 seconds
# ---------------------------------------------------------------------------
SENTIMENT_CRON_INTERVAL = 30  # seconds

async def _sentiment_cron_loop():
    """Background loop that scores unprocessed rows every 30 seconds."""
    print(f"[cron] Sentiment cron started (interval={SENTIMENT_CRON_INTERVAL}s)")
    while True:
        await asyncio.sleep(SENTIMENT_CRON_INTERVAL)
        if _sentiment_ready:
            try:
                # Run the synchronous pipeline in a thread to avoid blocking the event loop
                await asyncio.get_event_loop().run_in_executor(None, _run_pipeline)
            except Exception as exc:
                print(f"[cron] Sentiment cron error: {exc}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the sentiment cron on server boot, cancel on shutdown."""
    task = asyncio.create_task(_sentiment_cron_loop())
    print("[cron] Sentiment background task registered.")
    yield
    task.cancel()
    print("[cron] Sentiment background task cancelled.")

app = FastAPI(title="SIH Text Preprocessor API", lifespan=lifespan)

# Enable CORS so the browser can make requests to this API from Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False when allow_origins is ["*"] for browser CORS compliance
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Health check endpoint for Railway deployment probes."""
    return {"status": "ok", "sentiment_ready": _sentiment_ready}


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
