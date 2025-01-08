FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl && \
    curl https://getcroc.schollz.com | bash

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
