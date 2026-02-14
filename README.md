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
docker-compose up --build
```

This single command starts:
- **API** at `http://localhost:8000` (FastAPI with auto-docs at `/docs`)
- **PostgreSQL** at `localhost:5432`
- **MinIO** at `localhost:9000` (console at `localhost:9001`)
- Database migrations run automatically on startup

### Optional: Enable Real LLM (Ollama)

By default, the system uses a mock LLM provider. To use Ollama with Llama 3:

```bash
# Start with the LLM profile
docker-compose --profile llm up --build

# Pull the model (in another terminal)
docker exec -it jk-tech-luminalib-ollama-1 ollama pull llama3.2

# Update .env
# LLM_PROVIDER=ollama
```

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

## Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest -v

# Run with coverage
pytest -v --cov=app --cov-report=term-missing
```

## Configuration

All configuration is managed via the `.env` file. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_BACKEND` | `minio` | File storage: `minio` or `local` |
| `LLM_PROVIDER` | `mock` | LLM provider: `mock`, `ollama` |
| `JWT_SECRET_KEY` | (change me) | Secret for JWT signing |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token expiry |

### Swapping Providers

Change a single environment variable to swap implementations:

```env
# Switch from MinIO to local disk storage
STORAGE_BACKEND=local

# Switch from mock to real LLM
LLM_PROVIDER=ollama
```

No code changes required. See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

## Project Structure

```
app/
├── api/              # Thin route handlers (controllers)
├── services/         # Business logic layer
├── repositories/     # Database access layer
├── models/           # SQLAlchemy ORM models
├── schemas/          # Pydantic DTOs (request/response)
├── core/             # Security, config, dependencies, exceptions
├── interfaces/       # Abstract base classes (storage, LLM)
├── infrastructure/   # Concrete implementations (MinIO, Ollama, etc.)
└── workers/          # Background task functions
```

## Tech Stack

- **Framework**: FastAPI (async)
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0 (async) + Alembic
- **Storage**: MinIO (S3-compatible) with local disk fallback
- **LLM**: Ollama (Llama 3) with mock provider fallback
- **ML**: scikit-learn (TF-IDF + cosine similarity)
- **Auth**: JWT (python-jose) + bcrypt
- **Testing**: pytest + pytest-asyncio
- **Linting**: ruff (includes isort)
- **Containerization**: Docker + Docker Compose
