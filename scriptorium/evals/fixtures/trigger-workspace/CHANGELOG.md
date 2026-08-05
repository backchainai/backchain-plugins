# Changelog

All notable changes to DataForge are documented here. Format loosely follows
Keep a Changelog.

## [4.1.0] - 2026-06-18

### Added
- `dataforge hooks register` for custom transform hooks (see
  `docs/advanced-usage.md`).
- Per-pipeline retry policy override via `--retry-policy`.

### Fixed
- Worker pods no longer crash-loop when a poisoned message repeats past the
  queue's redelivery limit; it is now quarantined automatically.

## [4.0.0] - 2026-04-02

### Changed
- Internal scheduler-to-worker calls moved from REST to gRPC (see
  `docs/decisions/0004-rest-to-grpc.md`).

### Breaking
- `dataforge pipeline run` no longer accepts a bare pipeline name; it
  requires `--pipeline <id>` explicitly.

## [3.6.0] - 2026-02-14

### Added
- Event-sourced pipeline run history, replacing the mutable `pipeline_runs`
  row (see `docs/why-event-sourcing.md`).
