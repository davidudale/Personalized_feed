from contextlib import closing

import psycopg2
from psycopg2.extras import RealDictCursor

from config import CATEGORIES, DATABASE_URL


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    preferences TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT,
    source TEXT,
    url TEXT NOT NULL UNIQUE,
    published TEXT,
    category TEXT,
    sentiment TEXT,
    sentiment_score REAL DEFAULT 0,
    keywords TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    article_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(article_id) REFERENCES articles(id)
);
"""


class DatabaseConnection:
    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

    def execute(self, query, params=None):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type:
            self.rollback()
        self.close()


def get_connection():
    return DatabaseConnection()


def init_db():
    with closing(get_connection()) as conn:
        conn.execute(SCHEMA)
        conn.commit()


def seed_sample_articles(process_article):
    samples = [
        (
            "AI tools reshape software development across Africa",
            "Technology companies are using artificial intelligence tools to improve productivity and create new digital services.",
            "Tech Daily",
            "sample://ai-tools-africa",
        ),
        (
            "Government announces new economic policy for small businesses",
            "The policy is expected to support entrepreneurs, improve taxation, and strengthen local business activity.",
            "National Business",
            "sample://economic-policy-small-business",
        ),
        (
            "Health officials encourage vaccination and regular screening",
            "Medical experts say early screening and vaccination can reduce preventable disease in local communities.",
            "Health Watch",
            "sample://health-vaccination-screening",
        ),
        (
            "Local football club wins championship after dramatic final",
            "Fans celebrated after the team scored late in the match to secure a historic sports victory.",
            "Sports Desk",
            "sample://football-championship-final",
        ),
        (
            "Election debate focuses on security, jobs, and education",
            "Political candidates presented their plans ahead of the election during a televised national debate.",
            "Civic News",
            "sample://election-debate-security-jobs",
        ),
    ]

    with closing(get_connection()) as conn:
        existing = conn.execute("SELECT COUNT(*) AS count FROM articles").fetchone()["count"]
        if existing:
            return

        for title, text, source, url in samples:
            processed = process_article(f"{title}. {text}")
            conn.execute(
                """
                INSERT INTO articles
                (title, summary, content, source, url, published, category, sentiment, sentiment_score, keywords)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
                """,
                (
                    title,
                    text,
                    text,
                    source,
                    url,
                    "Sample data",
                    processed["category"],
                    processed["sentiment"],
                    processed["sentiment_score"],
                    ", ".join(processed["keywords"]),
                ),
            )
        conn.commit()


def get_user_profile(user_id):
    with closing(get_connection()) as conn:
        user = conn.execute("SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()
        if not user:
            return {category: 0.0 for category in CATEGORIES}

        profile = {category: 0.0 for category in CATEGORIES}
        for category in user["preferences"].split(","):
            if category in profile:
                profile[category] += 2.0

        rows = conn.execute(
            """
            SELECT articles.category, interactions.action, COUNT(*) AS count
            FROM interactions
            JOIN articles ON articles.id = interactions.article_id
            WHERE interactions.user_id = %s
            GROUP BY articles.category, interactions.action
            """,
            (user_id,),
        ).fetchall()

        weights = {"view": 0.5, "like": 1.5, "save": 1.2, "skip": -0.7}
        for row in rows:
            if row["category"] in profile:
                profile[row["category"]] += weights.get(row["action"], 0) * row["count"]

        return profile
