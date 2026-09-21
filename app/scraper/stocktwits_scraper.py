# app/scraper/stocktwits_scraper.py
import requests
import logging
from app.scraper.base import BaseScraper
from app.scraper.utils import clean_html

logger = logging.getLogger(__name__)

class StockTwitsScraper(BaseScraper):
    """Scrapes public StockTwits symbol streams. No auth required for read access."""

    BASE_URL = "https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"

    def __init__(self, symbols: list[str], limit_per_symbol: int = 30):
        self.symbols = symbols
        self.limit_per_symbol = limit_per_symbol

    def fetch(self) -> list[dict]:
        posts = []
        for symbol in self.symbols:
            url = self.BASE_URL.format(symbol=symbol)
            try:
                resp = requests.get(url, timeout=10, headers={"User-Agent": "news_analyzer_bot/1.0"})
                resp.raise_for_status()
                data = resp.json()
                messages = data.get("messages", [])[: self.limit_per_symbol]

                for msg in messages:
                    posts.append({
                        "title": f"${symbol} community post",
                        "url": f"https://stocktwits.com/message/{msg['id']}",
                        "source": f"stocktwits:{symbol}",
                        "source_type": "stocktwits",
                        "content": clean_html(msg.get("body", ""))
                    })
            except requests.exceptions.RequestException as e:
                logger.error(f"StockTwits fetch failed for {symbol}: {e}")
                continue
            except (KeyError, ValueError) as e:
                logger.error(f"StockTwits response parsing failed for {symbol}: {e}")
                continue
        return posts