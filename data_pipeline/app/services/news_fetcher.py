"""
app/services/news_fetcher.py — Simple RSS/news fetcher.

Fetches recent items from a set of RSS feeds, filters them by query
keywords, and returns structured items suitable for the research pipeline.
This avoids reliance on paid search APIs and provides immediate, crawlable
news content for embedding.
"""
from typing import List, Dict
import logging
import requests
import feedparser
from bs4 import BeautifulSoup

logger = logging.getLogger("trademate.news")

# A short curated list of global & regional news RSS feeds. Add/remove as needed.
RSS_FEEDS = [
    "http://feeds.reuters.com/Reuters/worldNews",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.dawn.com/rss/world.xml",
    "https://tribune.com.pk/feed/",
]


def _extract_text_from_url(url: str) -> str:
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.debug("Failed to fetch full article %s: %s", url, e)
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")
    # Simple extraction: join paragraph texts
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    return "\n\n".join(p for p in paragraphs if p)


def fetch_news_by_query(
    query: str,
    max_items: int = 20,
    require_all: bool = True,
    full_fetch_limit: int = 10,
) -> List[Dict]:
    """
    Return a list of dicts: {title, content, source, url} matching the query.

    Matching modes:
    - If `require_all` is True, an entry must contain ALL keywords from the
      query (AND). Otherwise it matches any keyword (OR).

    To reduce HTTP requests, `full_fetch_limit` controls how many matched
    results will have their article pages fetched and parsed. Remaining
    matched items will use the feed summary/description only.
    """
    keywords = [t.lower() for t in query.split() if t.strip()]
    if not keywords:
        return []

    results: List[Dict] = []
    full_fetched = 0

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            logger.debug("Failed to parse feed %s: %s", feed_url, e)
            continue

        for entry in feed.entries:
            title = (entry.get("title") or "").strip()
            summary = (entry.get("summary") or entry.get(
                "description") or "").strip()
            link = entry.get("link") or entry.get("id")
            text_blob = " ".join([title, summary]).lower()

            if require_all:
                matched = all(k in text_blob for k in keywords)
            else:
                matched = any(k in text_blob for k in keywords)

            if not matched:
                continue

            # Only fetch full HTML for a limited number of items to reduce
            # outbound HTTP calls from the Lambda. Use feed summary otherwise.
            content = summary
            if full_fetched < full_fetch_limit and link:
                fetched = _extract_text_from_url(link)
                if fetched:
                    content = fetched
                full_fetched += 1

            results.append({
                "title": title,
                "content": content,
                "source": feed.feed.get("title", feed_url),
                "url": link,
            })

            if len(results) >= max_items:
                break

        if len(results) >= max_items:
            break

    return results
