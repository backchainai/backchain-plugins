# On-Call: Database Failover

Severity mapping: this runbook applies to SEV1 and SEV2 incidents involving
the primary Postgres instance.

## Symptoms

- `dataforge doctor` reports `database: unreachable`.
- Ingest workers logging repeated connection timeouts.

## Steps

1. Confirm the primary is actually down: `dataforge db status --verbose`.
2. Promote the standby: `dataforge db promote-standby --region us-east-1`.
3. Point `DATAFORGE_DATABASE_URL` at the new primary via the config service.
4. Restart all workers so they pick up the new connection string:
   `dataforge worker restart --all`.
5. Page the on-call DBA to rebuild a new standby from the promoted primary.

## Rollback

If promotion fails partway, do not attempt a second promotion without DBA
sign-off; page immediately instead.
