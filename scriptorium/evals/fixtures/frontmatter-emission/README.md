# Widget Relay

Widget Relay is a webhook relay you self-host between two systems that do not speak to each other directly. It buffers events in a queue and retries delivery with backoff until the downstream system acknowledges receipt.

Current version: 2.4.0.

See `docs/reference_credential-api.md` for the credential API this project exposes, and `credentials.py` for the CLI that manages service credentials.
