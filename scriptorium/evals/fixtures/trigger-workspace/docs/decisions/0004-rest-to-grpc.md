# 0004: Move the Internal Service Mesh from REST to gRPC

## Status

Accepted, 2026-05-12.

## Context

DataForge's internal services (scheduler, ingest, transform, load) call each
other over plain REST/JSON today. As pipeline volume grew, serialization
overhead and connection churn on the scheduler-to-worker path became
measurable in production latency, and the JSON schema drift between services
had caused two incidents where a field rename in one service silently broke
another's parsing.

## Decision

The internal service mesh moves to gRPC with protobuf-defined contracts.
External-facing APIs (the customer-facing REST API documented in
`docs/api-reference.md`) are unaffected; this decision governs only
service-to-service calls inside the cluster.

## Alternatives considered

- **Keep REST, add a shared JSON schema registry.** Would have caught the
  field-rename class of incident but does nothing for serialization
  overhead, and a registry is itself another service to operate.
- **GraphQL federation.** Solves schema drift but adds a gateway layer and a
  query language mismatch with the mostly-fixed-shape internal calls DataForge
  makes; the flexibility GraphQL buys was not needed internally.
- **gRPC (chosen).** Protobuf contracts are generated into both client and
  server code, so a field rename fails at compile time rather than at
  runtime, and binary serialization removed the JSON overhead entirely in
  benchmarking.

## Consequences

Every internal service needs a `.proto` file and generated stubs in CI. The
migration is staged service-pair by service-pair, starting with
scheduler-to-worker, the pair that produced both incidents.
