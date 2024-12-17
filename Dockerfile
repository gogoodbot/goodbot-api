FROM python:3.10-slim

RUN apt update -y && apt install -y curl git python3-pip && apt clean && rm -rf /var/lib/apt/lists/*

WORKDIR /goodbot_api

COPY requirements.txt .

RUN python3 -m pip install --upgrade pip

RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
