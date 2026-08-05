# DataForge API Reference

Base URL: `https://api.dataforge.io/v1`. All endpoints require a bearer
token in the `Authorization` header.  

### Pipelines

`GET /pipelines` lists every pipeline the caller can see, paginated with
`?cursor=`.

`POST /pipelines` creates a pipeline from a `source`, a `destination`, and an
ordered list of `transforms`.  

##### Pipeline runs

`GET /pipelines/{id}/runs` lists runs for a pipeline, newest first.

`POST /pipelines/{id}/runs` starts a run immediately, ignoring the pipeline's
configured schedule.

## Webhooks

`POST /webhooks` registers a callback URL that receives a `run.completed` or
`run.failed` event.  

Every webhook payload is signed; verify it against the `X-DataForge-Signature`
header before trusting the body.

### Rate limits

100 requests per minute per API key, `429` with a `Retry-After` header once
exceeded.
