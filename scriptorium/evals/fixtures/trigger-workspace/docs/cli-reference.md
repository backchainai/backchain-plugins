# DataForge CLI Reference

## Global flags

- `--config <path>`: path to the CLI config file (default `~/.dataforge/config.yaml`).
- `--profile <name>`: named connection profile.
- `--legacy-auth`: use the deprecated username/password auth flow instead of
  the token-based flow. Deprecated; will be removed in a future release.
- `-v` / `--verbose`: increase log verbosity.

## Commands

### `dataforge pipeline run <id>`

Runs a pipeline immediately, ignoring its configured schedule.

### `dataforge pipeline list`

Lists every pipeline visible to the current profile.

### `dataforge worker start --stage <stage>`

Starts a worker process for the given pipeline stage.

### `dataforge doctor`

Checks that every local dependency (database, event bus) is reachable and
prints a pass/fail line per dependency.

### `dataforge hooks register <path>:<function>`

Registers a custom transform hook. See `docs/advanced-usage.md` for the full
hook lifecycle.
