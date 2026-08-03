# Deploy the service

You need `kubectl` configured against the target cluster and a deploy token for the container registry before starting.

1. Fetch the release tag you are shipping with `git fetch --tags` and check it out.
2. Pull the published container image for that release tag from the registry using the deploy token.
3. Apply the manifests in `deploy/` against the target cluster.
4. Watch the rollout with `kubectl rollout status deployment/api` until it reports complete.
5. Confirm the health check endpoint returns 200 before closing out the deploy.
