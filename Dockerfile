# # docker build -t joke-reader:1.0 . --no-cache
FROM python:3.11-slim-buster

RUN pip install poetry==1.3.2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /code

COPY . /code/

ENV DB_LOCATION=/code/chucks_wisdom/sqlite_storage/sqlite.db

RUN poetry install --no-cache

EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=5 \
            CMD curl -f http://localhost:5000/health || exit 1
ENTRYPOINT ["poetry", "run", "python", "app.py"]
