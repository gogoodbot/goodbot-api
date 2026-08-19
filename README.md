## GoodBot API Backend Application

A backend application for the GoodBot Project written in Python using the FastAPI framework.

### Prerequisites

- Python 3.12
- pip
- FastAPI
- pytest

### Project Structure

```
goodbot-api
├── api
│   ├── main.py
│   ├── model
│   │   ├── data models
│   ├── routes
│   │   ├── api routes/endpoints
|── tests
│   ├── unit tests
```

### Installation

1. Install [Python](https://www.python.org/downloads/)
2. Install [uv](https://docs.astral.sh/uv/)
3. Install dependencies via `uv sync`

### Running the Application Locally

1. Run the application via `uv run fastapi dev api/main.py`
2. The application should be available at `http://127.0.0.1:8000`
3. To stop the application, press `Ctrl + C`

### Running the Unit Tests

1. Run the unit tests via `uv run pytest tests/unit_tests`

### Running the Application with Docker

To run the application in production mode, use the following command:

```bash
sudo docker build -t api . && sudo docker run -d -p 80:80 --env-file .env api
```

This command will:

- Build the Docker image tagged as api.
- Run the container in detached mode (-d), ensuring it continues running in the background.
- Use environment variables from the .env file.
- The application will now be available at http://localhost:80 or http://127.0.0.1:80.
