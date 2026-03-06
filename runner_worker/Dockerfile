FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y docker.io

COPY worker.py .

RUN pip install psycopg2-binary

CMD ["python", "worker.py"]