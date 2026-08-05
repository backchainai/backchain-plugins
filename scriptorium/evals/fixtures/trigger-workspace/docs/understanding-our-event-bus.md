# Understanding our Event Bus

DataForge's pipelines communicate through an internal event bus rather than
direct service calls. Every stage of a pipeline (extract, transform, load)
publishes a record of what it did, and downstream stages subscribe to the
records they care about instead of being wired to a specific upstream
service. This decoupling is what lets a customer add a new transform stage
without redeploying the extractor that feeds it, and it is why a single slow
subscriber never blocks a fast one: each reads the bus at its own pace.

The bus itself is a thin wrapper over Kafka topics, one topic per pipeline
stage, and every event on it carries a pipeline run ID so a failure in one
customer's run never gets attributed to another's.

## Topics and payloads

| Topic | Published by | Payload |
|---|---|---|
| `ingest.received` | Extract stage | `{run_id, source, row_count, received_at}` |
| `transform.applied` | Transform stage | `{run_id, rules_applied, row_count, duration_ms}` |
| `load.completed` | Load stage | `{run_id, destination, row_count, completed_at}` |
| `pipeline.failed` | Any stage | `{run_id, stage, error_code, message}` |

Consumers subscribe by topic name; there is no wildcard subscription today,
which is a known limitation tracked separately from this document.
