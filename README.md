# chucks-wisdom

A joke importer (a Kubernetes Job) and a reader app over Postgres. Cluster
setup: `k8s_config/CLUSTER_SETUP.md`.

## Tests

```bash
poetry run pytest
```

`tests/test_importer.py` unit-tests the importer with a fake API and fake
storage. `tests/test_functional_db.py` runs the importer and the reader
against a real Postgres: a throwaway `postgres:15` container (the cluster's
image) with a one-off password, initialised by the `init.sql` from
`k8s_config/postgres/postgres-configmap.yaml`, so the cluster's schema script
is tested too. It covers the schema, random and search imports (with the
duplicate check running as real SQL), and the reader serving hashes of what
the importer wrote. Those tests are skipped where Docker isn't available.
`tests/test_reader_metrics.py` checks the reader's metrics with Flask's
test client. `tests/test_logs.py` checks both programs write one JSON
object per line.

## Metrics

Logs, traces and request metrics come from
[brick-observe](https://github.com/operations-ivy/brick-observe). The reader
serves `/metrics`: its `http_server_*` requests and durations by route, and
from `metrics.py` how long reading every joke from Postgres takes, failed
reads, and how many jokes the last read returned. An importer run also pushes
its result to the Pushgateway (`job_*`, job `chuck-importer`). Postgres has a `postgres-exporter`
sidecar (connections, transactions, rows, sizes, cache hits, deadlocks).
`k8s_config/metrics/podmonitor.yaml` has Prometheus scrape both, and the
"Chuck's wisdom: reader and Postgres" dashboard
(`k8s_config/metrics/reader-dashboard-configmap.yaml`) draws them. The
importer's own counters still go through its Service and ServiceMonitor.
