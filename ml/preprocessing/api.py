import sys
import os
from pathlib import Path

# Ensure we can import text_cleaner when running directly or as a module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.responses import FileResponse
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
    # Clean the input text using our logic
    cleaned = clean_text(request.text)
    return CleanResponse(cleaned_text=cleaned)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"


@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")

if __name__ == "__main__":
    import uvicorn
    # Run the server on port 8000
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
