from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import unittest

FIELDS = {"timestamp", "level", "event", "logger", "service"}


def lines_from(code: str) -> list[dict]:
    env = {**os.environ, "LOG_FORMAT": "json", "OTEL_SDK_DISABLED": "true", "PYTHONPATH": "."}
    env.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)
    out = subprocess.run([sys.executable, "-c", textwrap.dedent(code)], env=env, capture_output=True, text=True, check=True)
    return [json.loads(line) for line in (out.stdout + out.stderr).splitlines()]


class LogTests(unittest.TestCase):
    def test_the_reader_logs_one_json_object_per_line(self):
        lines = lines_from("""
            import cyberpunk
            client = cyberpunk.app.test_client()
            client.get("/")
            client.get("/wp-login.php")
        """)
        self.assertEqual([x["route"] for x in lines if x["event"] == "request"], ["/", "other"])
        for line in lines:
            self.assertLessEqual(FIELDS, set(line))
            self.assertEqual(line["service"], "chucks-wisdom-reader")

    def test_the_importer_logs_one_json_object_per_line(self):
        lines = lines_from("""
            import brick_observe
            brick_observe.init("chucks-wisdom-importer")
            import importer

            class Api:
                def find_specific(self, query):
                    return {"result": [{"id": "a", "value": "joke"}]}

            class Storage:
                def check_for_duplicate(self, *_):
                    return False
                def insert_joke(self, *_):
                    pass

            importer.import_search(Api(), Storage(), importer.Settings(query="x"))
        """)
        self.assertIn("new joke", [x["event"] for x in lines])
        for line in lines:
            self.assertLessEqual(FIELDS, set(line))
