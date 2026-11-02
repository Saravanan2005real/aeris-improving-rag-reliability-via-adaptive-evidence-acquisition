# STEP 22C — CLEAN FULL ABLATION

## Experiment identity
Experiment ID: exp_clean224_20261004_173525

## Dataset
Benchmark Path: data/benchmark/aeris_benchmark.json
Total Questions: 28

## Variants
- FULL_AERIS
- NO_ADAPTIVE_RETRIEVAL
- NO_QUERY_REFORMULATION
- NO_RETRIEVAL_MEMORY
- NO_CLAIM_VERIFICATION
- NO_CONTRADICTION_ANALYSIS
- NO_CROSSLINGUAL_AGREEMENT
- NO_SELECTIVE_VERIFICATION

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

## Failure summary
Failures by variant:
- FULL_AERIS: 0
- NO_ADAPTIVE_RETRIEVAL: 0
- NO_QUERY_REFORMULATION: 0
- NO_RETRIEVAL_MEMORY: 0
- NO_CLAIM_VERIFICATION: 0
- NO_CONTRADICTION_ANALYSIS: 0
- NO_CROSSLINGUAL_AGREEMENT: 0
- NO_SELECTIVE_VERIFICATION: 0

Failures by question:

## Claim typing validation
Total claims: 12568
Batches: 1376
Recovered omissions: 1376
Unrecovered omissions: 0
Invented IDs: 0
Duplicate indexes: 0
Unknown indexes: 0

## Planner robustness
Initial schema failures: 8
Recovered: 4
Unrecovered: 0

## Evidence guardrail validation
High-confidence/no-evidence: 0
Completed-without-evidence: 0
Invalid evidence IDs: 0

## Latency statistics
Mean: 51.42
Median: 44.15
P90: 64.41
P95: 76.51
P99: 194.90
Max: 302.54
Infrastructure outliers: None

## Per-variant results
### FULL_AERIS
* successful runs: 28
* failed runs: 0
* success rate: 100.00%
* evidence hit rate: 25.00%
* evidence recall: 0.1964
* verified claims: 2.39
* selected claims: 1.79
* average latency: 98.95
* median latency: 67.49
* P95 latency: 220.07
* repair count: 10
* retry count: 178

### NO_ADAPTIVE_RETRIEVAL
* successful runs: 28
* failed runs: 0
* success rate: 100.00%
* evidence hit rate: 25.00%
* evidence recall: 0.1964
* verified claims: 2.39
* selected claims: 1.79
* average latency: 46.27
* median latency: 44.23
* P95 latency: 64.81
* repair count: 8
* retry count: 174

### NO_QUERY_REFORMULATION
* successful runs: 28
* failed runs: 0
* success rate: 100.00%
* evidence hit rate: 25.00%
* evidence recall: 0.1964
* verified claims: 2.39
* selected claims: 1.79
* average latency: 44.08
* median latency: 43.34
* P95 latency: 57.13
* repair count: 8
* retry count: 174

### NO_RETRIEVAL_MEMORY
* successful runs: 28
* failed runs: 0
* success rate: 100.00%
* evidence hit rate: 25.00%
* evidence recall: 0.1964
* verified claims: 2.39
* selected claims: 1.79
* average latency: 45.44
* median latency: 44.23
* P95 latency: 63.47
* repair count: 8
* retry count: 174

### NO_CLAIM_VERIFICATION
* successful runs: 28
* failed runs: 0
* success rate: 100.00%
* evidence hit rate: 25.00%
* evidence recall: 0.1964
* verified claims: 0.00
* selected claims: 1.79
* average latency: 42.98
* median latency: 40.56
* P95 latency: 63.47
* repair count: 5
* retry count: 174

### NO_CONTRADICTION_ANALYSIS
* successful runs: 28
* failed runs: 0
* success rate: 100.00%
* evidence hit rate: 21.43%
* evidence recall: 0.1786
* verified claims: 2.39
* selected claims: 1.79
* average latency: 44.93
* median latency: 43.36
* P95 latency: 63.60
* repair count: 8
* retry count: 174

### NO_CROSSLINGUAL_AGREEMENT
* successful runs: 28
* failed runs: 0
* success rate: 100.00%
* evidence hit rate: 25.00%
* evidence recall: 0.1964
* verified claims: 2.39
* selected claims: 1.79
* average latency: 44.96
* median latency: 43.24
* P95 latency: 63.94
* repair count: 8
* retry count: 174

### NO_SELECTIVE_VERIFICATION
* successful runs: 28
* failed runs: 0
* success rate: 100.00%
* evidence hit rate: 25.00%
* evidence recall: 0.1964
* verified claims: 2.39
* selected claims: 0.00
* average latency: 43.74
* median latency: 43.39
* P95 latency: 62.30
* repair count: 5
* retry count: 174

## Per-question results
Not fully detailed to save space, but all 28 questions executed across 8 variants.

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
* Evidence Hit Delta: 0.00%
* Evidence Recall Delta: 0.0000

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

FINAL DECISION:

READY_FOR_STEP_23
