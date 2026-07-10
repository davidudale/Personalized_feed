from contextlib import closing

import feedparser
import requests
from bs4 import BeautifulSoup

from config import RSS_FEEDS
from database import get_connection
from nlp_pipeline import process_article


def fetch_page_text(url, timeout=8):
    try:
        response = requests.get(url, timeout=timeout, headers={"User-Agent": "PersonalizedNewsAggregator/1.0"})
        response.raise_for_status()
    except requests.RequestException:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "aside"]):
        tag.decompose()
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    return " ".join(paragraphs[:12])


def fetch_rss_articles(limit_per_feed=8, fetch_full_text=False):
    saved = 0
    with closing(get_connection()) as conn:
        for source, feed_url in RSS_FEEDS.items():
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:limit_per_feed]:
                title = getattr(entry, "title", "Untitled article")
                url = getattr(entry, "link", "")
                summary = getattr(entry, "summary", "")
                published = getattr(entry, "published", "")
                content = fetch_page_text(url) if fetch_full_text and url else summary
                processed = process_article(f"{title}. {summary}. {content}")
                cursor = conn.execute(
                    """
                    INSERT INTO articles
                    (title, summary, content, source, url, published, category, sentiment, sentiment_score, keywords)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                    """,
                    (
                        title,
                        summary,
                        content,
                        source,
                        url,
                        published,
                        processed["category"],
                        processed["sentiment"],
                        processed["sentiment_score"],
                        ", ".join(processed["keywords"]),
                    ),
                )
                saved += cursor.rowcount
        conn.commit()
    return saved
