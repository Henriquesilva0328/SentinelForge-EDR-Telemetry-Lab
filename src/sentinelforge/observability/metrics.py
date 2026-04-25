from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    start_http_server,
)

_HTTP_REQUESTS_TOTAL = Counter(
    "sentinelforge_http_requests_total",
    "Total de requests HTTP recebidas pela API.",
    ["method", "path", "status_code"],
)

_HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "sentinelforge_http_request_duration_seconds",
    "Latência das requests HTTP da API.",
    ["method", "path"],
)

_INGEST_EVENTS_TOTAL = Counter(
    "sentinelforge_ingest_events_total",
    "Total de decisões de ingestão por categoria.",
    ["decision", "category"],
)

_KAFKA_PUBLISH_TOTAL = Counter(
    "sentinelforge_kafka_publish_total",
    "Total de publicações Kafka por tópico e resultado.",
    ["topic", "result"],
)

_NORMALIZATION_EVENTS_TOTAL = Counter(
    "sentinelforge_normalization_events_total",
    "Total de resultados da normalização.",
    ["decision", "category", "event_action"],
)

_DETECTION_MATCHES_TOTAL = Counter(
    "sentinelforge_detection_matches_total",
    "Total de matches produzidos pelo motor de regras.",
    ["rule_id", "severity"],
)

_ALERTS_CREATED_TOTAL = Counter(
    "sentinelforge_alerts_created_total",
    "Total de alertas criados por regra.",
    ["rule_id", "severity"],
)

_WORKER_UP = Gauge(
    "sentinelforge_worker_up",
    "Indica se o worker está ativo.",
    ["worker"],
)

_WORKER_MESSAGES_TOTAL = Counter(
    "sentinelforge_worker_messages_total",
    "Total de mensagens tratadas por worker e resultado.",
    ["worker", "result"],
)

_STARTED_WORKER_METRICS_PORTS: set[int] = set()


def generate_metrics_payload() -> bytes:
    return generate_latest()


def metrics_content_type() -> str:
    return CONTENT_TYPE_LATEST


def observe_http_request(
    *,
    method: str,
    path: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    _HTTP_REQUESTS_TOTAL.labels(
        method=method,
        path=path,
        status_code=str(status_code),
    ).inc()

    _HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        path=path,
    ).observe(duration_seconds)


def observe_ingest_result(*, decision: str, category: str) -> None:
    _INGEST_EVENTS_TOTAL.labels(
        decision=decision,
        category=category,
    ).inc()


def observe_kafka_publish(*, topic: str, result: str) -> None:
    _KAFKA_PUBLISH_TOTAL.labels(
        topic=topic,
        result=result,
    ).inc()


def observe_normalization_result(
    *,
    decision: str,
    category: str,
    event_action: str,
) -> None:
    _NORMALIZATION_EVENTS_TOTAL.labels(
        decision=decision,
        category=category,
        event_action=event_action,
    ).inc()


def observe_detection_match(*, rule_id: str, severity: str) -> None:
    _DETECTION_MATCHES_TOTAL.labels(
        rule_id=rule_id,
        severity=severity,
    ).inc()


def observe_alert_created(*, rule_id: str, severity: str) -> None:
    _ALERTS_CREATED_TOTAL.labels(
        rule_id=rule_id,
        severity=severity,
    ).inc()


def start_worker_metrics_server(*, worker: str, port: int) -> None:
    if port in _STARTED_WORKER_METRICS_PORTS:
        _WORKER_UP.labels(worker=worker).set(1)
        return

    start_http_server(port)
    _STARTED_WORKER_METRICS_PORTS.add(port)
    _WORKER_UP.labels(worker=worker).set(1)


def set_worker_down(*, worker: str) -> None:
    _WORKER_UP.labels(worker=worker).set(0)


def observe_worker_message_result(*, worker: str, result: str) -> None:
    _WORKER_MESSAGES_TOTAL.labels(
        worker=worker,
        result=result,
    ).inc()