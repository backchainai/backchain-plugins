# 0007: Use Postgres as the event store

## Status

Accepted, 2026-03-14

## Context

The order-processing service needs an append-only log of domain events that downstream consumers can replay. Two options were evaluated: a dedicated message log (Kafka) and an append-only table in the existing Postgres cluster.

The reason a message log is normally the default choice is that it decouples producers from consumer throughput and gives every consumer group its own offset. That decoupling matters most at a scale this service does not yet operate at: current peak throughput is under 200 events per second, and the team already operates and backs up the Postgres cluster this service already uses for its transactional data.

Standing up Kafka would mean a new piece of infrastructure to operate, monitor, and back up, with its own failure modes, for a throughput level Postgres handles comfortably with a single append-only table and a sequence-based offset column.

## Decision

Store domain events in a Postgres table, `event_log`, with a monotonically increasing `sequence` column as the replay offset. Consumers poll the table for rows past their last-seen sequence.

To bring a new consumer online:

1. Create a row in `consumer_offsets` for the new consumer, seeded with the sequence of the last event it should skip.
2. Grant the consumer's service account `SELECT` on `event_log` and `SELECT, UPDATE` on its own row in `consumer_offsets`.
3. Deploy the consumer with polling enabled and the offset table name in its configuration.
4. Confirm the consumer's offset advances by checking `consumer_offsets` after its first poll cycle.

## Consequences

Replay is a table scan bounded by the sequence column, not a dedicated log API, and query latency degrades if the table is not pruned. Because a single table serves every consumer, we accept coarser isolation between consumer groups than a dedicated message log would give us, in exchange for not operating a second stateful system to get an event log the current throughput does not require.
