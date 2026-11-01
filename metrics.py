"""The reader's own Prometheus metrics, served at /metrics with brick-observe's
http_server_* ones (cyberpunk.py): how long the database read takes, and how
many jokes the last read returned."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

DB_READ_SECONDS = Histogram("reader_db_read_duration_seconds", "Time to read every joke from Postgres.")
DB_ERRORS = Counter("reader_db_errors_total", "Database reads that failed.")
JOKES = Gauge("reader_jokes", "Jokes the last database read returned.")
