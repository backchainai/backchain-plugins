# Install Postgres for DataForge

DataForge's ingest workers need a local Postgres instance for the pipeline
metadata store. This walks through getting one running on a dev machine.

## Prerequisites

- Docker 24+
- 4 GB free disk for the volume
- The `dataforge` CLI already installed (`pip install dataforge-cli`)

## Steps

1. Pull the pinned image: `docker pull postgres:16.3`.
2. Create a named volume: `docker volume create dataforge-pg-data`.
3. Start the container:

   ```
   docker run -d --name dataforge-pg \
     -e POSTGRES_PASSWORD=devpassword \
     -v dataforge-pg-data:/var/lib/postgresql/data \
     -p 5432:5432 postgres:16.3
   ```

4. Run the DataForge schema bootstrap: `dataforge db bootstrap --local`.
5. Confirm the pipeline-runs table exists: `dataforge db shell -c '\dt'`.

## Verifying the connection

Point `DATAFORGE_DATABASE_URL` at `postgresql://postgres:devpassword@localhost:5432/postgres`
and run `dataforge doctor`. A green `database: ok` line confirms the ingest
worker can reach it.

## Tearing down

`docker rm -f dataforge-pg && docker volume rm dataforge-pg-data` removes the
container and its data. Do this before switching branches that carry a
different schema migration head.
