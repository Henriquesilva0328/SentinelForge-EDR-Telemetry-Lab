# From Event to Alert

This document shows the practical flow from a single endpoint telemetry event to a stored alert.

## Scenario

A process event is sent with:

- `process_name = powershell.exe`
- `command_line` containing `-EncodedCommand`

This is expected to trigger rule `PROC-PS-ENC-001`.

## Step 1. Event ingestion

The client sends a JSON payload to:

`POST /api/v1/events`

The API validates:

- Bearer token
- content-type
- request size
- schema contract
- payload structure

## Step 2. Raw persistence

If accepted, the event is stored in `raw_events`.

The system also writes an ingest audit entry to `ingest_audit`.

## Step 3. Raw Kafka publication

The API publishes the accepted event to Kafka topic:

`telemetry.raw.ingested`

## Step 4. Normalization

The normalizer worker consumes the raw Kafka message and transforms it into a normalized internal document.

For a PowerShell process event, the normalized output contains fields such as:

- `category = process`
- `event_action = process_start`
- `process_name = powershell.exe`
- `process_pid = 1234`

The normalized record is stored in `normalized_events`.

## Step 5. Normalized Kafka publication

The normalizer republishes the structured event to:

`telemetry.normalized`

## Step 6. Detection

The detector worker consumes the normalized event and evaluates current rules.

For the encoded PowerShell case, the rule engine detects:

- process category
- process name equals `powershell.exe`
- command line contains encoded command indicators

## Step 7. Alert generation

The detector stores an alert in `alerts` and evidence in `alert_evidence`.

Typical alert result:

- `rule_id = PROC-PS-ENC-001`
- `severity = high`
- title describing encoded PowerShell execution

## Step 8. Evidence

The evidence record contains a structured explanation of why the alert fired, including fields such as:

- command line
- event action
- process name
- raw event id
- normalized event id

## Why this matters

This end-to-end flow proves that the project is not just receiving logs. It is:

- validating contracts
- preserving raw truth
- creating internal normalized representations
- evaluating detection content
- producing explainable alerts
- keeping the full flow reproducible