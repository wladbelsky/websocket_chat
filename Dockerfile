FROM python:3.12-bullseye

LABEL authors="wladbelsky"

COPY requirements.txt /app/requirements.txt

RUN apt-get update && apt-get install -y libpq-dev

RUN pip install -r /app/requirements.txt

COPY . /app

WORKDIR /app

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
