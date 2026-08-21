"""
ml/sentiment/run_sentiment_pipeline.py

Reads every row in the Supabase `comments` table where:
  - `preprocessing` is not null/empty
  - `sentiment_type` is still null  (not yet scored)

Runs the existing sentiment model on `preprocessing` and writes
`sentiment_score` and `sentiment_type` back to the same row.

Model: cardiffnlp/twitter-roberta-base-sentiment-latest
  label  -> "positive" | "negative" | "neutral"
  score  -> confidence of that label (0.0 - 1.0)

Mapping:
  sentiment_type  <- label   ("positive", "negative", "neutral")
  sentiment_score <- score   (float, 4 decimal places, 0.0 - 1.0)

Usage:
  Set env vars SUPABASE_URL and SUPABASE_SERVICE_KEY, then run:
      python ml/sentiment/run_sentiment_pipeline.py
"""

import os
import sys

# ---------------------------------------------------------------------------
# Table / column constants
# ---------------------------------------------------------------------------
TABLE = "comments"
PK_COL = "comment_id"
TEXT_COL = "preprocessing"
SCORE_COL = "sentiment_score"
TYPE_COL = "sentiment_type"

# ---------------------------------------------------------------------------
# Lazy singletons — initialised on first call to run_pipeline()
# ---------------------------------------------------------------------------
_supabase = None
_pipeline = None


def _get_supabase():
    """Return (and lazily create) the Supabase client."""
    global _supabase
    if _supabase is not None:
        return _supabase

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables must be set."
        )

    try:
        from supabase import create_client
    except ImportError:
        raise RuntimeError(
            "supabase-py is not installed. Run: pip install supabase"
        )

    _supabase = create_client(url, key)
    return _supabase


def _get_pipeline():
    """Return (and lazily load) the HuggingFace sentiment pipeline."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    try:
        from transformers import pipeline as hf_pipeline
    except ImportError:
        raise RuntimeError(
            "transformers is not installed. Run: pip install transformers torch"
        )

    print("[sentiment] Loading model cardiffnlp/twitter-roberta-base-sentiment-latest ...")
    _pipeline = hf_pipeline(
        "sentiment-analysis",
        model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    )
    print("[sentiment] Model loaded.")
    return _pipeline


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def analyze(text: str) -> dict:
    """
    Run the model on `text` and return a dict with sentiment_type and
    sentiment_score.  Returns None if text is null/empty.
    """
    if not text or not text.strip():
        return None

    result = _get_pipeline()(text)[0]
    return {
        TYPE_COL: result["label"],             # "positive" | "negative" | "neutral"
        SCORE_COL: round(result["score"], 4),  # confidence: 0.0 - 1.0
    }


def fetch_unprocessed_rows() -> list:
    """
    Fetch rows where preprocessing text exists but sentiment has not been set yet.
    """
    response = (
        _get_supabase().table(TABLE)
        .select(PK_COL + ", " + TEXT_COL)
        .not_.is_(TEXT_COL, "null")
        .is_(TYPE_COL, "null")
        .execute()
    )
    return response.data or []


def update_row(row_id, scores: dict) -> None:
    """
    Write sentiment_score and sentiment_type back to the row identified by row_id.
    """
    response = (
        _get_supabase()
        .table(TABLE)
        .update(scores)
        .eq(PK_COL, row_id)
        .execute()
    )
    # Log the raw response so we can diagnose silent failures
    print("[sentiment]   [DEBUG] update response data:", response.data)
    if not response.data:
        print("[sentiment]   [WARN] Update returned no data — possible RLS block or wrong PK column name.")
        print("[sentiment]   [WARN] PK_COL used:", PK_COL, "| row_id:", row_id)
        print("[sentiment]   [WARN] Columns updated:", list(scores.keys()))


def run_pipeline() -> None:
    """
    Main entry point.  Scores all unscored rows in Supabase.
    Safe to call multiple times; model and client are created once.
    """
    print("[sentiment] Fetching unscored rows from '" + TABLE + "' ...")
    rows = fetch_unprocessed_rows()

    if not rows:
        print("[sentiment] No unscored rows found. Nothing to do.")
        return

    print("[sentiment] Found " + str(len(rows)) + " row(s) to process.")

    success = 0
    skipped = 0
    errors = 0

    for row in rows:
        row_id = row.get(PK_COL)
        text = row.get(TEXT_COL)

        scores = analyze(text)
        if scores is None:
            print("[sentiment]   [SKIP] id=" + str(row_id) + " -- preprocessing text is null/empty")
            skipped += 1
            continue

        try:
            update_row(row_id, scores)
            print(
                "[sentiment]   [OK]   id=" + str(row_id) +
                " -> type=" + scores[TYPE_COL] +
                "  score=" + str(scores[SCORE_COL])
            )
            success += 1
        except Exception as exc:
            print("[sentiment]   [ERR]  id=" + str(row_id) + " -- failed to update: " + str(exc))
            errors += 1

    print(
        "[sentiment] Done.  OK: " + str(success) +
        "  skipped: " + str(skipped) +
        "  errors: " + str(errors)
    )


if __name__ == "__main__":
    # When run directly, check env vars eagerly and give a clear error
    if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_SERVICE_KEY"):
        print(
            "ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set as environment variables.\n"
            "  Example (PowerShell):\n"
            '    $env:SUPABASE_URL="https://<project-ref>.supabase.co"\n'
            '    $env:SUPABASE_SERVICE_KEY="<service-role-key>"\n'
            "  Never put the service-role key in frontend code."
        )
        sys.exit(1)
    run_pipeline()
