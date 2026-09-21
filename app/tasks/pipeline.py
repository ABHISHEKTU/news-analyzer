# app/tasks/pipeline.py
import logging
from app.core.celery_app import celery_app
from app.scraper.rss_scraper import RSSScraper
from app.scraper.stocktwits_scraper import StockTwitsScraper
from app.nlp.sentiment import analyze_news, analyze_social
from app.db.session import SessionLocal
from app.db.models import Article

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://www.moneycontrol.com/rss/economy.xml",
]

STOCKTWITS_SYMBOLS = ["AAPL", "TSLA", "NVDA"]

SENTIMENT_ROUTER = {
    "rss": analyze_news,
    "stocktwits": analyze_social,
}

def process_source(scraper, db, seen_urls: set) -> tuple[int, int]:
    """Fetch from one scraper, analyze, store. Returns (new_count, skipped_count)."""
    raw_items = scraper.fetch()
    new_count = 0
    skipped_count = 0

    for item in raw_items:
        url = item["url"]

        if url in seen_urls:
            skipped_count += 1
            continue

        exists = db.query(Article).filter_by(url=url).first()
        if exists:
            skipped_count += 1
            seen_urls.add(url)
            continue

        engine_fn = SENTIMENT_ROUTER.get(item["source_type"], analyze_news)
        sentiment = engine_fn(item["content"] or item["title"])

        article = Article(
            title=item["title"],
            url=url,
            source=item["source"],
            source_type=item["source_type"],
            content=item["content"],
            sentiment_label=sentiment["label"],
            sentiment_score=sentiment["score"],
            engine=sentiment["engine"],
        )
        db.add(article)
        seen_urls.add(url)
        new_count += 1

    return new_count, skipped_count

def run_pipeline_sync() -> dict:
    """Scrape all sources, analyze sentiment via router, store new items."""
    db = SessionLocal()
    total_new = 0
    total_skipped = 0
    seen_urls = set()  # tracks URLs across ALL sources in this run, prevents intra-batch dupes
    try:
        rss_scraper = RSSScraper(RSS_FEEDS)
        n, s = process_source(rss_scraper, db, seen_urls)
        total_new += n
        total_skipped += s

        st_scraper = StockTwitsScraper(STOCKTWITS_SYMBOLS, limit_per_symbol=20)
        n, s = process_source(st_scraper, db, seen_urls)
        total_new += n
        total_skipped += s

        db.commit()
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

    logger.info(f"Pipeline done: {total_new} new, {total_skipped} skipped (dupes)")
    return {"new_articles": total_new, "skipped": total_skipped}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_pipeline_task(self):
    try:
        return run_pipeline_sync()
    except Exception as exc:
        logger.error(f"Task failed, retrying: {exc}")
        raise self.retry(exc=exc)