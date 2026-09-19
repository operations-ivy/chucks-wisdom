# Deploying chucks-wisdom onto the cluster

This is the runbook for deploying `k8s_config/` onto the k3s cluster. Two
nodes:

| Role                          | Hostname    | IP             | k3s mode | Notes                                  |
|-------------------------------|-------------|----------------|----------|------------------------------------------|
| control-plane ("MAIN")        | `brick420`  | 192.168.1.183  | server   | Smaller disk (29G SD card) — runs the API server, scheduler, controller-manager. Also schedules stateless pods (reader, importer). |
| worker ("WORKER")              | `brick2000` | 192.168.1.170  | agent    | Larger disk (917G NVMe) — labeled `chuck.io/storage-node=true` so Postgres (and its PVC) always lands here. |

Both run as user `zaphod` with the laptop's SSH key already authorized.

**Cluster bootstrap (installing k3s, joining the worker, the dashboard) lives
in the separate
[`brick-k8s-config`](https://github.com/operations-ivy/brick-k8s-config) repo
now** — that's cluster infrastructure, not specific to this app, so it moved
out. This doc picks up assuming the cluster is already up and
`~/.kube/chuck-config` already works (`brick-k8s-config`'s README covers
getting there, including the `chuck.io/storage-node=true` label on
`brick2000` that `postgres-deployment.yaml`'s `nodeSelector` depends on).

## 5. Deploy chucks-wisdom

If you don't have local `kubectl`, copy the manifests over and apply them
with the control-plane node's own `k3s kubectl`:

```bash
scp -r k8s_config zaphod@192.168.1.183:/tmp/k8s_config

ssh zaphod@192.168.1.183 '
  sudo k3s kubectl apply -f /tmp/k8s_config/chuck-namespace.yaml
  sudo k3s kubectl apply -f /tmp/k8s_config/postgres/
  sudo k3s kubectl apply -f /tmp/k8s_config/reader/
  sudo k3s kubectl apply -f /tmp/k8s_config/importer/importer-job.yaml
  sudo k3s kubectl apply -f /tmp/k8s_config/metrics/metrics-service.yaml
'
# metrics-service-monitor.yaml only applies if kube-prometheus-stack's CRDs are installed
```

(With local `kubectl` and `KUBECONFIG` set to `~/.kube/chuck-config`, just run
the same `kubectl apply -f k8s_config/...` commands directly from the repo
root.)

Check rollout:

```bash
ssh zaphod@192.168.1.183 sudo k3s kubectl -n chuck get pods -o wide
# postgres should show NODE brick2000; reader/importer can land on either
```

The importer pod may restart once or twice at first boot — it's racing
Postgres's startup and is caught by the Job's `restartPolicy: OnFailure` /
`backoffLimit: 3`, not a real failure.

## 6. Reach the reader

k3s's built-in ServiceLB fronts Traefik on **every** node's IP, so either
works:

```bash
# on your workstation
echo "192.168.1.183 reader.local" | sudo tee -a /etc/hosts
```

Then `curl http://reader.local/` or open it in a browser.

Kubernetes Dashboard is deployed separately, from `brick-k8s-config` — see
that repo's README.

## Re-running the importer

The importer is a `Job`, so it runs once and completes. To re-import:

```bash
ssh zaphod@192.168.1.183 '
  sudo k3s kubectl -n chuck delete job importer
  sudo k3s kubectl apply -f /tmp/k8s_config/importer/importer-job.yaml
'
```
