# Code Review - GoodBot API

## Executive Summary

This review identifies **critical security vulnerabilities**, error handling issues, code quality concerns, and architectural improvements for the GoodBot API. Priority should be given to security fixes, especially credential management and password exposure.

---

## 🔴 CRITICAL ISSUES

### 1. **Exposed Credentials in `.env` File**
**Location:** `.env:1-6`
**Severity:** CRITICAL

The `.env` file contains sensitive credentials that are currently committed to version control:
- JWT secret key
- Database API keys
- Google API key

**Impact:** Anyone with repository access can:
- Forge authentication tokens
- Access the production database
- Use your Google AI API quota

**Fix:**
```bash
# Immediately rotate ALL credentials
# Remove .env from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Ensure .env is in .gitignore (it already is, but verify)
# Create .env.example with placeholder values
```

### 2. **Password Exposure in API Response**
**Location:** `routes/users_route_v1.py:63-76`, `model/user_v1.py:7-13`
**Severity:** CRITICAL

The `/users/me` endpoint returns the user's hashed password in the response:

```python
@router.get("/me", response_model=User)
async def get_user(...):
    user = repository.get_user_by_username(token_username)
    return user  # Returns password field!
```

**Impact:** Exposes bcrypt hashes which can be subjected to offline brute-force attacks.

**Fix:**
```python
# Create a UserResponse model without password
class UserResponse(BaseModel):
    username: str
    active: int

# Update endpoint
@router.get("/me", response_model=UserResponse)
async def get_user(...):
    user = repository.get_user_by_username(token_username)
    return UserResponse(username=user["username"], active=user["active"])
```

### 3. **Hardcoded CORS Origins**
**Location:** `api/main.py:19-24`
**Severity:** HIGH

CORS origins are hardcoded in the application code, making it difficult to configure per environment:

```python
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "https://www.responsibletechrepo.com",
]
```

**Fix:** Move to environment variables:
```python
# .env
CORS_ORIGINS=http://localhost,http://localhost:3000,https://www.responsibletechrepo.com

# main.py
origins = os.getenv("CORS_ORIGINS", "").split(",")
```

---

## 🟠 HIGH PRIORITY ISSUES

### 4. **Inconsistent Error Handling**
**Location:** Throughout all routes
**Severity:** HIGH

All routes follow the same problematic pattern:
- Generic exception catching (`except Exception as e`)
- No HTTP status codes (always returns 200)
- Inconsistent error responses (sometimes dict, sometimes string)
- Only prints errors to console (no logging)

**Example Issues:**
```python
# routes/users_route_v1.py:29-60
@router.post("/")
async def create_user(...):
    try:
        if repository.user_exists(value=username):
            return {"message": "User already exists"}  # Should be 409 Conflict
        # ...
        return {"message": "User creation failed"}  # Should be 500 or specific error
    except Exception as e:
        print(f"Error creating user: {e}")  # Only prints, doesn't log
        return {"message": "User creation failed"}  # Always 200 OK
```

**Fix:**
```python
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(...):
    username = user.username.lower()

    if repository.user_exists(value=username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )

    hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
    new_user = repository.insert_user(username, hashed_password)

    if not new_user:
        logger.error(f"Failed to create user: {username}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed"
        )

    return {"message": "User created successfully"}
```

### 5. **Missing Input Validation**
**Location:** `model/create_user_request_v1.py`, `model/user_v1.py`
**Severity:** HIGH

No validation on user inputs:
- No email format validation for username
- No password strength requirements
- No length constraints

**Fix:**
```python
from pydantic import BaseModel, Field, field_validator
import re

class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator('username')
    @classmethod
    def validate_email(cls, v):
        # Basic email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain a number')
        return v
```

### 6. **SQL Injection Risk via Search**
**Location:** `data/database_repository.py:280-340`
**Severity:** HIGH

The search function manipulates user input directly for text search:

```python
async def search_by_keywords(self, keywords: str):
    keywords = keywords.replace(" ", ",")
    keywords_array = keywords.split(",")
    keywords_array = [f"'{keyword}'" for keyword in keywords_array]  # Manual quoting!
    keywords = " | ".join(keywords_array)
```

While Supabase client likely handles this safely, it's better to validate and sanitize input explicitly.

**Fix:**
```python
import re

async def search_by_keywords(self, keywords: str):
    # Sanitize input - remove special characters except alphanumeric and spaces
    keywords = re.sub(r'[^a-zA-Z0-9\s]', '', keywords)

    # Limit length to prevent DoS
    keywords = keywords[:500]

    # Rest of implementation...
```

### 7. **Database Connection Pool Exhaustion**
**Location:** `data/database_repository.py:11-20`
**Severity:** HIGH

Every request creates a new Supabase client instance:

```python
def get_database_client() -> Client:
    load_dotenv()  # Called on every request!
    client: Client = create_client(...)  # New connection every time
    return client
```

**Impact:**
- Connection pool exhaustion under load
- Slow performance due to connection overhead
- Unnecessary .env file parsing on every request

**Fix:**
```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_database_client() -> Client:
    load_dotenv()
    client: Client = create_client(
        os.environ.get("DATABASE_URL"),
        os.environ.get("DATABASE_API_KEY")
    )
    return client
```

---

## 🟡 MEDIUM PRIORITY ISSUES

### 8. **Typo in Router Tag**
**Location:** `routes/experts_route_v1.py:10`
**Severity:** MEDIUM

```python
router = APIRouter(
    prefix="/experts",
    tags=["excepts"],  # Should be "experts"
    ...
)
```

### 9. **Dead/Test Code**
**Location:** Multiple files
**Severity:** MEDIUM

Several endpoints contain test/unused code:

1. `routes/users_route_v1.py:82-92` - Test endpoint with incorrect docstring
2. `routes/nonprofits_route_v1.py:54-65` - Commented-out functionality
3. `usecase/get_homepage_data.py:19-22` - TODO comments

**Fix:** Remove test endpoints before production or protect with feature flags.

### 10. **Missing Pagination Validation**
**Location:** `routes/experts_route_v1.py:22-34`, `routes/nonprofits_route_v1.py:33-51`
**Severity:** MEDIUM

Pagination parameters lack validation:

```python
@router.get("/")
async def get_experts(page_number: int = 1, page_size: int = 10, ...):
    # No validation: user can request page_number=-1 or page_size=1000000
```

**Fix:**
```python
from pydantic import Field
from fastapi import Query

@router.get("/")
async def get_experts(
    page_number: int = Query(default=1, ge=1, le=1000),
    page_size: int = Query(default=10, ge=1, le=100),
    ...
):
```

### 11. **Async/Await Inconsistency**
**Location:** `routes/litigations_route_v1.py:25-34`
**Severity:** MEDIUM

Some repository methods are not async but are called in async endpoints:

```python
@router.get("/")
async def fetch_litigations(...):
    litigations = repository.get_litigations()  # Not awaited - sync method
```

**Impact:** Blocks the event loop, reducing concurrency.

**Fix:** Make all DB operations async:
```python
# In database_repository.py
async def get_litigations(self):
    # Use async Supabase methods if available
```

### 12. **Rate Limiter Not Thread-Safe**
**Location:** `data/ai_service.py:86-92`
**Severity:** MEDIUM

The LLM rate limiter uses instance variables that aren't thread-safe:

```python
self.llm_rate_limiter = {
    "calls": 0,
    "max_calls": 10,
    # ...
}
```

In async context, race conditions can occur when multiple requests modify the counter.

**Fix:** Use a proper rate limiting library like `slowapi` or Redis-based rate limiting.

### 13. **Missing Response Models**
**Location:** All routes
**Severity:** MEDIUM

Most endpoints don't define response models, making the API documentation unclear:

```python
@router.get("/")
async def get_experts(...):
    return {"data": experts}  # Undocumented structure
```

**Fix:**
```python
from pydantic import BaseModel

class ExpertResponse(BaseModel):
    data: list[dict]  # Or better: list[Expert]

@router.get("/", response_model=ExpertResponse)
async def get_experts(...) -> ExpertResponse:
    experts = await repository.get_experts(...)
    return ExpertResponse(data=experts)
```

---

## 🟢 LOW PRIORITY / IMPROVEMENTS

### 14. **Code Duplication**
**Location:** All routes
**Severity:** LOW

Every route file duplicates the `get_database_repository()` function.

**Fix:** Move to a shared `dependencies.py`:
```python
# routes/dependencies.py
def get_database_repository() -> DatabaseRepository:
    return DatabaseRepository()

# In route files
from routes.dependencies import get_database_repository
```

### 15. **Inconsistent Naming**
**Location:** Various
**Severity:** LOW

- `get_litigations()` is sync while `get_experts()` is async
- Some endpoints return `{"data": ...}`, others return raw data
- `nonprofit_id` vs `expert_id` inconsistent handling

### 16. **Missing Health Check Endpoint**
**Location:** N/A
**Severity:** LOW

No `/health` or `/readiness` endpoint for monitoring.

**Fix:**
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
```

### 17. **Web Scraping Without Retry Logic**
**Location:** `data/ai_service.py:96-111`
**Severity:** LOW

Web scraping has a single timeout but no retry logic for transient failures.

**Fix:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def scrape_website(self, url: str, timeout: int = 10):
    # existing implementation
```

### 18. **Hardcoded LLM Model**
**Location:** `data/ai_service.py:38`
**Severity:** LOW

```python
client = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",  # Hardcoded
    ...
)
```

**Fix:** Use environment variable for model selection.

---

## Testing Gaps

### 19. **Missing Test Coverage**
**Severity:** MEDIUM

Missing tests for:
- `data/ai_service.py` (0% coverage)
- `data/database_repository.py` (partial coverage via route tests)
- Edge cases (pagination boundaries, special characters in search)
- Authentication middleware edge cases
- Error scenarios in routes

### 20. **Test Data Quality**
**Location:** `tests/unit_tests/test_search_route.py:59-71`
**Severity:** LOW

Test expects hardcoded error message that doesn't match actual implementation:

```python
assert response.json() == {"message": 'Error while searching for "{query}"'}
```

Actual code returns:
```python
return {"message": 'Error while searching for "{query}"'}  # {query} not interpolated
```

---

## Architecture Recommendations

### 21. **Consider Dependency Injection Framework**
**Severity:** LOW

Current manual DI works but could benefit from a framework like `dependency-injector` for better testability and lifecycle management.

### 22. **Implement Logging Strategy**
**Severity:** MEDIUM

Replace all `print()` statements with proper logging:

```python
import logging
from logging.config import dictConfig

# Configure structured logging
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
})
```

### 23. **Add API Versioning Strategy**
**Severity:** LOW

Currently uses `/v1` prefix but no clear versioning strategy documented.

### 24. **Environment-Based Configuration**
**Severity:** MEDIUM

Create proper configuration management:

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_ms: int
    database_url: str
    database_api_key: str
    google_api_key: str
    cors_origins: list[str]

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Summary of Action Items

### Immediate (Do Today)
1. ✅ Rotate all credentials in `.env`
2. ✅ Remove `.env` from git history
3. ✅ Fix password exposure in User model
4. ✅ Add proper HTTP status codes to error responses

### Short Term (This Week)
5. ✅ Implement structured logging
6. ✅ Add input validation to models
7. ✅ Fix database connection pooling
8. ✅ Add response models to all endpoints
9. ✅ Implement proper error handling with HTTPException

### Medium Term (This Month)
10. ✅ Increase test coverage to >80%
11. ✅ Make all DB operations consistently async
12. ✅ Implement proper rate limiting
13. ✅ Add health check endpoints
14. ✅ Move CORS origins to environment config

### Long Term (Next Quarter)
15. ✅ Implement centralized error handling middleware
16. ✅ Add request/response logging middleware
17. ✅ Consider API gateway for rate limiting
18. ✅ Implement monitoring and alerting
