# app/nlp/sentiment.py
from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

SENTIMENT_MODEL = "ProsusAI/finbert"

@lru_cache(maxsize=1)
def get_finbert():
    logger.info("Loading FinBERT model (first call only)...")
    return pipeline("sentiment-analysis", model=SENTIMENT_MODEL)

@lru_cache(maxsize=1)
def get_vader():
    return SentimentIntensityAnalyzer()

def analyze_social(text: str) -> dict:
    """VADER — for informal/social text (StockTwits, tweets, etc)."""
    if not text or not text.strip():
        return {"label": "NEUTRAL", "score": 0.0, "engine": "vader"}
    try:
        vs = get_vader()
        compound = vs.polarity_scores(text)["compound"]
        if compound >= 0.05:
            label = "POSITIVE"
        elif compound <= -0.05:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"
        return {"label": label, "score": round(abs(compound), 4), "engine": "vader"}
    except Exception as e:
        logger.error(f"VADER failed: {e}")
        return {"label": "ERROR", "score": 0.0, "engine": "vader"}

def analyze_news(text: str) -> dict:
    """FinBERT — for formal financial news text. Falls back to VADER if model fails."""
    if not text or not text.strip():
        return {"label": "NEUTRAL", "score": 0.0, "engine": "finbert"}
    try:
        clf = get_finbert()
        result = clf(text[:512])[0]
        return {"label": result["label"].upper(), "score": round(result["score"], 4), "engine": "finbert"}
    except Exception as e:
        logger.warning(f"FinBERT failed: {e}, falling back to VADER")
        return analyze_social(text)