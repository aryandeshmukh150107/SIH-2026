"""Fetch topic-relevant Reddit comments into Supabase.

Usage from the repository root:
    python ml/reddit/reddit_ingestion.py "India economy"

Required environment variables:
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
    SUPABASE_URL, SUPABASE_SERVICE_KEY
"""

from __future__ import annotations

import logging
import os
import re
import sys
from datetime import datetime, timezone
from typing import Iterable


TABLE = "reddit_comments"
DEFAULT_POST_LIMIT = 25
DEFAULT_COMMENT_LIMIT = 500
ID_BATCH_SIZE = 100
STOP_WORDS = {
    "about", "after", "again", "against", "being", "between", "could",
    "from", "have", "into", "more", "most", "other", "should", "their",
    "there", "these", "they", "this", "those", "under", "were", "which",
    "with", "would",
}

logger = logging.getLogger("reddit_ingestion")


def _query_terms(query: str) -> set[str]:
    """Return meaningful words used for the local comment relevance check."""
    terms = set(re.findall(r"[\w']+", query.casefold()))
    meaningful = {term for term in terms if len(term) > 2 and term not in STOP_WORDS}
    return meaningful or terms


def _is_relevant(text: str, terms: set[str]) -> bool:
    body_terms = set(re.findall(r"[\w']+", text.casefold()))
    return bool(body_terms & terms)


def _comment_row(comment, query_terms: set[str]) -> dict | None:
    body = getattr(comment, "body", None)
    reddit_id = getattr(comment, "id", None)
    created_utc = getattr(comment, "created_utc", None)

    if not isinstance(reddit_id, str) or not reddit_id.strip():
        logger.info("invalid/deleted comment skipped: missing Reddit ID")
        return None
    if not isinstance(body, str) or not body.strip():
        logger.info("invalid/deleted comment skipped: reddit_id=%s", reddit_id)
        return None
    if body in {"[deleted]", "[removed]"}:
        logger.info("invalid/deleted comment skipped: reddit_id=%s", reddit_id)
        return None
    if not _is_relevant(body, query_terms):
        logger.info("irrelevant comment skipped: reddit_id=%s", reddit_id)
        return None
    if not isinstance(created_utc, (int, float)):
        logger.info("invalid comment skipped: reddit_id=%s has no timestamp", reddit_id)
        return None

    created = datetime.fromtimestamp(created_utc, tz=timezone.utc)
    subreddit = getattr(getattr(comment, "subreddit", None), "display_name", None)
    return {
        "reddit_id": reddit_id,
        "subreddit": subreddit if isinstance(subreddit, str) else "",
        "text": body,
        "score": int(getattr(comment, "score", 0) or 0),
        "sentiment": None,
        "confidence": None,
        "date": created.date().isoformat(),
        "time": created.time().isoformat(timespec="seconds"),
    }


def _get_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set.")

    try:
        from supabase import create_client
    except ImportError as exc:
        raise RuntimeError("supabase-py is not installed. Run: pip install -r requirements.txt") from exc
    return create_client(url, key)


def _get_reddit():
    values = {
        "client_id": os.environ.get("REDDIT_CLIENT_ID"),
        "client_secret": os.environ.get("REDDIT_CLIENT_SECRET"),
        "user_agent": os.environ.get("REDDIT_USER_AGENT"),
    }
    env_names = {
        "client_id": "REDDIT_CLIENT_ID",
        "client_secret": "REDDIT_CLIENT_SECRET",
        "user_agent": "REDDIT_USER_AGENT",
    }
    missing = [env_names[name] for name, value in values.items() if not value]
    if missing:
        raise RuntimeError("Missing Reddit environment variables: " + ", ".join(missing))

    try:
        import praw
    except ImportError as exc:
        raise RuntimeError("praw is not installed. Run: pip install -r requirements.txt") from exc
    return praw.Reddit(**values, check_for_async=False)


def _is_rate_limit_error(error: Exception) -> bool:
    response = getattr(error, "response", None)
    return getattr(error, "status", None) == 429 or getattr(response, "status_code", None) == 429


def _existing_ids(supabase, reddit_ids: Iterable[str]) -> set[str]:
    existing: set[str] = set()
    ids = list(reddit_ids)
    for start in range(0, len(ids), ID_BATCH_SIZE):
        response = (
            supabase.table(TABLE)
            .select("reddit_id")
            .in_("reddit_id", ids[start:start + ID_BATCH_SIZE])
            .execute()
        )
        existing.update(row["reddit_id"] for row in (response.data or []) if row.get("reddit_id"))
    return existing


def ingest(query: str, post_limit: int = DEFAULT_POST_LIMIT, comment_limit: int = DEFAULT_COMMENT_LIMIT) -> int:
    """Import relevant comments for *query* and return the inserted count."""
    query = query.strip()
    if not query:
        raise ValueError("Search query must not be empty.")

    logger.info("search query: %s", query)
    reddit = _get_reddit()
    supabase = _get_supabase()
    query_terms = _query_terms(query)
    comments_seen = 0
    rows: list[dict] = []

    try:
        posts = list(reddit.subreddit("all").search(query, sort="relevance", time_filter="all", limit=post_limit))
        logger.info("posts found: %d", len(posts))
        for post in posts:
            try:
                post.comment_sort = "relevance"
                post.comments.replace_more(limit=0)
                for comment in post.comments.list()[:comment_limit]:
                    comments_seen += 1
                    row = _comment_row(comment, query_terms)
                    if row is not None:
                        rows.append(row)
            except Exception:
                logger.exception("API error while reading comments for post %s", getattr(post, "id", "unknown"))
    except Exception:
        error = sys.exc_info()[1]
        if isinstance(error, Exception) and _is_rate_limit_error(error):
            logger.warning("Reddit API rate limit reached; no comments imported this run")
            return 0
        logger.exception("API error while searching Reddit")
        raise

    logger.info("comments found: %d; valid relevant comments: %d", comments_seen, len(rows))
    unique_rows = {row["reddit_id"]: row for row in rows}
    existing = _existing_ids(supabase, unique_rows)
    new_rows = [row for reddit_id, row in unique_rows.items() if reddit_id not in existing]
    logger.info("duplicates skipped: %d", len(unique_rows) - len(new_rows))

    inserted = 0
    for row in new_rows:
        try:
            supabase.table(TABLE).insert(row).execute()
            inserted += 1
        except Exception:
            logger.exception("Supabase error inserting reddit_id=%s", row["reddit_id"])
    logger.info("comments inserted: %d", inserted)
    return inserted


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    if len(sys.argv) != 2:
        print('Usage: python ml/reddit/reddit_ingestion.py "India economy"')
        return 2
    try:
        ingest(sys.argv[1])
    except Exception as exc:
        logger.error("ingestion failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
