# app/main.py
from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Financial News Analyzer")

app.include_router(router, prefix="/api", tags=["news"])

@app.get("/health")
def health_check():
    return {"status": "ok"}