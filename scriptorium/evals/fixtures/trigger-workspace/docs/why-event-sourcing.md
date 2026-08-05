# Why We Chose Event Sourcing over CRUD

DataForge's pipeline-run history originally lived in a CRUD table: one row
per run, updated in place as the run progressed through extract, transform,
and load. That table could never answer "what did this run's state look like
five minutes ago," which support needed constantly when a customer reported
a pipeline that had "changed" without them touching it. A CRUD row only ever
shows the current state; the history that produced it is gone the moment the
next update lands.

Event sourcing replaces the row with an append-only log of everything that
happened to a run: `run.started`, `stage.completed`, `stage.retried`,
`run.failed`, `run.completed`. Current state is a projection over that log,
computed on read, and any past state is the same projection truncated to an
earlier point in the log. Support can now answer "what did this look like"
by replaying the log up to a timestamp, and a bug in the projection logic is
recoverable by replaying from the same untouched log rather than by restoring
a backup.

This did move the hard part of the system from storage to replay
performance, which is the tradeoff the team accepted deliberately: a
projection that reads the whole log for every request does not scale, so a
snapshot needed to be part of the design from the start.

## Migrating an existing pipeline table

1. Stand up the `pipeline_events` append-only table alongside the existing
   `pipeline_runs` table; do not touch the old table yet.
2. Dual-write: every state change writes to both the old row and a new event.
3. Backfill history for existing runs into `pipeline_events` from the audit
   log, best-effort, marking gaps explicitly rather than guessing.
4. Switch reads to the projection, one endpoint at a time, behind a flag.
5. Once every read path uses the projection, stop writing to `pipeline_runs`
   and drop it in a follow-up release.
