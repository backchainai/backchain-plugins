# Incident Response: P1

## Scope

Any incident that stops pipeline runs for more than one customer at once.

## First five minutes

1. Declare the incident in `#incidents` and start a timeline doc.
2. Assign an incident commander; the on-call engineer is IC by default
   until someone explicitly takes over.
3. Check the status page and post an initial "investigating" update.

## Investigation

Pull the last 30 minutes of scheduler logs and the event bus's
`pipeline.failed` topic for the affected pipelines. Cross-reference against
the most recent deploy; most P1s in the last year traced back to a deploy
in the prior hour.

## Closing out

Once mitigated, post a resolution update on the status page and file a
follow-up for the postmortem within 24 hours.
