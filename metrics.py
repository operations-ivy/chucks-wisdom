"""The reader's Prometheus metrics, served at /metrics (cyberpunk.py):
requests by route and status, how long they and the database read take,
and how many jokes the last read returned."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

REQUESTS = Counter("reader_http_requests_total", "HTTP requests served.", ["route", "code"])
REQUEST_SECONDS = Histogram("reader_http_request_duration_seconds", "Time to answer a request.", ["route"])
DB_READ_SECONDS = Histogram("reader_db_read_duration_seconds", "Time to read every joke from Postgres.")
DB_ERRORS = Counter("reader_db_errors_total", "Database reads that failed.")
JOKES = Gauge("reader_jokes", "Jokes the last database read returned.")
