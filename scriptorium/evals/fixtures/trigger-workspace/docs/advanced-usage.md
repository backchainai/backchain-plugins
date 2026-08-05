# Advanced Usage

## Why we built custom transform hooks

The built-in transform stages (filter, map, dedupe) cover most pipelines, but
several customers needed logic that touches an external system mid-run: a
lookup against a customer's own reference database, or a call to a
third-party enrichment API. Rather than growing the built-in stage list
without bound, DataForge exposes a `transform_hook` extension point so a
customer's own code runs inside the pipeline without becoming a first-class
stage type we have to maintain.

## Migrating a pipeline to use a custom hook

1. Write the hook as a Python function taking a `Record` and returning a
   `Record` or `None` (returning `None` drops the record).
2. Register it: `dataforge hooks register my_hook.py:enrich`.
3. Reference it in the pipeline definition: add `{"hook": "enrich"}` to the
   `transforms` list, in the position the enrichment should run.
4. Deploy to a staging pipeline first; hooks run with the same timeout as a
   built-in stage (30s), and a hook that exceeds it fails the run.
5. Once staging runs clean for 24 hours, promote the pipeline definition to
   production.

## Hook configuration options

| Option | Type | Default | Purpose |
|---|---|---|---|
| `timeout_s` | int | 30 | Max seconds before the hook run is killed |
| `retries` | int | 0 | Retries on a transient exception |
| `on_error` | string | `fail` | `fail`, `skip`, or `quarantine` the record |
| `concurrency` | int | 4 | Parallel hook invocations per worker |
