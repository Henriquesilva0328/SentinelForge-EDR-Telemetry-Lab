# Rules and Benchmark

## Current detection rule set

### PROC-PS-ENC-001
**Name:** Encoded PowerShell Command  
**Severity:** high

#### Logic
Triggers when:

- category is `process`
- `process_name` is `powershell.exe`
- command line contains indicators such as:
  - `-enc`
  - ` -e `
  - `EncodedCommand`

#### Purpose
This rule demonstrates a realistic suspicious process execution scenario with a clear and explainable detection outcome.

## Replay datasets

### encoded-powershell-positive
Expected result:

- should generate `PROC-PS-ENC-001`
- should pass benchmark with no false positives and no false negatives

### benign-admin-activity
Expected result:

- should generate no alerts
- should pass benchmark with no false positives

## Benchmark logic

For each replay run, the benchmark compares:

- expected rule ids
- observed rule ids
- false positive rule ids
- false negative rule ids

## Interpretation

### Passed = true
The replay produced exactly the expected set of rule ids.

### False positive
A rule fired even though the dataset did not expect it.

### False negative
A dataset expected a rule, but the system did not generate it.

## Why benchmarking matters

Benchmarking makes the project stronger for portfolio purposes because it proves:

- rules can be validated repeatedly
- detection behavior can be measured
- benign data can be used to check noise
- the lab is not dependent on manual one-off demonstrations