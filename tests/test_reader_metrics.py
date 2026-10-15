from __future__ import annotations

import os
import unittest
from unittest import mock

os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4317")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")  # no trace export from tests

import cyberpunk  # noqa: E402
import reader  # noqa: E402


class FakeStorage:
    def __init__(self, _dsn):
        pass

    def read_all_jokes(self):
        return [(1, "dev", "a joke"), (2, "food", "another")]

    def close_connection(self):
        pass


class ReaderMetricsTests(unittest.TestCase):
    def setUp(self):
        self.client = cyberpunk.app.test_client()

    def metrics(self) -> str:
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        return r.get_data(as_text=True)

    def test_api_counts_jokes_and_requests_by_route(self):
        with mock.patch.dict(os.environ, {"DB_CONNECTION_STRING": "x"}), mock.patch.object(reader, "PGStorage", FakeStorage):
            self.assertEqual(len(self.client.get("/api").get_json()), 2)
        text = self.metrics()
        self.assertIn("reader_jokes 2.0", text)
        self.assertIn('reader_http_requests_total{code="200",route="/api"}', text)
        self.assertIn("reader_db_read_duration_seconds_count", text)

    def test_unknown_paths_share_one_series(self):
        self.client.get("/wp-login.php")
        self.assertIn('reader_http_requests_total{code="404",route="other"}', self.metrics())

    def test_failed_reads_are_counted(self):
        class Broken(FakeStorage):
            def read_all_jokes(self):
                raise RuntimeError("db down")

        before = reader.metrics.DB_ERRORS._value.get()
        with mock.patch.dict(os.environ, {"DB_CONNECTION_STRING": "x"}), mock.patch.object(reader, "PGStorage", Broken):
            with self.assertRaises(RuntimeError):
                reader.read_hashed_entries()
        self.assertEqual(reader.metrics.DB_ERRORS._value.get(), before + 1)
