# app/scraper/base.py
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    @abstractmethod
    def fetch(self) -> list[dict]:
        """Return list of dicts: title, url, source, content"""
        ...