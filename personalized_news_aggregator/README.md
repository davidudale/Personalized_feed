# Personalized News Aggregator Using NLP

This is a Flask-based MVP for a personalized news aggregator. It collects RSS articles, applies lightweight NLP, stores data in PostgreSQL, and recommends articles based on user preferences and reading actions.

## Features

- User registration and login
- User news preference selection
- RSS news collection with `feedparser`
- Optional article scraping with `BeautifulSoup`
- Topic classification using keyword-backed lightweight NLP
- Sentiment analysis using VADER
- Keyword/entity extraction with spaCy when available
- Personalized feed using TF-IDF and cosine similarity
- Simulated Precision@K score for recommendation evaluation

## Setup In VS Code

Open this folder in VS Code:

```powershell
cd "C:\Users\David Udale Anyegwu\Documents\New project\personalized_news_aggregator"
code .
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create a PostgreSQL database:

```powershell
createdb news_aggregator
```

Set the database connection string. Adjust the username and password to match your PostgreSQL installation:

```powershell
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/news_aggregator"
```

Optional spaCy English model:

```powershell
python -m spacy download en_core_web_sm
```

Run the app:

```powershell
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## How To Demonstrate The Project

1. Register a user and choose categories such as Technology, Business, and Health.
2. View the personalized feed.
3. Click Refresh RSS to fetch live news.
4. Like, save, view, or skip articles.
5. Reload the feed and observe how ranking changes.
6. Use the displayed Precision@10 value as a simple recommendation evaluation metric.

## Suggested Report Mapping

- Requirements analysis: user login, preference selection, article collection, classification, recommendation.
- System design: Flask backend, PostgreSQL database, RSS ingestion module, NLP pipeline, recommender.
- Implementation: `app.py`, `database.py`, `news_fetcher.py`, `nlp_pipeline.py`, `recommender.py`.
- Evaluation: category classification metrics can be added with a labelled dataset; recommendation relevance is represented with Precision@K.
