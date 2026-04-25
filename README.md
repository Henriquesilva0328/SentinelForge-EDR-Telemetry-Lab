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