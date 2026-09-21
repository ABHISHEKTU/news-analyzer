# app/reports/generator.py
from sqlalchemy.orm import Session
from app.db.models import Article

def generate_summary(db: Session) -> dict:
    """Aggregate sentiment across sources into a weighted market mood score."""
    articles = db.query(Article).all()

    if not articles:
        return {
            "total_articles": 0,
            "news_sentiment": 0.0,
            "social_sentiment": 0.0,
            "combined_market_mood": 0.0,
            "news_count": 0,
            "social_count": 0,
        }

    news_items = [a for a in articles if a.source_type == "rss"]
    social_items = [a for a in articles if a.source_type == "stocktwits"]

    def signed_avg(items: list[Article]) -> float:
        """Average sentiment as signed score: +score for positive, -score for negative, 0 for neutral."""
        signed_scores = []
        for a in items:
            label = (a.sentiment_label or "").upper()
            if label == "POSITIVE":
                signed_scores.append(a.sentiment_score or 0.0)
            elif label == "NEGATIVE":
                signed_scores.append(-(a.sentiment_score or 0.0))
            elif label == "NEUTRAL":
                signed_scores.append(0.0)
            # ERROR-labeled rows excluded entirely — don't let failed analyses skew the average
        return round(sum(signed_scores) / len(signed_scores), 4) if signed_scores else 0.0

    news_score = signed_avg(news_items)
    social_score = signed_avg(social_items)

    # weighted blend: news considered more reliable signal than informal social chatter
    NEWS_WEIGHT = 0.65
    SOCIAL_WEIGHT = 0.35
    combined = round(NEWS_WEIGHT * news_score + SOCIAL_WEIGHT * social_score, 4)

    return {
        "total_articles": len(articles),
        "news_sentiment": news_score,
        "social_sentiment": social_score,
        "combined_market_mood": combined,
        "news_count": len(news_items),
        "social_count": len(social_items),
    }