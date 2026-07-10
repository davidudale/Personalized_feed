from contextlib import closing

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import CATEGORIES
from database import get_connection, get_user_profile
from nlp_pipeline import category_vector


def _article_text(article):
    fields = [
        article["title"] or "",
        article["summary"] or "",
        article["content"] or "",
        article["category"] or "",
        article["keywords"] or "",
    ]
    return " ".join(fields)


def recommend_articles(user_id, limit=30):
    with closing(get_connection()) as conn:
        articles = conn.execute(
            """
            SELECT *
            FROM articles
            WHERE id NOT IN (
                SELECT article_id FROM interactions
                WHERE user_id = %s AND action IN ('skip')
            )
            ORDER BY created_at DESC
            LIMIT 200
            """,
            (user_id,),
        ).fetchall()

    if not articles:
        return []

    profile = get_user_profile(user_id)
    profile_terms = []
    for category in CATEGORIES:
        weight = max(profile.get(category, 0), 0)
        profile_terms.extend([category_vector(category)] * int(weight + 1))

    user_document = " ".join(profile_terms) or " ".join(category_vector(category) for category in CATEGORIES)
    article_documents = [_article_text(article) for article in articles]
    vectors = TfidfVectorizer(stop_words="english").fit_transform([user_document] + article_documents)
    scores = cosine_similarity(vectors[0:1], vectors[1:]).flatten()

    ranked = []
    for article, score in zip(articles, scores):
        category_bonus = max(profile.get(article["category"], 0), 0) * 0.04
        ranked.append((dict(article), float(score + category_bonus)))

    ranked.sort(key=lambda item: item[1], reverse=True)
    return [{"article": article, "score": score} for article, score in ranked[:limit]]


def precision_at_k(recommendations, preferred_categories, k=10):
    top_k = recommendations[:k]
    if not top_k:
        return 0.0
    relevant = sum(1 for item in top_k if item["article"]["category"] in preferred_categories)
    return relevant / len(top_k)
