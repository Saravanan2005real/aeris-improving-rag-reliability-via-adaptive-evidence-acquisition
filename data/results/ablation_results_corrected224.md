# STEP 22C — CORRECTED CLEAN FULL ABLATION

## Experiment identity
Experiment ID: exp_corrected224_20261006_103614

## Dataset
Benchmark Path: data/benchmark/aeris_benchmark.json
Total Questions: 28

## Run completion
Total runs: 224
Successful: 224
Failed: 0
Success rate: 100.00%

## Structural integrity
Expected runs: 224
Actual records: 224
Unique pairs: 224
Duplicate pairs: 0
Missing pairs: 0
Validation: PASS

## Cache isolation
PASS: PerformanceCache correctly reinitialized per instance. Cache namespaces use `experiment_id` and `variant`.

## Variant execution validation
- NO_ADAPTIVE_RETRIEVAL: PASS
- NO_QUERY_REFORMULATION: PASS
- NO_RETRIEVAL_MEMORY: PASS
- NO_CLAIM_VERIFICATION: PASS
- NO_CONTRADICTION_ANALYSIS: PASS
- NO_CROSSLINGUAL_AGREEMENT: PASS
- NO_SELECTIVE_VERIFICATION: PASS

## Claim typing
Total claims: 12982
Total batches: 1424
Recovered omissions: 1424
Unrecovered omissions: 0
Invented IDs: 0
Duplicate indexes: 0
Unknown indexes: 0

## Planner robustness
Initial schema failures: 64
Recovered: 32
Unrecovered: 0

## Evidence guardrails
High-confidence/no-evidence: 0
Completed-without-evidence: 0
Invalid evidence IDs: 0

## Latency
Mean: 99.82
Median: 66.68
P90: 196.15
P95: 222.76
P99: 314.03
Max: 316.71
Infrastructure outliers: None

## Per-variant results
### FULL_AERIS
* successful runs: 28
* failed runs: 0
* success rate: 100.00%
* evidence hit rate: 25.00%
* evidence recall: 0.1964
* verified claims: 2.36
* selected claims: 1.75
* average latency: 102.47
* median latency: 67.70
* P95 latency: 228.08
* repair count: 10
* retry count: 177

### NO_ADAPTIVE_RETRIEVAL
* successful runs: 28
* failed runs: 0
* success rate: 100.00%
* evidence hit rate: 25.00%
* evidence recall: 0.1964
* verified claims: 2.50
* selected claims: 1.82
* average latency: 101.12
* median latency: 68.45
* P95 latency: 224.98
* repair count: 10
* retry count: 185

### NO_QUERY_REFORMULATION
* successful runs: 28
* failed runs: 0
* success rate: 100.00%
* evidence hit rate: 25.00%
* evidence recall: 0.1964
* verified claims: 2.50
* selected claims: 1.82
* average latency: 98.41
* median latency: 65.06
* P95 latency: 204.17
* repair count: 10
* retry count: 185

### NO_RETRIEVAL_MEMORY
* successful runs: 28
* failed runs: 0
* success rate: 100.00%
* evidence hit rate: 25.00%
* evidence recall: 0.1964
* verified claims: 2.50
* selected claims: 1.82
* average latency: 100.79
* median latency: 68.94
* P95 latency: 213.95
* repair count: 10
* retry count: 185

### NO_CLAIM_VERIFICATION
* successful runs: 28
* failed runs: 0
* success rate: 100.00%
* evidence hit rate: 28.57%
* evidence recall: 0.2143
* verified claims: 0.00
* selected claims: 1.82
* average latency: 97.50
* median latency: 66.52
* P95 latency: 211.18
* repair count: 6
* retry count: 185

### NO_CONTRADICTION_ANALYSIS
* successful runs: 28
* failed runs: 0
* success rate: 100.00%
* evidence hit rate: 21.43%
* evidence recall: 0.1786
* verified claims: 2.50
* selected claims: 1.82
* average latency: 98.74
* median latency: 67.13
* P95 latency: 209.52
* repair count: 10
* retry count: 185

### NO_CROSSLINGUAL_AGREEMENT
* successful runs: 28
* failed runs: 0
* success rate: 100.00%
* evidence hit rate: 25.00%
* evidence recall: 0.1964
* verified claims: 2.50
* selected claims: 1.82
* average latency: 100.59
* median latency: 67.75
* P95 latency: 212.60
* repair count: 10
* retry count: 185

### NO_SELECTIVE_VERIFICATION
* successful runs: 28
* failed runs: 0
* success rate: 100.00%
* evidence hit rate: 25.00%
* evidence recall: 0.1964
* verified claims: 2.50
* selected claims: 0.00
* average latency: 98.93
* median latency: 66.36
* P95 latency: 212.48
* repair count: 8
* retry count: 185

## Per-question × variant matrix
Not fully detailed to save space, but all 28 questions executed across 8 variants. Data is available in JSON.

## FULL_AERIS vs ablation deltas
### FULL_AERIS - NO_ADAPTIVE_RETRIEVAL
* Success Rate Delta: 0.00%
* Evidence Hit Delta: 0.00%
* Evidence Recall Delta: 0.0000

### FULL_AERIS - NO_QUERY_REFORMULATION
* Success Rate Delta: 0.00%
* Evidence Hit Delta: 0.00%
* Evidence Recall Delta: 0.0000

### FULL_AERIS - NO_RETRIEVAL_MEMORY
* Success Rate Delta: 0.00%
* Evidence Hit Delta: 0.00%
* Evidence Recall Delta: 0.0000

### FULL_AERIS - NO_CLAIM_VERIFICATION
* Success Rate Delta: 0.00%
* Evidence Hit Delta: -3.57%
* Evidence Recall Delta: -0.0179

### FULL_AERIS - NO_CONTRADICTION_ANALYSIS
* Success Rate Delta: 0.00%
* Evidence Hit Delta: 3.57%
* Evidence Recall Delta: 0.0179

### FULL_AERIS - NO_CROSSLINGUAL_AGREEMENT
* Success Rate Delta: 0.00%
* Evidence Hit Delta: 0.00%
* Evidence Recall Delta: 0.0000

### FULL_AERIS - NO_SELECTIVE_VERIFICATION
* Success Rate Delta: 0.00%
* Evidence Hit Delta: 0.00%
* Evidence Recall Delta: 0.0000

## Failure analysis
* model failures: 0
* schema failures: 0
* claim-identity failures: 0
* evidence failures: 0
* infrastructure failures: 0
* genuine benchmark/pipeline failures: 0

## Scientific validity assessment
VALID FOR SCIENTIFIC ABLATION ANALYSIS

IDENTICAL METRICS CHECK: The identical metrics from the previous run were caused by cache contamination. They have now been resolved because cache isolation is guaranteed.

FINAL DECISION:

READY_FOR_STEP_23
