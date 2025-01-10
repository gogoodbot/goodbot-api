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
2. Install [pip](https://pip.pypa.io/en/stable/installing/)
3. Create a virtual environment via `python -m venv [virtual_environment_name]`
4. Activate the virtual environment via `source [virtual_environment_name]/bin/activate`
5. Install the dependencies via `pip install -r requirements.txt`

### Running the Application Locally

1. Activate the virtual environment via `source [virtual_environment_name]/bin/activate`
2. Run the application via `fastapi dev api/main.py`
3. The application should be available at `http://127.0.0.1:8000`
4. To stop the application, press `Ctrl + C`

### Running the Unit Tests

1. Activate the virtual environment via `source [virtual_environment_name]/bin/activate`
2. Run the unit tests via `pytest tests/unit_tests`

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
