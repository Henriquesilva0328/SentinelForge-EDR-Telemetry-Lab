# SentinelForge EDR Telemetry Lab

O SentinelForge EDR Telemetry Lab é um pipeline orientado a eventos para ingestão de telemetria de endpoint e geração de detecções, projetado para simular um fluxo realista de Blue Team, SOC e Detection Engineering.

O projeto recebe eventos de telemetria, valida contratos de ingestão, armazena eventos brutos, normaliza os dados, publica etapas de processamento por Kafka, aplica regras de detecção, gera alertas com evidências, expõe métricas com Prometheus e suporta validação reproduzível com datasets de replay e benchmark.

## Capacidades principais

- ingestão segura de telemetria com validação e hardening
- persistência de eventos brutos e trilha de auditoria
- pipeline assíncrono baseado em Kafka
- normalização de eventos para formato interno consistente
- geração de alertas baseada em regras com evidência estruturada
- observabilidade com Prometheus e Grafana
- datasets de replay para validação e benchmark de falso positivo

## Tecnologias principais

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

## Diferencial do projeto

O principal diferencial do SentinelForge não é apenas receber eventos e gerar um alerta isolado. O projeto foi desenhado para demonstrar um fluxo completo de engenharia de detecção:

- entrada segura
- persistência bruta
- processamento assíncrono
- normalização
- detecção baseada em regras
- geração de evidência
- observabilidade operacional
- benchmark reproduzível