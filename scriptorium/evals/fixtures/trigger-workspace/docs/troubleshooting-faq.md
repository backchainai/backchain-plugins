# Troubleshooting FAQ

**My pipeline is stuck in "pending."**
Check that a worker for the pipeline's first stage is actually running.
`dataforge worker start --stage extract` if not.

**Why did my run fail with `SchemaMismatch`?**
The source's columns changed since the pipeline was last configured. Update
the pipeline's field mapping; DataForge does not infer this for you.

**I keep getting rate limited.**
You're over your plan's request budget. Read the docs before opening a
ticket about this.

**My webhook never fires.**
Nine times out of ten this is a firewall blocking DataForge's egress IPs.
Check that before assuming it's our bug.

**Can I rename a pipeline after creating it?**
Yes: `dataforge pipeline rename <id> <new-name>`. This does not change the
pipeline's `id`, only its display name.

**Why is my transform hook timing out?**
Hooks have a 30-second timeout by default. If yours legitimately needs
longer, set `timeout_s` in the hook's config, but consider whether the work
belongs in a hook at all first.
