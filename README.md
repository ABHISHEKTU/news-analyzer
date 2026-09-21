# 📊 Financial News Analyzer

A production-shaped, async financial sentiment analysis pipeline that scrapes news and social media, runs domain-appropriate sentiment models, and serves aggregated market mood scores via a REST API — built to demonstrate real backend engineering patterns, not just ML plumbing.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688)
![Celery](https://img.shields.io/badge/Celery-5.6-37814A)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![Postgres](https://img.shields.io/badge/Postgres-16-336791)

---

## Overview

Financial sentiment analysis tools usually make one mistake: they run a single model against every kind of text. Formal news headlines and informal trading-community chatter carry sentiment very differently — this project routes each source to the model suited for it, then combines the results into a single weighted market mood signal.

The system runs as five containerized services (API, worker, scheduler, message broker, database), scrapes two live sources on a recurring schedule, analyzes sentiment through a hybrid FinBERT/VADER pipeline, and exposes everything through a documented REST API.

---

## Architecture

┌─────────────┐ ┌──────────────┐ ┌─────────────────┐
│ RSS Feeds │ │ StockTwits │ │ (extensible │
│ (Moneycontrol│ │ Public API │ │ to more sources)│
│ /Economy) │ │ │ │ │
└──────┬───────┘ └──────┬───────┘ └──────────────────┘
│ │
└──────────┬──────────┘
▼
┌─────────────────┐
│ Scraper Layer │ (per-source error isolation,
│ (base + impls) │ HTML/entity cleaning)
└────────┬─────────┘
▼
┌──────────────────────┐
│ Sentiment Router │
│ ┌─────────┐ ┌──────┐ │
│ │ FinBERT │ │VADER │ │ news → FinBERT (formal text)
│ │ (news) │ │(social)│ social → VADER (informal text)
│ └─────────┘ └──────┘ │
└──────────┬────────────┘
▼
┌───────────────────────┐
│ PostgreSQL Storage │ (URL-unique, dedupe-safe,
│ (Article table) │ intra-batch + cross-run)
└──────────┬─────────────┘
│
┌──────────────┼──────────────┐
▼ ▼ ▼
┌─────────────┐ ┌───────────┐ ┌──────────────┐
│ Celery Beat │ │ Celery │ │ FastAPI │
│ (scheduler, │ │ Worker │ │ (REST API) │
│ every 30m) │ │ (executes │ │ │
│ │ │ via Redis│ │ /trigger-scan│
│ │ │ queue) │ │ /task-status │
│ │ │ │ │ /articles │
│ │ │ │ │ /report │
└─────────────┘ └───────────┘ └──────────────┘


**Flow**: Beat schedules a scan every 30 minutes → dispatches a task to Redis → a Celery worker picks it up → scrapes both sources → routes each item through the correct sentiment engine → deduplicates and stores in Postgres → results are queryable instantly via the API, with a weighted aggregate mood score computed on demand.

---

## Why hybrid sentiment routing?

Financial news headlines ("Company beats quarterly earnings estimates") and trading-community posts ("bagholders in shambles 📉") are different languages. A single general-purpose model handles neither well.

| Source | Model | Why |
|---|---|---|
| RSS news (Moneycontrol) | **FinBERT** | Transformer fine-tuned on financial text; understands domain terms like "guidance cut," "beat expectations" |
| StockTwits posts | **VADER** | Lexicon-based, built for informal/social text; handles emphasis, punctuation, emoji — but misses finance-specific slang |

FinBERT falls back to VADER automatically if the model fails to load, so a single point of failure never takes down the whole pipeline. Each stored article records which engine scored it (`engine` field), so results stay auditable.

**Aggregation**: news sentiment is weighted 65%, social sentiment 35%, in the combined market mood score — reflecting that formal reporting is a more reliable signal than informal chatter, while still capturing real-time crowd sentiment.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| API | FastAPI | Async REST endpoints, auto-generated OpenAPI docs |
| Task Queue | Celery + Redis | Background job execution, retry logic |
| Scheduler | Celery Beat | Recurring automated scans |
| Database | PostgreSQL (SQLite for local dev) | Persistent, dedupe-safe article storage |
| ORM | SQLAlchemy 2.0 | Data modeling and queries |
| NLP | FinBERT (transformers) + VADER | Domain-routed sentiment analysis |
| Scraping | feedparser, requests, BeautifulSoup | RSS parsing, HTTP API calls, HTML cleaning |
| Containerization | Docker + Docker Compose | Multi-service orchestration |
| Config | Pydantic Settings | Environment-based configuration |

---

## Project Structure

news_analyzer/
├── app/
│ ├── main.py # FastAPI app entrypoint
│ ├── api/
│ │ ├── routes.py # REST endpoints
│ │ └── schemas.py # Pydantic response models
│ ├── core/
│ │ ├── config.py # Centralized settings (env-driven)
│ │ └── celery_app.py # Celery configuration + beat schedule
│ ├── scraper/
│ │ ├── base.py # Abstract scraper interface
│ │ ├── rss_scraper.py # RSS feed scraper
│ │ ├── stocktwits_scraper.py # StockTwits public API scraper
│ │ └── utils.py # Shared HTML/entity cleaning
│ ├── nlp/
│ │ └── sentiment.py # FinBERT + VADER, routing logic
│ ├── db/
│ │ ├── models.py # SQLAlchemy models
│ │ └── session.py # DB engine/session management
│ ├── tasks/
│ │ └── pipeline.py # Celery task: scrape → analyze → store
│ └── reports/
│ └── generator.py # Sentiment aggregation logic
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env # Local config (not committed)


---

## Getting Started

### Prerequisites
- Docker Desktop
- (For local dev without Docker) Python 3.12+

### Run with Docker Compose (recommended)

```bash
git clone https://github.com/ABHISHEKTU/news-analyzer.git
cd news-analyzer
docker compose up --build
```

This starts all five services: `api` (port 8000), `worker`, `beat`, `redis` (port 6379), and `db` (Postgres, port 5432).

Once running, open **http://localhost:8000/docs** for interactive API documentation.

### Local development (without Docker)

```bash
python -m venv venv
venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt

# Terminal 1
uvicorn app.main:app --reload

# Terminal 2 (requires local Redis, e.g. via `docker run -d -p 6379:6379 redis`)
celery -A app.core.celery_app worker --loglevel=info --pool=solo   # --pool=solo required on Windows

# Terminal 3
celery -A app.core.celery_app beat --loglevel=info
```

Local dev defaults to SQLite (`news.db`) via `.env`; Docker Compose overrides this to Postgres automatically.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/trigger-scan` | Queue a scrape+analyze job, returns immediately with a `task_id` |
| `GET` | `/api/task-status/{task_id}` | Poll async task status/result |
| `GET` | `/api/articles?limit=20` | List stored articles with sentiment scores |
| `GET` | `/api/report` | Aggregated sentiment report (news/social/combined mood) |

**Example: trigger a scan and check status**

```bash
curl -X POST http://localhost:8000/api/trigger-scan
# {"task_id": "...", "status": "queued"}

curl http://localhost:8000/api/task-status/<task_id>
# {"task_id": "...", "status": "SUCCESS", "result": {"new_articles": 19, "skipped": 0}}
```

**Example: get the aggregated report**

```json
{
  "total_articles": 39,
  "news_sentiment": 0.2326,
  "social_sentiment": 0.0881,
  "combined_market_mood": 0.182,
  "news_count": 19,
  "social_count": 20
}
```

---

## Engineering Decisions & Challenges Solved

This project was built incrementally with real debugging at every layer — not scaffolded and hoped-for. A few notable problems and how they were resolved:

- **Broken HTML entities in RSS feeds**: Moneycontrol's feed occasionally drops the leading `&` from numeric entities (`company#39;s` instead of `company&#39;s`). Standard `html.unescape()` doesn't catch this — added a regex-based patch for malformed entity patterns.

- **Intra-batch duplicate key violations**: A single StockTwits post can mention multiple tickers ($AAPL $NVDA $TSLA), so it appears in multiple symbol streams within the same scrape run. The database-based dedupe check doesn't see uncommitted rows from earlier in the same transaction, causing a `UNIQUE constraint` failure. Fixed with an in-memory `seen_urls` set scoped to each pipeline run, checked alongside the DB query.

- **Postgres sequence race condition**: When `api`, `worker`, and `beat` containers all start simultaneously and each calls `Base.metadata.create_all()`, they can race on creating the same auto-increment sequence, causing a startup crash. Wrapped table creation in a try/except that treats "already exists" as expected, not fatal.

- **Third-party API resilience**: StockTwits occasionally returns timeouts or 403s in containerized environments. Per-source error isolation ensures one failing source degrades gracefully rather than crashing the whole pipeline — RSS data still lands even if StockTwits is unavailable.

- **CPU-only PyTorch for Docker**: Default `torch` installs full CUDA libraries even without GPU access, bloating the image by several GB and dramatically slowing builds. Switched to PyTorch's CPU-only wheel index, cutting install size and time significantly.

- **Windows/Linux Celery pool differences**: Celery's default `prefork` worker pool doesn't work on native Windows, requiring `--pool=solo` for local dev — but works normally inside the Linux-based Docker container, so the containerized deployment uses the default pool.

---

## Known Limitations & Future Improvements

- **Duplicate content detection**: currently dedupes by URL only; republished stories under new URLs aren't caught. A content-hash-based dedupe (title + body) would catch this.
- **StockTwits access**: public endpoint access can be inconsistent (rate limits, occasional blocks) — a production version would add exponential backoff and possibly an authenticated API tier.
- **Single-region news source**: currently limited to Indian financial news (Moneycontrol); easily extensible via the `BaseScraper` interface to add more feeds.
- **No authentication**: API is fully open — a production deployment would add API key or OAuth protection.
- **Non-root container user**: current Dockerfile runs as root; a hardened version would create a dedicated non-root user.

---

## License

MIT