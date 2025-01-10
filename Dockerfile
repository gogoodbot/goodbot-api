FROM python:3.12-slim

RUN apt update -y && apt install -y curl git python3-pip && apt clean && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip

COPY . .

RUN python3 -m pip install --no-cache-dir --upgrade -r /requirements.txt

EXPOSE 80

CMD ["fastapi", "run", "/api/main.py", "--host", "0.0.0.0", "--port", "80", "--reload"]
