# AGENTS.md

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Development mode (with auto-reload)
fastapi dev api/main.py

# Production mode with Docker
sudo docker build -t api . && sudo docker run -d -p 80:80 --env-file .env api
```

### Testing
```bash
# Run all unit tests
pytest tests/unit_tests

# Run specific test file
pytest tests/unit_tests/test_search_route.py

# Run with verbose output
pytest tests/unit_tests -v
```

### Code Quality
```bash
# Format code with black
black .

# Sort imports
isort .
```

## Architecture & Patterns

### Application Structure
- `api/main.py`: FastAPI application entry point. Creates app instance, registers all route modules with `/v1` prefix, and configures CORS middleware and custom AuthMiddleware
- `routes/`: API route handlers (endpoints), organized by resource (users, experts, nonprofits, litigations, search, auth, home). Each route module defines a FastAPI router with its endpoints
- `data/`: Data access layer containing DatabaseRepository (Supabase client wrapper) and AIService (LangChain + Google Gemini integration)
- `model/`: Pydantic data models for request/response validation
- `usecase/`: Business logic layer (currently minimal)
- `tests/unit_tests/`: Pytest unit tests using mocking (pytest-mock, pytest-asyncio)

### Authentication Flow

Authentication is JWT-based with a custom middleware pattern:

1. **AuthMiddleware** (`routes/middleware.py`): Intercepts all requests with `Authorization` headers, extracts bearer tokens, and validates them using `verify_access_token()` from `auth_route_v1.py`
2. Login endpoint (`/v1/login`) authenticates users via username/password against Supabase `users` table using bcrypt for password hashing
3. Successful authentication returns a JWT token signed with `SECRET_KEY` (HS256 algorithm) from environment variables
4. Token expiration is controlled by `ACCESS_TOKEN_EXPIRE_MILLISECONDS` environment variable

### Database Architecture

The application uses Supabase (PostgreSQL) with the following key patterns:

- **DatabaseRepository** (`data/database_repository.py`): Centralized repository class that encapsulates all database operations
- Uses Supabase Python client for table operations and RPC calls
- Key tables: `users`, `experts`, `entities`, `nonprofits`, `Litigation`, `structural_sub_factors`
- Complex queries use Supabase RPC functions (e.g., `get_homepage_data`, `search_experts_with_keyword`, `search_entities_with_keyword`)
- Full-text search implemented via `.text_search()` method on `entities.about` field

### AI Integration (`data/ai_service.py`)

The **AIService** (`data/ai_service.py`) handles AI-powered features:

- **Web scraping**: Uses BeautifulSoup4 to extract content from nonprofit/expert websites
- **About page discovery**: LLM analyzes scraped HTML to find "About Us" pages
- **Summary generation**: Generates 3-4 sentence summaries from about pages
- **Hashtag generation**: Extracts relevant hashtags (1-4) from about text
- **Rate limiting**: Built-in rate limiter (10 calls per minute) to manage LLM API usage
- Uses Google Gemini 2.0 Flash via LangChain with structured JSON output parsing

### Dependency Injection Pattern

All routes use FastAPI's dependency injection for DatabaseRepository:

```python
def get_database_repository() -> DatabaseRepository:
    return DatabaseRepository()

@router.get("/endpoint")
async def endpoint(repository: DatabaseRepository = Depends(get_database_repository)):
    # Use repository...
```

This pattern enables easy mocking in tests using `mocker.patch()`.

## Environment Variables (.env)

Required environment variables in `.env`:
- `SECRET_KEY`: JWT signing key
- `ALGORITHM`: JWT algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MILLISECONDS`: Token expiration time
- `DATABASE_URL`: Supabase project URL
- `DATABASE_API_KEY`: Supabase anon/public API key
- `GOOGLE_API_KEY`: Google AI API key for Gemini

## Testing Conventions

- Tests use `pytest` with async support enabled via `pytest.ini` (`--asyncio-mode=auto`)
- Mock external dependencies (DatabaseRepository, AIService) using `pytest-mock`
- Use `AsyncMock` for async methods, `MagicMock` for sync methods
- FastAPI TestClient is used for endpoint testing without running a server
- Test files follow naming pattern `test_<module>_route.py` or `test_<module>.py`

## Deployment

The application is deployed on Vercel using `vercel.json` configuration:
- All routes are rewritten to `api/main.py`
- FastAPI runs in serverless mode on Vercel
- Docker support available for traditional deployments (port 80, production mode with `fastapi run`)
