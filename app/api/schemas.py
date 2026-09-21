# app/api/schemas.py
from pydantic import BaseModel
from datetime import datetime

class ArticleOut(BaseModel):
    id: int
    title: str
    url: str
    source: str
    source_type: str
    engine: str | None
    sentiment_label: str | None
    sentiment_score: float | None
    scraped_at: datetime

    class Config:
        from_attributes = True