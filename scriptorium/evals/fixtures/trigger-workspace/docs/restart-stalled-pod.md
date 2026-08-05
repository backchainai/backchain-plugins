# Restart a Stalled Kubernetes Pod

## How the DataForge scheduler assigns pods

Every ingest job DataForge accepts is handed to the scheduler, which binds it
to a worker pod in the `dataforge-workers` namespace. The scheduler tracks
pod health through a liveness probe hitting `/healthz` every 10 seconds and
reassigns a job only after three consecutive probe failures, which is why a
pod can sit in a degraded state for up to 30 seconds before the scheduler
notices anything is wrong.

## Why pods crash-loop under DataForge's ingest load

A worker pod crash-loops most often because its ingest queue backs up faster
than the pod can drain it: memory climbs past the container's limit, the
kubelet OOM-kills the process, and the pod restarts into the same backlog.
A second common cause is a poisoned message: one malformed record repeatedly
throws during deserialization, the pod exits non-zero, and Kubernetes retries
the exact same message on restart. Both causes look identical from `kubectl
get pods` alone; the difference only shows up in the pod's last-terminated
reason.

## Restarting a stalled pod

1. Identify the pod: `kubectl get pods -n dataforge-workers | grep Stalled`.
2. Check the termination reason: `kubectl describe pod <pod> -n dataforge-workers`.
3. If OOMKilled, bump the pod's memory limit in `worker-deployment.yaml` and
   redeploy: `kubectl apply -f worker-deployment.yaml`.
4. If a poisoned message, quarantine it: `dataforge queue quarantine <msg-id>`.
5. Delete the stalled pod so the deployment recreates it cleanly:
   `kubectl delete pod <pod> -n dataforge-workers`.
6. Confirm recovery: `kubectl get pods -n dataforge-workers -w`.
