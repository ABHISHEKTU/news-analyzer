# app/db/models.py
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    source = Column(String)
    source_type = Column(String, default="rss")
    engine = Column(String, nullable=True)
    content = Column(Text)
    sentiment_label = Column(String, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    scraped_at = Column(DateTime, default=datetime.datetime.utcnow)