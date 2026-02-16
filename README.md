# LuminaLib - Intelligent Library System

An intelligent library management system with GenAI-powered book summarization, sentiment analysis, and ML-based recommendations. Built with FastAPI, PostgreSQL, MinIO, and Docker.

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- No other local setup required

### One-Command Start

```bash
# Clone the repository
git clone <repository-url>
cd jk-tech-LuminaLib

# Start all services
docker compose up --build
```

This single command starts:
- **API** at `http://localhost:8000` (FastAPI with auto-docs at `/docs`)
- **PostgreSQL** at `localhost:5432`
- **MinIO** at `localhost:9000` (console at `localhost:9001`)
- **Ollama LLM** at `localhost:11434` (when using --profile llm)
- Database migrations run automatically on startup

### Using Real LLM (Ollama)

The system is configured to use Ollama by default (`LLM_PROVIDER=ollama` in `.env`). Ollama starts automatically with all other services.

```bash
# Start all services (including Ollama)
docker compose up --build

# The ollama-pull service automatically downloads llama3.2 on first start
# Check if model is downloaded:
docker compose exec ollama ollama list
```

**To use mock LLM instead** (for testing without AI):
- Set `LLM_PROVIDER=mock` in `.env`
- Restart API: `docker compose restart api`

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive Swagger UI.

### Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/signup` | No | Register a new user |
| POST | `/auth/login` | No | Login and get JWT token |
| POST | `/auth/signout` | Yes | Revoke current token |
| GET | `/auth/profile` | Yes | Get user profile |
| PUT | `/auth/profile` | Yes | Update profile & preferences |
| POST | `/books` | Yes | Upload book file + metadata |
| GET | `/books` | Yes | List books (paginated) |
| GET | `/books/{id}` | Yes | Get book details |
| PUT | `/books/{id}` | Yes | Update book metadata |
| DELETE | `/books/{id}` | Yes | Delete book and file |
| POST | `/books/{id}/borrow` | Yes | Borrow a book |
| POST | `/books/{id}/return` | Yes | Return a book |
| POST | `/books/{id}/reviews` | Yes | Submit review (must have borrowed) |
| GET | `/books/{id}/analysis` | Yes | Get AI review analysis |
| GET | `/recommendations` | Yes | Get ML-based suggestions |

### Authentication Flow

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"reader","password":"SecurePass123","preferred_genres":["Fiction","Science"]}'

# 2. Login (use email as username in form)
curl -X POST http://localhost:8000/auth/login \
  -d "username=user@example.com&password=SecurePass123"

# 3. Use the token
export TOKEN="<access_token from step 2>"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/books
```

### Book Upload Example

```bash
curl -X POST http://localhost:8000/books \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@mybook.pdf" \
  -F "title=The Great Book" \
  -F "author=Jane Author" \
  -F "genre=Fiction" \
  -F "description=A wonderful story"
```

The API returns immediately with `summary_status: "pending"`. The summary is generated asynchronously in the background.

## API Testing with Postman

A comprehensive Postman collection is included at `LuminaLib.postman_collection.json` with all API endpoints pre-configured.

### Import the Collection

1. Open Postman
2. Click **Import** → Select `LuminaLib.postman_collection.json`
3. The collection includes folders for:
   - Authentication (signup, login, profile)
   - Books (upload, list, get, update, delete)
   - Library Operations (borrow, return, reviews)
   - Recommendations & Analysis

### Using the Collection

1. **Sign up** or **Login** using the Auth folder
2. The access token is automatically saved to collection variables
3. All subsequent requests use the token automatically
4. No manual header setup needed!

**Note**: Update the `baseUrl` variable in collection settings if not using `http://localhost:8000`.

## Loading Sample Data

### Option 1: Quick Test Data (Mock LLM)

For quick testing with mock data:

```bash
# 1. Ensure services are running
docker compose up -d

# 2. Create a test user
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123",
    "preferred_genres": ["Fiction", "Science Fiction"]
  }'

# 3. Login and save token
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -d "username=test@example.com&password=SecurePass123" | jq -r .access_token)

# 4. Upload a sample book (use any PDF or TXT file)
curl -X POST http://localhost:8000/books \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample.pdf" \
  -F "title=Sample Book" \
  -F "author=Test Author" \
  -F "genre=Fiction" \
  -F "description=A test book for demo purposes"
```

### Option 2: Real Books from Project Gutenberg (Recommended)

Load 20 real public domain books with AI summarization:

```bash
# 1. Ensure all services are running (including Ollama)
docker compose up -d

# 2. Wait for Ollama to download the llama3.2 model (first time only, ~2GB)
docker compose logs -f ollama-pull
# Wait until you see "success"

# 3. Verify model is ready
docker compose exec ollama ollama list
# Should show: llama3.2

# 4. Ensure .env has LLM_PROVIDER=ollama (default)
# Already set by default - no changes needed!

# 5. Run the sample data script
python3 add_real_books.py
```

**What this does:**
- Downloads 20 classic books from Project Gutenberg (free, legal)
- Uploads them to your library
- Triggers AI summarization for each book
- Books include: Frankenstein, Dracula, Pride & Prejudice, Moby-Dick, etc.
- Covers 8 genres: Science Fiction, Fantasy, Mystery, Historical Fiction, Romance, Adventure, Horror, Literary Fiction

**Expected timeline:**
- All 20 books: 10-30 minutes
- Each book: 30 seconds to 4 minutes depending on size
- Monitor progress: `docker compose logs -f api | grep summarization`

### Verify Sample Data

```bash
# Check book count
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/books | jq '.total'

# View a book with summary
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/books | jq '.items[0]'
```

## Running Tests

The project has comprehensive test coverage (71 tests) covering all layers.

### Quick Test Run

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest -v

# Run with coverage report
pytest -v --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_services/test_auth_service.py -v

# Run tests matching a pattern
pytest -v -k "test_borrow"
```

### Test Structure

```
tests/
├── conftest.py              # Fixtures (DB, auth, etc.)
├── factories/               # Test data factories
│   ├── book_factory.py
│   ├── user_factory.py
│   └── review_factory.py
├── test_api/               # Integration tests (routes)
│   ├── test_auth_routes.py
│   ├── test_book_routes.py
│   └── test_recommendation_routes.py
├── test_services/          # Business logic tests
│   ├── test_auth_service.py
│   ├── test_book_service.py
│   └── test_recommendation_service.py
└── test_repositories/      # Data access tests
    ├── test_book_repository.py
    └── test_user_repository.py
```

### Test Coverage

Current coverage: **~85%** across all modules

| Module | Coverage | Notes |
|--------|----------|-------|
| Services | 90% | Core business logic fully tested |
| Repositories | 95% | Database operations covered |
| API Routes | 80% | Integration tests for all endpoints |
| Models | 85% | Model methods and relationships |

### Writing New Tests

```python
# Example test using fixtures
async def test_borrow_book(db_session, auth_user, sample_book):
    service = BorrowService(db_session)
    result = await service.borrow_book(sample_book.id, auth_user.id)
    assert result.book_id == sample_book.id
```

### SQLite Compatibility Note

Tests use SQLite for speed, but the app uses PostgreSQL in production. A compatibility layer handles JSONB types automatically.

## Configuration

All configuration is managed via the `.env` file at the project root.

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `LuminaLib` | Application name |
| `DEBUG` | `false` | Debug mode (set to `true` for development) |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection string |

### Authentication & Security

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | `change-me-to-a-random-secret-in-production` | **MUST change in production!** |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token expiration time |

### Storage Backend

| Variable | Default | Options | Description |
|----------|---------|---------|-------------|
| `STORAGE_BACKEND` | `minio` | `minio`, `local` | File storage provider |
| `LOCAL_STORAGE_PATH` | `/app/uploads` | - | Path for local storage |
| `MINIO_ENDPOINT` | `minio:9000` | - | MinIO server endpoint |
| `MINIO_ACCESS_KEY` | `minioadmin` | - | MinIO access credentials |
| `MINIO_SECRET_KEY` | `minioadmin` | - | MinIO secret credentials |
| `MINIO_BUCKET_NAME` | `luminalib-books` | - | S3 bucket name |
| `MINIO_USE_SSL` | `false` | `true`, `false` | Use HTTPS for MinIO |

### LLM Provider

| Variable | Default | Options | Description |
|----------|---------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | `ollama`, `mock` | LLM provider (Ollama runs by default) |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | - | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.2` | `llama3.2`, `llama3.2:1b` | Model to use (1b is 3x faster, auto-downloaded) |
| `OPENAI_API_KEY` | - | - | OpenAI API key (for future OpenAI integration) |
| `OPENAI_MODEL` | `gpt-4o-mini` | - | OpenAI model (for future OpenAI integration) |

### Swapping Providers

The system uses **dependency injection** with factory pattern - change a single environment variable to swap implementations:

```bash
# Switch to local disk storage (no MinIO needed)
STORAGE_BACKEND=local

# Use mock LLM for testing (no Ollama needed)
LLM_PROVIDER=mock
```

**No code changes required!** The factory automatically instantiates the correct implementation based on environment variables.

See [ARCHITECTURE.md](ARCHITECTURE.md) for implementation details.

## Project Structure

The project follows a **clean MVC architecture** with clear separation of concerns:

```
app/
├── api/              # API route handlers (thin layer, routing only)
├── controllers/      # Controller layer (HTTP logic, request/response handling)
├── services/         # Business logic layer (core application logic)
├── repositories/     # Database access layer (data persistence)
├── models/           # SQLAlchemy ORM models (database schema)
├── schemas/          # Pydantic DTOs (request/response validation)
├── core/             # Security, config, dependencies, exceptions
├── interfaces/       # Abstract base classes (storage, LLM providers)
├── infrastructure/   # Concrete implementations (MinIO, Ollama, local storage)
└── workers/          # Background task functions (async job processing)
```

**Request Flow:**
```
Request → Route (api/) → Controller (controllers/) → Service (services/) → Repository (repositories/) → Database
                    ↓                                      ↓
                Response ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←
```

## Tech Stack

- **Framework**: FastAPI (async)
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0 (async) + Alembic
- **Storage**: MinIO (S3-compatible) with local disk fallback
- **LLM**: Ollama (Llama 3.2) with mock provider fallback
- **ML**: scikit-learn (TF-IDF + cosine similarity)
- **Auth**: JWT (python-jose) + bcrypt
- **Testing**: pytest + pytest-asyncio (71 tests, 85% coverage)
- **Linting**: ruff (includes isort)
- **Containerization**: Docker + Docker Compose

## Features

### 🤖 AI-Powered Summarization

- **Automatic book summaries** using Llama 3.2 via Ollama
- Intelligent text extraction from PDF, TXT, and EPUB files
- Background task processing with status tracking
- Supports concurrent summarization of multiple books

### 🎯 ML-Based Recommendations

The recommendation engine uses multiple strategies:

1. **Content-Based Filtering**: TF-IDF vectorization + cosine similarity on book metadata
2. **Implicit Preferences**: Automatically learns from your ratings
   - Genre weights calculated from review scores
   - 5-star reviews boost genre recommendations
   - 1-star reviews penalize genre recommendations
3. **Explicit Preferences**: Favorite genres and authors from your profile
4. **Collaborative Filtering**: Popular books among similar readers

**How it works:**
```python
# Rate books you've read
POST /books/{id}/reviews {"rating": 5, "comment": "Amazing!"}

# System automatically updates your preferences
# Next recommendation call considers your taste
GET /recommendations
# Returns personalized suggestions with strategy used
```

### 📊 Review Sentiment Analysis

- AI-powered sentiment scoring (0.0 to 1.0)
- Sentiment labels: positive, neutral, negative
- **Review consensus**: Aggregated summary of all reviews for a book
- Helps readers understand overall reception before borrowing

### 📚 Library Management

- **Borrow/Return system** with availability tracking
- **Copy management**: Track available vs total copies
- **Borrow history**: Full audit trail of who borrowed what
- **Review requirements**: Must borrow to review (verified readers only)

## Development

### Local Development Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd jk-tech-LuminaLib

# 2. Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Start services
docker compose up -d

# 5. Run tests
pytest -v

# 6. Run linter
ruff check .
ruff format .
```

### Making Code Changes

The API container auto-reloads when you change Python files:

```bash
# Start with logs
docker compose up

# Edit files in your IDE
# Watch logs for automatic reload
# Test your changes immediately
```

### Database Migrations

```bash
# Create a new migration
docker compose exec api alembic revision --autogenerate -m "Add new field"

# Apply migrations
docker compose exec api alembic upgrade head

# Rollback one version
docker compose exec api alembic downgrade -1

# View migration history
docker compose exec api alembic history
```

### Applying Code Changes to Docker

After modifying code:

```bash
# Quick restart (Python code changes only)
docker compose restart api

# Full rebuild (dependency or config changes)
docker compose down
docker compose build api
docker compose up -d

# Clean rebuild (if you have issues)
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

## Troubleshooting

### API won't start

**Check logs:**
```bash
docker compose logs api
```

**Common issues:**
- **Database not ready**: Wait 10 seconds after `docker compose up`
- **Port conflict**: Check if port 8000 is already in use
- **Migration errors**: Run `docker compose down -v` to reset database

### LLM Summarization Timing Out

**Solutions:**

1. **Check Ollama is running:**
   ```bash
   docker compose ps ollama
   docker compose logs ollama
   ```

2. **Verify model is downloaded:**
   ```bash
   docker compose exec ollama ollama list
   ```

3. **Reduce batch size**: Upload fewer books at a time (5-10 instead of 20)

4. **Use faster model:**
   ```bash
   docker compose exec ollama ollama pull llama3.2:1b  # 3x faster
   # Update .env: OLLAMA_MODEL=llama3.2:1b
   docker compose restart api
   ```

### Bcrypt Version Error

If you see `error reading bcrypt version`:

```bash
# Already fixed in pyproject.toml (bcrypt==4.0.1)
# Just rebuild:
docker compose down
docker compose build --no-cache api
docker compose up -d
```

### Tests Failing

```bash
# Ensure you have dev dependencies
pip install -e ".[dev]"

# Run tests with verbose output
pytest -vv

# Run single test for debugging
pytest tests/test_services/test_auth_service.py::test_signup -vv
```

### MinIO Connection Issues

```bash
# Check MinIO is running
docker compose ps minio

# Access MinIO console
open http://localhost:9001
# Login: minioadmin / minioadmin

# Switch to local storage (bypass MinIO)
# In .env: STORAGE_BACKEND=local
docker compose restart api
```

### Database Issues

```bash
# View database logs
docker compose logs db

# Connect to database directly
docker compose exec db psql -U postgres -d luminalib

# Reset database completely
docker compose down -v
docker compose up -d
```

## Monitoring

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f ollama

# Filter by keyword
docker compose logs api | grep summarization
docker compose logs api | grep ERROR
```

### Monitor Summarization Progress

```bash
# Real-time summarization tracking
docker compose logs -f api | grep -E "(ollama_|summarization)"

# Check summarization status in database
docker compose exec db psql -U postgres -d luminalib -c \
  "SELECT summary_status, COUNT(*) FROM books GROUP BY summary_status;"
```

### Health Checks

```bash
# API health
curl http://localhost:8000/docs

# Database connection
docker compose exec api python -c "from app.core.database import engine; print('DB OK')"

# MinIO storage
curl http://localhost:9000/minio/health/live
```

## Support

- **Documentation**: See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- **Issues**: Open an issue on GitHub
- **Questions**: Contact the maintainers
