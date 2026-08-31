from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config import CATEGORIES, SECRET_KEY
from database import get_connection, init_db
from news_fetcher import fetch_rss_articles
from nlp_pipeline import process_article
from recommender import precision_at_k, recommend_articles


app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


@app.before_request
def bootstrap_database():
    init_db()
    with get_connection() as conn:
        conn.execute("DELETE FROM articles WHERE published = 'Sample data'")
        conn.commit()
        existing = conn.execute("SELECT COUNT(*) AS count FROM articles").fetchone()["count"]
        if not existing:
            try:
                fetch_rss_articles(limit_per_feed=6, fetch_full_text=False)
            except Exception:
                pass


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("feed"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        preferences = ",".join(request.form.getlist("preferences"))
        with get_connection() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO users (name, email, password_hash, preferences)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (name, email, generate_password_hash(password), preferences),
                )
                user_id = cursor.fetchone()["id"]
                conn.commit()
            except Exception:
                flash("That email address is already registered.", "danger")
                return render_template("register.html", categories=CATEGORIES)
        session["user_id"] = user_id
        session["name"] = name
        flash("Account created. Your personalized feed is ready.", "success")
        return redirect(url_for("feed"))
    return render_template("register.html", categories=CATEGORIES)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        with get_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE email = %s", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            return redirect(url_for("feed"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/feed")
@login_required
def feed():
    recommendations = recommend_articles(session["user_id"])
    with get_connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],)).fetchone()
    preferred = [item for item in user["preferences"].split(",") if item]
    score = precision_at_k(recommendations, set(preferred), k=10)
    return render_template("feed.html", recommendations=recommendations, precision=score, preferences=preferred)


@app.route("/categories/<category>")
@login_required
def category(category):
    with get_connection() as conn:
        articles = conn.execute(
            "SELECT * FROM articles WHERE category = %s ORDER BY created_at DESC LIMIT 50",
            (category,),
        ).fetchall()
    return render_template("category.html", category=category, articles=articles, categories=CATEGORIES)


@app.route("/preferences", methods=["GET", "POST"])
@login_required
def preferences():
    with get_connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],)).fetchone()
        if request.method == "POST":
            selected = ",".join(request.form.getlist("preferences"))
            conn.execute("UPDATE users SET preferences = %s WHERE id = %s", (selected, session["user_id"]))
            conn.commit()
            flash("Preferences updated.", "success")
            return redirect(url_for("feed"))
    selected = set(user["preferences"].split(","))
    return render_template("preferences.html", categories=CATEGORIES, selected=selected)


@app.route("/interact/<int:article_id>/<action>", methods=["POST"])
@login_required
def interact(article_id, action):
    if action not in {"view", "like", "save", "skip"}:
        flash("Unknown action.", "danger")
        return redirect(url_for("feed"))
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO interactions (user_id, article_id, action) VALUES (%s, %s, %s)",
            (session["user_id"], article_id, action),
        )
        conn.commit()
    flash(f"Article marked as {action}.", "success")
    return redirect(request.referrer or url_for("feed"))


@app.route("/refresh", methods=["POST"])
@login_required
def refresh():
    try:
        count = fetch_rss_articles(limit_per_feed=6, fetch_full_text=False)
        flash(f"Fetched {count} new articles from RSS feeds.", "success")
    except Exception as exc:
        flash(f"Could not refresh RSS feeds: {exc}", "danger")
    return redirect(url_for("feed"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
