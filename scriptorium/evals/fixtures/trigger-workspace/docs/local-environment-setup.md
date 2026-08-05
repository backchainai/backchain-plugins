# Local Environment Setup

## Requirements

- `dataforge-cli` >= 2.4
- Docker 24+
- Python 3.12+
- `make`

## Bootstrap

```
git clone git@github.com:dataforge/dataforge.git
cd dataforge
make bootstrap
```

`make bootstrap` starts the local Postgres and Kafka containers, runs schema migrations, and seeds a demo pipeline named `demo-csv-to-warehouse`.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DATAFORGE_ENV` | `local` | Selects the config profile |
| `DATAFORGE_DATABASE_URL` | `postgresql://localhost:5432/dataforge` | Metadata store |
| `DATAFORGE_KAFKA_BROKERS` | `localhost:9092` | Event bus |
| `DATAFORGE_LOG_LEVEL` | `info` | Logger verbosity |

## Common commands

- `dataforge pipeline run demo-csv-to-warehouse` runs the seeded demo.
- `dataforge worker start --stage transform` starts a transform worker.
- `dataforge doctor` checks that every local dependency is reachable.
- `make test` runs the unit suite; `make test-integration` also needs the
  Kafka container up.

## Resetting

`make reset` tears down and re-seeds the local containers, for when a
migration has drifted the schema out from under your working branch.
