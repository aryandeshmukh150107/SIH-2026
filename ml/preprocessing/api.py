import sys
import os

# Ensure we can import text_cleaner when running directly or as a module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
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

if __name__ == "__main__":
    import uvicorn
    # Run the server on port 8000
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
