# Do evento ao alerta

Este documento explica o fluxo completo de um evento de telemetria dentro do SentinelForge.

## Cenário

Um evento de processo é enviado com:

- `process_name = powershell.exe`
- `command_line` contendo `-EncodedCommand`

Esse cenário deve disparar a regra `PROC-PS-ENC-001`.

## Etapa 1. Ingestão

O cliente envia um evento para:

`POST /api/v1/events`

A API valida:

- token Bearer
- content-type
- tamanho da request
- contrato do schema
- estrutura do payload

## Etapa 2. Persistência bruta

Se o evento for aceito, ele é salvo em `raw_events`.

Além disso, o sistema registra uma trilha de auditoria em `ingest_audit`.

## Etapa 3. Publicação no Kafka bruto

A API publica o evento aceito no tópico:

`telemetry.raw.ingested`

## Etapa 4. Normalização

O worker de normalização consome a mensagem do Kafka e transforma o evento em um formato interno consistente.

No caso de um evento de processo PowerShell, o evento normalizado contém campos como:

- `category = process`
- `event_action = process_start`
- `process_name = powershell.exe`
- `process_pid = 1234`

O resultado é salvo em `normalized_events`.

## Etapa 5. Publicação no Kafka normalizado

O normalizador republica o evento estruturado para o tópico:

`telemetry.normalized`

## Etapa 6. Detecção

O worker detector consome o evento normalizado e avalia as regras atuais.

No caso do PowerShell codificado, a lógica identifica:

- categoria de processo
- nome do processo igual a `powershell.exe`
- command line com indicador de comando codificado

## Etapa 7. Geração de alerta

O detector persiste um alerta em `alerts` e uma evidência em `alert_evidence`.

Exemplo de resultado:

- `rule_id = PROC-PS-ENC-001`
- `severity = high`
- título indicando execução de PowerShell com comando codificado

## Etapa 8. Evidência

A evidência armazena uma explicação estruturada do motivo do disparo, incluindo campos como:

- command line
- event action
- process name
- raw event id
- normalized event id

## Por que isso importa

Esse fluxo prova que o projeto não apenas recebe logs. Ele consegue:

- validar entrada
- preservar a informação bruta
- criar uma representação interna consistente
- avaliar regras
- gerar alerta explicável
- manter o comportamento reproduzível com replay