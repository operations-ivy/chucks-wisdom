"""The importer and the reader against a real Postgres: a throwaway
postgres:15 container (the image the cluster runs), initialised by the same
init.sql the cluster's ConfigMap carries. Skipped where Docker isn't
available.

    poetry run pytest tests/test_functional_db.py
"""

from __future__ import annotations

import os
import secrets
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

import yaml

import importer
from importer import Settings
from tests.test_importer import FakeApi, joke

ROOT = Path(__file__).resolve().parent.parent
IMAGE = "postgres:15"


def docker(*args, check=True):
    return subprocess.run(["docker", *args], capture_output=True, text=True, check=check)


@unittest.skipUnless(shutil.which("docker") and docker("info", check=False).returncode == 0, "needs Docker")
class AgainstPostgres(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        configmap = yaml.safe_load((ROOT / "k8s_config/postgres/postgres-configmap.yaml").read_text())
        (cls.tmp / "init.sql").write_text(configmap["data"]["init.sql"])
        cls.tmp.chmod(0o755)
        (cls.tmp / "init.sql").chmod(0o644)
        password = secrets.token_hex(16)  # throwaway, for this container only
        cls.container = docker(
            "run", "-d", "--rm", "-e", "POSTGRES_USER=zaphod", "-e", f"POSTGRES_PASSWORD={password}",
            "-e", "POSTGRES_DB=chuck", "-p", "127.0.0.1::5432",
            "-v", f"{cls.tmp / 'init.sql'}:/docker-entrypoint-initdb.d/init.sql:ro", IMAGE).stdout.strip()
        port = docker("port", cls.container, "5432/tcp").stdout.split(":")[-1].strip()
        cls.url = f"postgresql://zaphod:{password}@127.0.0.1:{port}/chuck"  # secret-scan: allow (password is random per run, throwaway local container)
        # Ready once the init script has made the table (the entrypoint restarts
        # the server after init, so pg_isready alone isn't enough).
        for _ in range(120):
            probe = docker("exec", cls.container, "psql", "-U", "zaphod", "-d", "chuck", "-tAc",
                           "select to_regclass('public.chuck') is not null", check=False)
            if probe.stdout.strip() == "t" and docker("exec", cls.container, "pg_isready", "-h", "127.0.0.1",
                                                      check=False).returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError("Postgres never came up with the chuck table")
        os.environ["DB_CONNECTION_STRING"] = cls.url

    @classmethod
    def tearDownClass(cls):
        docker("rm", "-f", cls.container, check=False)
        os.environ.pop("DB_CONNECTION_STRING", None)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        from sql_storage_operations_ivy.pg_storage import PGStorage
        self.storage = PGStorage(self.url)
        self.storage.conn.execute("TRUNCATE chuck")
        self.storage.conn.commit()

    def tearDown(self):
        self.storage.close_connection()

    def count(self):
        return self.storage.conn.execute("select count(*) from chuck").fetchone()[0]

    def test_the_clusters_init_script_builds_the_schema(self):
        indexes = {r[0] for r in self.storage.conn.execute(
            "select indexname from pg_indexes where tablename = 'chuck'").fetchall()}
        self.assertIn("chuck_id_idx", indexes)
        self.assertIn("chuck_category_value_index", indexes)

    def test_random_import_writes_new_jokes_and_skips_duplicates(self):
        jokes = [joke("a", ["dev"]), joke("b", ["dev"]), joke("a", ["dev"]), joke("c", ["dev"])]
        api = FakeApi(categories=["dev"], jokes=jokes)
        settings = Settings(jokes=3, tries_per_category=4, max_duplicates=5, sleep_seconds=0)
        added = importer.import_random(api, self.storage, settings, sleep=lambda s: None)
        self.assertEqual(added, 3)
        self.assertEqual(self.count(), 3)
        # A second run over the same jokes adds nothing: the duplicate check is real SQL now.
        api = FakeApi(categories=["dev"], jokes=list(jokes))
        settings = Settings(jokes=3, tries_per_category=4, max_duplicates=2, sleep_seconds=0)
        self.assertEqual(importer.import_random(api, self.storage, settings, sleep=lambda s: None), 0)
        self.assertEqual(self.count(), 3)

    def test_search_import(self):
        api = FakeApi(search={"total": 2, "result": [joke("s1", ["food"]), joke("s2")]})
        added = importer.import_search(api, self.storage, Settings(query="pizza", jokes=10))
        self.assertEqual(added, 2)
        self.assertEqual(self.count(), 2)

    def test_reader_serves_what_the_importer_wrote(self):
        importer.import_search(FakeApi(search={"total": 1, "result": [joke("r1", ["dev"])]}),
                               self.storage, Settings(query="x", jokes=10))
        # The app sets up tracing on import; point it nowhere in particular.
        os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4317")
        os.environ.setdefault("OTEL_SDK_DISABLED", "true")
        import cyberpunk
        client = cyberpunk.app.test_client()
        self.assertEqual(client.get("/health").data, b"OK")
        [entry] = client.get("/api").get_json()
        self.assertEqual(len(entry["value"]), 64)  # sha256, never the joke itself
        self.assertNotIn("joke r1", client.get("/api").get_data(as_text=True))
        self.assertEqual(client.get("/").status_code, 200)


if __name__ == "__main__":
    unittest.main()
