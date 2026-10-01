from __future__ import annotations

import os
import time
import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import field

import structlog
from api_request_operations_ivy.api_request import ApiRequest
from opentelemetry import trace
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from prometheus_client import Counter
from prometheus_client import start_http_server
from sql_storage_operations_ivy.pg_storage import PGStorage

from tracing import init_tracing

log = structlog.get_logger()
tracer = trace.get_tracer(__name__)

JOKES_WRITTEN = Counter("importer_jokes_written_total", "Number of jokes written to DB this session")
DUPLICATES_RECEIVED = Counter("importer_duplicates_received_total", "duplicate joke hits from API")
CATEGORY_SWITCHES = Counter(
    "importer_category_switches_total", "amount of times category has switched due to duplicates"
)

# Search results with no category are stored under this one.
UNCATEGORIZED = "uncategorized"


@dataclass
class Settings:
    """What to import. Set through IMPORTER_* environment variables (the Jenkins
    chuck-importer job's parameters); the defaults are the original behaviour."""

    # Free-text search: import the jokes matching it, in one request. Empty
    # means sample random jokes by category instead.
    query: str = ""
    # Categories to sample from; empty means every category the API has.
    categories: list[str] = field(default_factory=list)
    # Stop after this many new jokes.
    jokes: int = 1000
    # Random pulls per category in one pass over the categories.
    tries_per_category: int = 1000
    # Move to the next category after this many duplicates.
    max_duplicates: int = 50
    # Pause after each random pull, to go easy on the API.
    sleep_seconds: float = 60.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> Settings:
        s = cls()
        s.query = env.get("IMPORTER_QUERY", "").strip()
        s.categories = [c.strip() for c in env.get("IMPORTER_CATEGORIES", "").split(",") if c.strip()]
        s.jokes = int(env.get("IMPORTER_JOKES") or s.jokes)
        s.tries_per_category = int(env.get("IMPORTER_TRIES_PER_CATEGORY") or s.tries_per_category)
        s.max_duplicates = int(env.get("IMPORTER_MAX_DUPLICATES") or s.max_duplicates)
        s.sleep_seconds = float(env.get("IMPORTER_SLEEP_SECONDS") or s.sleep_seconds)
        return s


def import_search(api, storage, settings: Settings) -> int:
    """Store the jokes matching settings.query that we don't have yet, up to settings.jokes."""
    found = api.find_specific(urllib.parse.quote(settings.query))
    if "error" in found:
        raise RuntimeError(f"Search for {settings.query!r} failed: {found['error']}")
    results = found.get("result", [])
    log.info("Search results", query=settings.query, total=len(results))

    joke_count = 0
    for joke in results:
        if joke_count >= settings.jokes:
            break
        with tracer.start_as_current_span("process_joke") as span:
            category = (joke.get("categories") or [UNCATEGORIZED])[0]
            span.set_attribute("chuck.category", category)
            span.set_attribute("chuck.joke_id", joke["id"])
            if storage.check_for_duplicate(joke["id"], joke["value"]):
                DUPLICATES_RECEIVED.inc()
                span.set_attribute("chuck.outcome", "duplicate")
                continue
            storage.insert_joke(joke["id"], category, joke["value"])
            joke_count += 1
            JOKES_WRITTEN.inc()
            span.set_attribute("chuck.outcome", "inserted")
            log.info("Thats a new one!: %s", joke["id"])
    return joke_count


def choose_categories(api, settings: Settings) -> list[str]:
    """The categories to sample: the requested ones the API knows, or all of them."""
    available = api.get_categories()
    if isinstance(available, dict):
        raise RuntimeError(f"Couldn't list categories: {available.get('error')}")
    if not settings.categories:
        return available
    unknown = [c for c in settings.categories if c not in available]
    if unknown:
        log.warning("Skipping unknown categories", unknown=unknown, available=available)
    chosen = [c for c in settings.categories if c in available]
    if not chosen:
        raise RuntimeError(f"None of {settings.categories} are categories; the API has {available}")
    return chosen


def import_random(api, storage, settings: Settings, sleep=time.sleep) -> int:
    """Pull random jokes category by category until settings.jokes are new, or a
    full pass over the categories finds nothing new."""
    joke_categories = choose_categories(api, settings)
    joke_count = 0
    while joke_count < settings.jokes:
        joke_count_before_pass = joke_count
        for category in joke_categories:
            duplicate_count = 0
            for i in range(settings.tries_per_category):
                if joke_count >= settings.jokes:
                    break
                log.info("Checking API.. %s", i)
                try:
                    with tracer.start_as_current_span("process_joke") as span:
                        span.set_attribute("chuck.category", category)

                        joke_data = api.get_random_joke_from_category(category)
                        joke_id = joke_data["id"]
                        joke_value = joke_data["value"]
                        span.set_attribute("chuck.joke_id", joke_id)

                        sleep(settings.sleep_seconds)
                        if (
                            not storage.check_for_duplicate(joke_id, joke_value)
                            and duplicate_count < settings.max_duplicates
                        ):
                            storage.insert_joke(joke_id, category, joke_value)
                            joke_count += 1
                            JOKES_WRITTEN.inc()
                            span.set_attribute("chuck.outcome", "inserted")
                            log.info("Thats a new one!: %s", joke_id)
                        elif duplicate_count >= settings.max_duplicates:
                            CATEGORY_SWITCHES.inc()
                            span.set_attribute("chuck.outcome", "category_switch")
                            log.info("Ok let's move on: %s", category)
                            break
                        else:
                            DUPLICATES_RECEIVED.inc()
                            span.set_attribute("chuck.outcome", "duplicate")
                            log.info("I've heard that one before: %s", joke_id)
                            duplicate_count += 1
                            continue
                except Exception:
                    log.exception("Error fetching/storing joke for category %s, skipping", category)
                    continue

        log.info("Total Jokes Added this run: %s", str(joke_count))
        if joke_count == joke_count_before_pass:
            log.warning("No new jokes found in a full pass over all categories, stopping.")
            break
    return joke_count


if __name__ == "__main__":
    init_tracing("chucks-wisdom-importer")
    RequestsInstrumentor().instrument()
    PsycopgInstrumentor().instrument()

    start_http_server(8000)

    db_connection_string = os.environ["DB_CONNECTION_STRING"]
    settings = Settings.from_env()
    log.info("Importer settings", **vars(settings))
    api = ApiRequest()
    try:
        log.info("Creating DB Connection")
        log.info("...")
        storage = PGStorage(db_connection_string)
        log.info("DB Connection Established!")
    except Exception as e:
        raise Exception("No connection, did you export DB_CONNECTION_STRING?") from e

    try:
        if settings.query:
            added = import_search(api, storage, settings)
        else:
            added = import_random(api, storage, settings)
        log.info("Import finished", added=added)
    finally:
        storage.close_connection()
