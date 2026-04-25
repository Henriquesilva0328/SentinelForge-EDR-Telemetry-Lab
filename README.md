# SentinelForge-EDR-Telemetry-Lab

SentinelForge EDR Telemetry Lab is an event-driven endpoint telemetry and detection pipeline designed to simulate a realistic Blue Team and Detection Engineering workflow.

The project receives endpoint telemetry, validates ingestion contracts, stores raw events, normalizes data, publishes processing stages through Kafka, applies detection rules, generates alerts with evidence, exposes Prometheus metrics, and supports replay-based validation with benchmark reports.

## Key capabilities

- secure telemetry ingestion with request validation and hardening
- raw event persistence and audit trail
- asynchronous Kafka-based pipeline
- event normalization and structured internal representation
- rule-based alert generation with evidence
- Prometheus and Grafana observability
- replay datasets for validation and false positive benchmarking

## Architecture overview

The pipeline follows this sequence:

1. An endpoint telemetry event is sent to the ingest API.
2. The API validates authentication, content type, request size, and payload structure.
3. The raw event is stored in PostgreSQL.
4. The raw event is published to Kafka.
5. The normalizer worker consumes the raw Kafka message.
6. A normalized event is created and stored.
7. The normalized event is published to Kafka.
8. The detector worker consumes the normalized message.
9. Detection rules are evaluated.
10. Alerts and structured evidence are persisted.
11. Metrics are exposed for operational visibility.

## Core technologies

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Kafka
- Prometheus
- Grafana
- pytest
- Ruff

## Project structure

```text
sentinelforge-edr/
├── alembic/
├── datasets/
│   └── replay/
├── deploy/
│   ├── compose/
│   └── prometheus/
├── docs/
│   └── pt-br/
├── src/
│   └── sentinelforge/
│       ├── api/
│       ├── core/
│       ├── db/
│       ├── messaging/
│       ├── middleware/
│       ├── models/
│       ├── observability/
│       ├── replay/
│       ├── schemas/
│       ├── services/
│       └── workers/
├── tests/
└── README.md

## Additional Documentation

- [Architecture](docs/architecture.md)
- [From Event to Alert](docs/from-event-to-alert.md)
- [Rules and Benchmark](docs/rules-and-benchmark.md)
- [Portfolio Snippets](docs/portfolio-snippets.md)
- [Resumo em Português](docs/pt-br/resumo-do-projeto.md)