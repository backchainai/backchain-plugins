# CLAUDE.md

Guidance for Claude Code working in the DataForge repository.

## Repository

DataForge is a managed data-pipeline platform (extract, transform, load).
The scheduler, ingest, transform, and load services live under `src/`;
customer-facing documentation lives under `docs/`.

## Before committing

Always run `make test` before every commit, even for a one-line change. The
suite is fast enough (under 90 seconds) that there is no good reason to skip
it. Do not commit if `make test` fails.

## Before pushing

Run `make test-integration` before pushing, since it needs the Kafka
container and is too slow to run on every commit.

## Style

- Python: `ruff format` and `ruff check` must both pass.
- Commit messages: imperative mood, first line under 72 characters.
- Never commit `.env` or anything under `secrets/`.
