import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/news_aggregator",
)
SECRET_KEY = "change-this-secret-key-before-deployment"

CATEGORIES = [
    "Politics",
    "Business",
    "Technology",
    "Sports",
    "Health",
    "Entertainment",
    "World",
]

RSS_FEEDS = {
    "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "BBC Technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "BBC Business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "BBC Health": "https://feeds.bbci.co.uk/news/health/rss.xml",
    "The Guardian World": "https://www.theguardian.com/world/rss",
    "Punch Nigeria": "https://punchng.com/feed/",
    "Vanguard Nigeria": "https://www.vanguardngr.com/feed/",
}
