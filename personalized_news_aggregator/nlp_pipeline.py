import re
from collections import Counter

from config import CATEGORIES

try:
    import spacy
except ImportError:  # pragma: no cover
    spacy = None

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:  # pragma: no cover
    SentimentIntensityAnalyzer = None


CATEGORY_KEYWORDS = {
    "Politics": ["government", "election", "minister", "policy", "senate", "president", "law", "vote"],
    "Business": ["market", "economy", "business", "company", "trade", "bank", "finance", "investment"],
    "Technology": ["technology", "ai", "software", "startup", "digital", "cyber", "internet", "data"],
    "Sports": ["football", "match", "league", "team", "coach", "player", "goal", "championship"],
    "Health": ["health", "hospital", "doctor", "disease", "medicine", "vaccine", "screening", "medical"],
    "Entertainment": ["movie", "music", "celebrity", "film", "artist", "festival", "show", "entertainment"],
    "World": ["world", "global", "international", "foreign", "war", "climate", "border", "diplomacy"],
}

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were", "will", "have",
    "has", "into", "after", "their", "about", "said", "says", "new", "more", "over", "been",
}

_nlp = None
_sentiment = SentimentIntensityAnalyzer() if SentimentIntensityAnalyzer else None


def _load_spacy():
    global _nlp
    if _nlp is not None:
        return _nlp
    if spacy is None:
        return None
    try:
        _nlp = spacy.load("en_core_web_sm")
    except OSError:
        _nlp = spacy.blank("en")
    return _nlp


def clean_text(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"[^A-Za-z0-9\s.,'-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def classify_topic(text):
    tokens = set(re.findall(r"[a-zA-Z]+", text.lower()))
    scores = {
        category: sum(1 for word in words if word.lower() in tokens)
        for category, words in CATEGORY_KEYWORDS.items()
    }
    best_category, best_score = max(scores.items(), key=lambda item: item[1])
    return best_category if best_score else "World"


def extract_keywords(text, limit=8):
    nlp = _load_spacy()
    if nlp and nlp.pipe_names:
        doc = nlp(text)
        entities = [ent.text.strip() for ent in doc.ents if ent.label_ in {"PERSON", "ORG", "GPE", "PRODUCT"}]
        if entities:
            return list(dict.fromkeys(entities))[:limit]

    words = [
        word.lower()
        for word in re.findall(r"[A-Za-z]{4,}", text)
        if word.lower() not in STOPWORDS
    ]
    return [word for word, _ in Counter(words).most_common(limit)]


def analyze_sentiment(text):
    if not _sentiment:
        return "Neutral", 0.0
    score = _sentiment.polarity_scores(text)["compound"]
    if score >= 0.05:
        return "Positive", score
    if score <= -0.05:
        return "Negative", score
    return "Neutral", score


def process_article(raw_text):
    text = clean_text(raw_text)
    sentiment, score = analyze_sentiment(text)
    return {
        "clean_text": text,
        "category": classify_topic(text),
        "sentiment": sentiment,
        "sentiment_score": score,
        "keywords": extract_keywords(text),
    }


def category_vector(category):
    return " ".join(CATEGORY_KEYWORDS.get(category, []))


def all_categories():
    return list(CATEGORIES)
