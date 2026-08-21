# SIH-2026

## Run the comment portal locally

The frontend sends comments to the FastAPI text-cleaning service at `http://localhost:8000`. Start the API on the same computer where the frontend is opened.

### 1. Install Python dependencies

From the repository root:

```powershell
python -m pip install -r requirements.txt
```

Using a virtual environment is recommended:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Start the text-cleaning API

```powershell
cd ml\preprocessing
python api.py
```

Leave this terminal running. The API should be available at `http://localhost:8000/docs`.

### 3. Open the frontend

Open `frontend/index.html` in a browser, or serve the repository with a local static server. The Supabase configuration is already included in the frontend.

### Troubleshooting

- `Import "emoji" could not be resolved`: select the virtual environment in VS Code with **Python: Select Interpreter**, then install `requirements.txt` into that environment.
- `Failed to fetch`: the API is not running, the API dependencies are missing, or the frontend is being opened on a different computer from the API. In the last case, replace `localhost` in `frontend/index.html` with the API computer's reachable IP address and allow port `8000` through its firewall.


Ministry of Corporate Affairs :	Sentiment analysis of comments received through E-consultation module	Software	: SIH25035 : theme:	Miscellaneous

