FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMS_FILE=/data/streams.json

WORKDIR /app

COPY requirements.txt .
RUN pip install --require-hashes -r requirements.txt

# copy only the code; .env is passed in at runtime through env_file
COPY bot.py .
COPY radio/ radio/

VOLUME /data

CMD ["python", "bot.py"]
