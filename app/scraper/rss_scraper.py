# app/scraper/rss_scraper.py
import feedparser
import logging
from app.scraper.base import BaseScraper
from app.scraper.utils import clean_html

logger = logging.getLogger(__name__)

class RSSScraper(BaseScraper):
    def __init__(self, feed_urls: list[str]):
        self.feed_urls = feed_urls

    def fetch(self) -> list[dict]:
        articles = []
        for url in self.feed_urls:
            try:
                parsed = feedparser.parse(url)
                if parsed.bozo:
                    logger.warning(f"Feed parse issue: {url}")
                for entry in parsed.entries:
                    articles.append({
                        "title": clean_html(entry.get("title", "")),
                        "url": entry.get("link", ""),
                        "source": url,
                        "source_type": "rss",
                        "content": clean_html(entry.get("summary", ""))
                    })
            except Exception as e:
                logger.error(f"Failed fetching {url}: {e}")
                continue
        return articles