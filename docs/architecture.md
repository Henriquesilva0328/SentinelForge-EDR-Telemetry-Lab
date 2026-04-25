# SentinelForge Architecture

## Purpose

This document explains the technical architecture of SentinelForge EDR Telemetry Lab and how its main components interact.

## High-level components

### Ingest API

The ingest API is responsible for receiving endpoint telemetry from agents or simulated producers.

Main responsibilities:

- authenticate requests
- validate schema and payload constraints
- reject malformed or unsafe requests
- persist raw events
- record ingest audit trail
- publish accepted raw events to Kafka

### PostgreSQL

PostgreSQL acts as the system of record for:

- raw events
- ingest audit
- ingest rejection audit
- normalized events
- alerts
- alert evidence

### Kafka

Kafka acts as the asynchronous transport layer between processing stages.

Current topics:

- `telemetry.raw.ingested`
- `telemetry.normalized`

### Normalizer worker

The normalizer worker consumes raw ingested events, transforms them into an internal normalized format, stores normalized records, and republishes them to the next Kafka stage.

### Detector worker

The detector worker consumes normalized events, evaluates detection rules, and creates alerts plus evidence when a rule matches.

### Prometheus and Grafana

Prometheus scrapes metrics from the API and workers. Grafana is used to visualize operational health and pipeline behavior.

## Data flow

1. The ingest API receives telemetry.
2. Request guards and validation are applied.
3. The raw event is written to the database.
4. The raw event is published to Kafka.
5. The normalizer worker consumes the raw Kafka message.
6. The normalized event is stored in the database.
7. The normalized event is published to Kafka.
8. The detector worker consumes the normalized message.
9. The rule engine evaluates the event.
10. Alerts and evidence are stored.
11. Metrics are exposed for observability.

## Security design choices

Current hardening includes:

- Bearer token gate for ingestion
- JSON-only ingest enforcement
- request body size limits
- nested payload validation limits
- structured rejection auditing
- secure response headers
- hidden docs outside local and dev environments

## Design trade-offs

### Direct database plus Kafka publish

The ingest stage currently persists to PostgreSQL and then publishes to Kafka in the same flow. This is acceptable for a lab, but a production system would likely use an outbox pattern to reduce dual-write risk.

### Rule engine simplicity

Rules are intentionally small and explicit. This keeps behavior easy to demonstrate and benchmark, even though it is not yet a full detection content platform.

### Reproducibility over scale

The replay benchmark is optimized for deterministic validation, not high-throughput load simulation.

## Current detection maturity

The project already demonstrates:

- deduplicated ingestion
- normalized processing stages
- asynchronous worker topology
- traceable event-to-alert flow
- replay-based validation
- basic false positive benchmarking

## Future evolution

Suggested future improvements:

- outbox pattern for publish reliability
- richer event normalization coverage
- more detection rules and suppression logic
- ATT&CK mapping per rule
- correlation windows across multiple events
- stronger agent authentication
- CI replay job for regression detection