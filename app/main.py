# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import router

app = FastAPI(title="Financial News Analyzer")

app.include_router(router, prefix="/api", tags=["news"])
app.mount("/dashboard", StaticFiles(directory="app/static", html=True), name="dashboard")

@app.get("/health")
def health_check():
    return {"status": "ok"}