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

## Import Reddit comments

The standalone importer uses Reddit's official API through PRAW and inserts into the existing `reddit_comments` Supabase table. Set these environment variables in the PowerShell session where you run it:

```powershell
$env:REDDIT_CLIENT_ID="your-reddit-client-id"
$env:REDDIT_CLIENT_SECRET="your-reddit-client-secret"
$env:REDDIT_USER_AGENT="India-Chat/1.0 by your-reddit-username"
$env:SUPABASE_URL="https://your-project.supabase.co"
$env:SUPABASE_SERVICE_KEY="your-service-role-key"
```

From the repository root, run:

```powershell
python ml/reddit/reddit_ingestion.py "India economy"
```

The importer searches relevant public posts in `all`, reads their comments, keeps non-empty comments containing a meaningful search term, and stores UTC `date` and `time`. Deleted, removed, invalid, irrelevant, and already-present comments are skipped. Sentiment fields remain null for the existing sentiment workflow. The unique `reddit_id` is checked before insertion, so rerunning the command is incremental.

To verify imports, open the Supabase Table Editor and select `reddit_comments`, or run this SQL in Supabase SQL Editor:

```sql
select reddit_id, subreddit, text, score, date, time, sentiment, confidence
from reddit_comments
order by date desc, time desc
limit 20;
```


Ministry of Corporate Affairs :	Sentiment analysis of comments received through E-consultation module	Software	: SIH25035 : theme:	Miscellaneous

