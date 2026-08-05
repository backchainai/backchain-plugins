# RB: Worker Queue Backlog

## When to use this

Ingest queue depth alert has fired: more than 50,000 unprocessed messages
for more than 10 minutes.

## Diagnosis

1. Check queue depth by stage: `dataforge queue depth --by-stage`.
2. Identify whether one customer's pipeline is dominating the backlog:
   `dataforge queue depth --by-customer`.
3. Check worker pod health: `kubectl get pods -n dataforge-workers`.

## Mitigation

- If workers are healthy but under-provisioned, scale up:
  `kubectl scale deployment/transform-worker --replicas=12`.
- If one customer is dominating, apply a temporary per-customer rate limit:
  `dataforge queue throttle --customer <id> --rate 100`.
- If a poisoned message is repeating, quarantine it per
  `docs/restart-stalled-pod.md`.
