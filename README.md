


# 🍷 Wine API – FastAPI backend for interactive wine-data exploration

A production-ready FastAPI service that powers the WT2 – Wine Explorer web app.
It loads 130k Wine Enthusiast reviews, exposes rich REST endpoints, and adds a Retrieval-Augmented Generation (RAG) layer for natural-language Q&A.

🚀 Live demo:
API root: https://angelicamarker.online/wt2
Docs: https://angelicamarker.online/wt2/docs#/

---

## ✨ Key Features

| Category | Highlights |
|----------|------------|
| **REST API** | CRUD-style endpoints for wines, country stats, price/score buckets, etc. |
| **Search** | • `/api/wines/search` → PostgreSQL **tsvector** full-text search<br>• `/api/search` (+ `/answer`) → **Chroma + LangChain + OpenAI** vector search & RAG |
| **Performance** | 7 carefully chosen indexes (BTREE, composite, GIN) ensure sub-100 ms queries even on a modest VM |
| **Clean Code** | Pydantic v2 schemas, SQLAlchemy 2.x, service layer, strict Pyright & Pylint |
| **CI / CD** | GitHub Actions lints & zero-downtime Docker deploy to VPS |
| **Container-first** | Single-image `Dockerfile`; optional `docker-compose.yml` for local Postgres & Chroma |
| **Extensible** | Typed service layer, SOLID structure, room for Redis caching & Pytest suite |

---

## 🗂️ Project Structure
```

.
├── app/                 # FastAPI application
│   ├── api/endpoints    # Routers (wines, stats, search, …)
│   ├── services         # Business-logic layer
│   ├── db               # SQLAlchemy engine / session
│   ├── models           # ORM models
│   └── schemas          # Pydantic DTOs
├── Dockerfile           # Production image
├── docker-compose.yml   # Dev stack (API + Postgres)
└── embed\_wines.py       # One-off script: embed reviews → Chroma
```

---

## 🛠️ Tech Stack

* **Python 3.11**, **FastAPI 0.115**
* **PostgreSQL 15** (primary store)  
* **SQLAlchemy 2** + Pydantic v2 for type-safe data access
* **Chroma DB** as local vector store (volumized in production)
* **LangChain + OpenAI GPT-4-Turbo** for RAG search
* **Docker / GitHub Actions** for repeatable builds & deploys

---

## 🗄️ Chroma Setup (Production)

To persist ChromaDB **across container rebuilds**, the Docker container mounts:

```bash
-v /var/lib/wt2-chroma:/app/chroma_db
```

This ensures:

- 🔒 **Durability:** embeddings stay intact even after container restarts.
    
- 📦 **One-time setup:** you only need to build embeddings ONCE on the VPS.
    

### First-time: embed wine reviews on VPS

After deploying, SSH into your VPS and run:

```bash
docker exec -it wt2-api python embed_wines.py
```

This script:

- Loads all 130k wine reviews from PostgreSQL
    
- Embeds them via `SentenceTransformers`
    
- Populates ChromaDB at `/var/lib/wt2-chroma` (on VPS disk)
    

✅ Future deploys **reuse the existing Chroma data automatically.**

---

## 🗄️ Database Schema & Indexing

The single table **`kaggle_wine_reviews`** holds ~130 000 rows. Key columns:

| Column | Type | Notes |
|--------|------|-------|
| `id` | `SERIAL` PK | primary key |
| `description` | `TEXT` | review text |
| `price` | `NUMERIC(10,2)` | USD |
| `points` | `INTEGER` | 80–100 |
| `country`, `variety`, … | `TEXT` | categorical filters |
| `search_vector` | `TSVECTOR` | generated column for FTS |

### Current Indexes (7)

| Name | Columns | Type | Purpose |
|------|---------|------|---------|
| `kaggle_wine_reviews_pkey` | `id` | **UNIQUE btree** | PK lookups |
| `idx_wine_price` | `price` | BTREE | price slider |
| `idx_wine_points` | `points` | BTREE | score filter |
| `idx_wine_country` | `country` | BTREE | choropleth map |
| `idx_wine_variety` | `variety` | BTREE | dropdown filter |
| `idx_wine_price_points` | `price, points` | **Composite btree** | price-vs-points scatter |
| `idx_kaggle_wine_reviews_search_vector` | `search_vector` | **GIN** | full-text search |

> These cover all hot paths: simple filters, combined price + points queries, and GIN-powered full-text look-ups.

---

## 🔍 Search Capabilities

1. **Full-text search**  
   `POST /api/wines/search`  
   Uses `search_vector.match(<query>, 'english')` under the hood for instant keyword search across descriptions and titles. Results support pagination & secondary filters (country, variety, price/points ranges). 

2. **Semantic RAG search**  
   `POST /api/search` → returns top k snippets  
   `POST /api/search/answer` → streams an AI-crafted answer citing the same snippets.  
   Pipeline: review ➜ `Sentence-Transformer` embedding ➜ Chroma ➜ similarity search ➜ GPT-4-Turbo answer. 
---

## 📑  Core API Reference (v0 / wt2 prefix omitted)

| Method & Path | Description | Auth |
|---------------|-------------|------|
| `GET  /api/wines` | Paginated list (query: `page`, `size`) | – |
| `GET  /api/wines/{id}` | Single wine by ID | – |
| `POST /api/wines/search` | Keyword + structured filters search | – |
| `GET  /api/stats/countries` | Aggregated per-country metrics | – |
| `GET  /api/stats/price-rating` | Raw points-vs-price datapoints | – |
| `GET  /api/stats/price-rating-aggregated` | Bucketed heat-map for scatter | – |
| `POST /api/search` | Vector similarity search (RAG) | – |
| `POST /api/search/answer` | LLM answer using retrieved docs | – |

See the **OpenAPI /docs** route for the full contract – FastAPI autogenerates it at runtime.

---

## 🚀  Getting Started

### 1. Clone & Configure
```bash
git clone https://github.com/MarkerAnn/wine_backend.git
cd wine_backend
cp .env.example .env   # then fill in secrets
````

### 2. One-command dev stack

````bash
docker compose up --build
# API -> http://localhost:8001/wt2
# Swagger -> http://localhost:8001/wt2/docs
````


**Postgres** and **Chroma** volumes persist under `./data/` by default.

### 3. Manual (venv) run

````bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
````

---

## ⚙️  Required Environment Variables

| Key               | Example                                                       | Purpose                   |
| ----------------- | ------------------------------------------------------------- | ------------------------- |
| `DATABASE_URL`    | `postgresql+psycopg2://user:pw@localhost:5432/wine_review_db` | SQL source                |
| `OPENAI_API_KEY`  | `sk-…`                                                        | GPT-4-Turbo access        |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2`                                            | SBERT name                |
| `VECTORSTORE_DIR` | `chroma_db`                                                   | Chroma persistence folder |

---

## 🧪 Testing

* **Planned**: Pytest suite with a disposable Postgres container (`pytest-postgres`) and Faker data factories.
* CI step already exists – extend `ci-cd.yml` with `pytest -q`.

---


## 🔄 CI/CD Flow (GitHub Actions)

- **On push to `main`:**
    
    - Lints code (Pylint)
        
    - SSH into VPS
        
    - Pulls latest code
        
    - Stops old container
        
    - Rebuilds & starts Docker with volume mount for Chroma:
        

````bash
docker run -d --name wt2-api \
    -p 8000:5000 \
    --restart unless-stopped \
    --env-file .env \
    -v /var/lib/wt2-chroma:/app/chroma_db \
    wt2-api
````

✅ Embeddings stay safe across deployments.

---

## ➡️  Roadmap / Future Improvements

1. **Redis cache** – memoise hot endpoints (e.g., country stats) to cut DB latency.
2. **Test coverage ≥ 90 %** – unit & integration layers.
3. **JWT Auth** – protect write endpoints & RAG cost.
4. **OpenTelemetry** traces → Grafana dashboards.

---


## 📄  License

Released under the MIT License — see [`LICENSE`](./LICENSE) for details.



---

