---
id: reference_credential-api
title: Credential API
description: Lists every command and flag the credentials.py CLI exposes for managing Widget Relay service credentials.
type: reference
template: reference
status: current
audience: Platform engineers who already hold secrets-store access.
applies_to: ">=2.4"
created: 2026-07-15
updated: 2026-07-28
owner: widget-relay-platform
tags: [security, credentials, api]
source: [credentials.py]
reviewed_by: jordan-lee
reviewed_on: 2026-07-28
---

# Credential API

This page documents every command `credentials.py` exposes.

## `rotate-api-key`

Issues a new API key, overlaps it with the old key for a configurable window, then revokes the old key.

| Flag | Type | Required | Default | Description |
|---|---|---|---|---|
| `--key-id` | string | yes | none | The id of the key to rotate. |
| `--overlap-hours` | integer | no | `24` | Hours the old and new keys are both valid before the old key is revoked. |
| `--dry-run` | flag | no | `false` | Print the planned actions without executing them. |

**Effect:** issues a new key, waits for the overlap window if `--dry-run` is not set, and revokes the old key at the end of the window. Returns exit code `0` on success, `2` on an unknown command.

**Example:**

```console
python credentials.py rotate-api-key --key-id svc-relay-01 --overlap-hours 24
```
