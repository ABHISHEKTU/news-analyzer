# app/api/routes.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Article
from app.api.schemas import ArticleOut
from app.tasks.pipeline import run_pipeline_task
from app.core.celery_app import celery_app
from app.reports.generator import generate_summary

router = APIRouter()

@router.post("/trigger-scan")
def trigger_scan():
    task = run_pipeline_task.delay()
    return {"task_id": task.id, "status": "queued"}

@router.get("/task-status/{task_id}")
def get_task_status(task_id: str):
    result = celery_app.AsyncResult(task_id)
    response = {"task_id": task_id, "status": result.status}
    if result.status == "SUCCESS":
        response["result"] = result.result
    elif result.status == "FAILURE":
        response["error"] = str(result.result)
    return response

@router.get("/articles", response_model=list[ArticleOut])
def get_articles(limit: int = 20, db: Session = Depends(get_db)):
    articles = db.query(Article).order_by(Article.scraped_at.desc()).limit(limit).all()
    return articles

@router.get("/report")
def get_report(db: Session = Depends(get_db)):
    return generate_summary(db)