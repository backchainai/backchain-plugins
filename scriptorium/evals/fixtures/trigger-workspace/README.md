# DataForge

[![Build](https://img.shields.io/badge/build-passing-brightgreen)](https://ci.dataforge.io)
[![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen)](https://ci.dataforge.io)
[![PyPI](https://img.shields.io/badge/pypi-v4.1.0-blue)](https://pypi.org/project/dataforge-cli)
[![License](https://img.shields.io/badge/license-Apache--2.0-lightgrey)](LICENSE)
[![Slack](https://img.shields.io/badge/slack-join-4A154B)](https://dataforge.io/slack)
[![Docs](https://img.shields.io/badge/docs-latest-orange)](https://docs.dataforge.io)

DataForge is a managed data-pipeline platform: extract, transform, and load
data between the systems our customers already run, without hand-writing and
babysitting glue scripts.

## History

DataForge started in 2023 as an internal tool for moving CSV exports into a
warehouse without a nightly cron job breaking silently. It became a standalone
product in 2024 after three other teams asked to use the internal tool, and
the event bus described in `docs/understanding-our-event-bus.md` was added
that year to decouple the growing number of pipeline stages from each other.
Event sourcing replaced the original mutable run-history table in 2026 (see
`docs/why-event-sourcing.md`), and the internal service mesh moved from REST
to gRPC the same year (see `docs/decisions/0004-rest-to-grpc.md`). The
project has had three different logos and two different names before
settling on DataForge; the earlier name is still referenced in some old
support tickets and should not be used in new material.

## Installation

```
pip install dataforge-cli
dataforge doctor
```

See `docs/local-environment-setup.md` for the full local development setup,
including the Postgres and Kafka containers.

## Contributing

Pull requests welcome. Run `make test` before submitting.
