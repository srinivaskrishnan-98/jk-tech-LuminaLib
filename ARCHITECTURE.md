# LuminaLib - Architecture Document

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Client (HTTP)                                                │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│  API Layer (FastAPI Routers)                                  │
│  - Thin controllers: validation, deserialization, delegation  │
│  - No business logic                                          │
│  auth.py │ books.py │ reviews.py │ recommendations.py         │
└──────────────────────────┬───────────────────────────────────┘
                           │ Depends()
┌──────────────────────────▼───────────────────────────────────┐
│  Service Layer                                                │
│  - All business logic, rules, orchestration                   │
│  auth_service │ book_service │ borrow_service                 │
│  review_service │ recommendation_service                      │
└──────┬───────────────────┬───────────────────┬───────────────┘
       │                   │                   │
┌──────▼──────┐   ┌────────▼────────┐   ┌─────▼──────┐
│ Repositories│   │   Interfaces    │   │  Workers   │
│ (DB access) │   │ (Abstract ABCs) │   │ (Async BG) │
└──────┬──────┘   └────────┬────────┘   └────────────┘
       │                   │
┌──────▼──────┐   ┌────────▼────────────────────────┐
│ PostgreSQL  │   │  Infrastructure (Adapters)       │
│ (asyncpg)   │   │  ├─ storage/ (MinIO │ Local)    │
│             │   │  ├─ llm/ (Ollama │ Mock)        │
│             │   │  └─ text_extraction/ (pdfplumber)│
└─────────────┘   └────────────────────────────────┘
```

## Design Principles

### 1. Clean Architecture (Controller → Service → Repository)

The codebase follows strict layered architecture:

- **API Layer** (`app/api/`): Thin controllers that handle HTTP concerns (request parsing, response serialization, status codes). Zero business logic. Each endpoint delegates to a service method.

- **Service Layer** (`app/services/`): Contains all business rules and orchestration. For example, `ReviewService.submit_review()` enforces that the user must have borrowed the book before reviewing it. Services never import from `app/api/`.

- **Repository Layer** (`app/repositories/`): Pure data access. Each repository wraps SQLAlchemy queries for a specific model. Repositories never contain business logic — they don't know about borrowing rules or file uploads.

### 2. Dependency Injection and Interface-Driven Development

The system uses two key abstractions defined in `app/interfaces/`:

**`StorageBackend` (ABC)**
```
upload_file() | download_file() | delete_file() | file_exists()
```
Implementations: `MinIOStorage`, `LocalStorage`

**`LLMProvider` (ABC)**
```
generate_summary() | analyze_sentiment() | generate_review_consensus()
```
Implementations: `OllamaProvider`, `MockLLMProvider`

**Swapping is config-driven.** Factory functions in `app/infrastructure/*/factory.py` read the `STORAGE_BACKEND` and `LLM_PROVIDER` environment variables and instantiate the correct class. FastAPI's `Depends()` injects the resolved instance into services. To swap MinIO for local disk storage:

```env
STORAGE_BACKEND=local  # was: minio
```

No code changes. No redeployment. Just restart.

## Database Schema Design

### User Preferences Model (Hybrid Approach)

The `user_preferences` table uses a **hybrid explicit + implicit** model:

| Column | Type | Purpose |
|--------|------|---------|
| `preferred_genres` | JSONB | **Explicit**: User-set during signup/profile update |
| `preferred_authors` | JSONB | **Explicit**: User-set during signup/profile update |
| `genre_weights` | JSONB | **Implicit**: Auto-computed from borrow history + ratings |

**Why this design?**

1. **Explicit preferences** capture what users say they want. This is a strong prior, especially for new users with no borrow history (cold-start problem).

2. **Implicit genre_weights** capture what users actually do. Every time a user borrows a book, the weight for that book's genre increases. Reviews with higher ratings boost the weight further. This creates a continuously-evolving preference vector.

3. **The recommendation engine combines both signals**, weighting explicit preferences as a boost on top of the implicit behavior-based profile.

**Why JSONB instead of a join table?** The genre taxonomy is bounded (~20-50 genres). JSONB avoids join overhead, makes the preference vector directly usable for computation (no aggregation query needed), and PostgreSQL's GIN indexing supports JSONB if querying is needed later.

### Borrow Tracking

The `borrows` table uses a relation table (not a boolean flag) with composite indexing:

```
borrows: (id, user_id, book_id, borrowed_at, returned_at, is_active)
Index: ix_borrows_user_book_active ON (user_id, book_id, is_active)
```

This design provides:
- Full audit trail of all borrow/return events
- Fast lookup of "does user X currently have book Y?" via the composite index
- Support for multiple copies via `available_copies` denormalization on the `books` table
- Race condition prevention via `SELECT FOR UPDATE` when decrementing copies

### Review Constraints

- `UNIQUE(user_id, book_id)`: One review per user per book (DB-level enforcement)
- Business rule: Only users who have ever borrowed the book can review it (service-level enforcement via `BorrowRepository.has_ever_borrowed()`)

## Async Strategy: Background Processing

### Why FastAPI BackgroundTasks (not Celery)

The system uses FastAPI's built-in `BackgroundTasks` for async LLM operations:

1. **Book Upload → Async Summarization**
   - `POST /books` returns immediately with `summary_status: "pending"`
   - Background task: Download file → Extract text (pdfplumber) → LLM summary → Update DB
   - Status progression: `pending → processing → completed` (or `failed`)

2. **Review Submission → Async Consensus Update**
   - `POST /books/{id}/reviews` returns immediately
   - Background task: Fetch all reviews → LLM sentiment analysis → Update consensus

**Why not Celery?** The requirement is `docker-compose up --build` starts everything. Celery requires Redis/RabbitMQ + a separate worker container. BackgroundTasks keeps the topology to 3-4 containers. The workload (LLM API calls) is I/O-bound, not CPU-bound, so in-process background tasks are appropriate.

**Error handling:** Workers catch all exceptions, log them with structlog, and update status fields (`summary_status = "failed"`) so the failure is visible to API consumers.

### Pipeline Flow

```
Book Upload                          Review Submission
     │                                      │
     ▼                                      ▼
summary_status = "pending"           Submit review to DB
     │                                      │
     ▼ [Background]                         ▼ [Background]
Download file from MinIO             Fetch all book reviews
     │                                      │
     ▼                                      ▼
Extract text (pdfplumber)            Analyze each review sentiment
     │                                      │
     ▼                                      ▼
LLM generate_summary()              LLM generate_review_consensus()
     │                                      │
     ▼                                      ▼
summary_status = "completed"         Update book.review_consensus
```

## ML Recommendation Strategy

### Algorithm: Content-Based Filtering with TF-IDF

**Why content-based over collaborative filtering?**
- Library systems may have few users initially → cold-start problem for collaborative filtering
- Books have rich textual metadata (genre, author, description) ideal for TF-IDF
- The hybrid preference model maps directly to a user profile vector

### How It Works

1. **Feature Engineering**: Each book gets a feature string: `"{genre} {genre} {genre} {author} {author} {description}"`. Genre and author are repeated to increase their weight.

2. **TF-IDF Vectorization**: scikit-learn's `TfidfVectorizer` converts feature strings to sparse vectors. This captures term importance across the book catalog.

3. **User Profile Construction**:
   - **With history**: Average the TF-IDF vectors of all borrowed books, weighted by review ratings (higher ratings = more influence).
   - **Without history but with preferences**: Transform explicit `preferred_genres` and `preferred_authors` into a TF-IDF vector as a pseudo-profile.
   - **Truly cold**: Fall back to highly-rated/popular books.

4. **Preference Boosting**: The user profile vector is boosted by explicit preferences (genres × 0.3, authors × 0.2) to blend stated intent with observed behavior.

5. **Ranking**: Cosine similarity between the user profile vector and all unread book vectors. Already-borrowed books are excluded. Top-N returned.

### Implicit Preference Updates

The `genre_weights` field in `user_preferences` is automatically updated when:
- User borrows a book (genre weight += 1.0)
- User returns a book with a review (weight boosted by rating/3.0)

This happens in `RecommendationService.update_implicit_preferences()`, called from `BorrowService.borrow_book()`.

## Prompt Engineering Strategy

LLM prompts are defined as structured templates in each provider:

- **Summarization prompt**: Instructs the LLM to focus on main themes, key arguments, and takeaways within a word limit.
- **Sentiment prompt**: Requests JSON output with `score` (0.0-1.0) and `label` (positive/negative/neutral).
- **Consensus prompt**: Synthesizes multiple reviews into overall impression, praise points, criticisms, and target audience.

Prompts are co-located with their provider implementations (not scattered across services), making them easy to test and modify independently.

## Configuration-Driven Architecture

All configuration lives in `.env` and is loaded via Pydantic `BaseSettings`:

```python
class Settings(BaseSettings):
    STORAGE_BACKEND: str = "minio"   # "minio" | "local"
    LLM_PROVIDER: str = "mock"       # "ollama" | "mock"
    DATABASE_URL: str = "..."
    JWT_SECRET_KEY: str = "..."
```

No hardcoded values exist in application code. Every external URL, credential, and behavior toggle is configurable.
