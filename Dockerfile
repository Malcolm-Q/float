FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl && \
    curl https://getcroc.schollz.com | bash

RUN echo "y" | croc --classic

WORKDIR /app

RUN mkdir -p /app/src/files

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
