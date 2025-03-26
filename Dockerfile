# # docker build -t joke-reader:1.0 . --no-cache
# FROM python:3.9-alpine
# RUN apk add --no-cache curl
# WORKDIR /app
# RUN touch /app/sqlite.db
# ENV DB_LOCATION=/app/sqlite.db
# COPY requirements.txt requirements.txt
# RUN pip install -r requirements.txt
# COPY app.py app.py
# EXPOSE 5000
# HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=5 \
#             CMD curl -f http://localhost:5000/health || exit 1
# ENTRYPOINT [ "python3", "app.py" ]

FROM python:3.11.5-slim-bookworm

ARG JOKE_ENV

ENV DB_LOCATION=/code/sqlite.db

# ENV JOKE_ENV=${JOKE_ENV} \
#   DB_LOCATION=/code/sqlite.db
#   PYTHONFAULTHANDLER=1 \
#   PYTHONUNBUFFERED=1 \
#   PYTHONHASHSEED=random \
#   PIP_NO_CACHE_DIR=off \
#   PIP_DISABLE_PIP_VERSION_CHECK=on \
#   PIP_DEFAULT_TIMEOUT=100 \
#   # Poetry's configuration:
#   POETRY_NO_INTERACTION=1 \
#   POETRY_VIRTUALENVS_CREATE=false \
#   POETRY_CACHE_DIR='/var/cache/pypoetry' \
#   POETRY_HOME='/usr/local' \
#   POETRY_VERSION=1.4.0

WORKDIR /code

RUN apt-get -y update; apt-get -y install curl

# System deps:
RUN curl -sSL https://install.python-poetry.org | python3 -

RUN touch /code/sqlite.db

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY poetry.lock pyproject.toml /code/

# Project initialization:
RUN /root/.local/bin/poetry install --no-interaction --no-ansi

# Creating folders, and files for a project:
COPY . /code

COPY app.py app.py
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=5 \
            CMD curl -f http://localhost:5000/health || exit 1
ENTRYPOINT [ "/root/.local/bin/poetry"," run", "python3", "app.py" ]
