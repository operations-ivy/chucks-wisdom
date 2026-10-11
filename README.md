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
