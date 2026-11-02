# AERIS-RAG Ablation Analysis (Step 22C)

## 1. Overall Execution Statistics

- **Total Runs:** 224
- **Successful Runs:** 161 (71.9%)
- **Failed Runs:** 63 (28.1%)

## 2. Per-Variant Statistics

### FULL_AERIS
- Runs: 20 successful, 8 failed (Total: 28, Rate: 71.4%)
- Evidence Hit Rate: 0.150 (Denominator: 20 successful valid runs)
- Evidence Recall: 0.100 (Denominator: 20 successful valid runs)
- Mean Latency: 90.11s | Median: 57.89s | P95: 282.04s
- Verified Claims Avg: 1.50 | Selected Claims Avg: 1.30

### NO_ADAPTIVE_RETRIEVAL
- Runs: 20 successful, 8 failed (Total: 28, Rate: 71.4%)
- Evidence Hit Rate: 0.150 (Denominator: 20 successful valid runs)
- Evidence Recall: 0.100 (Denominator: 20 successful valid runs)
- Mean Latency: 34.66s | Median: 31.01s | P95: 58.61s
- Verified Claims Avg: 1.50 | Selected Claims Avg: 1.30

### NO_CLAIM_VERIFICATION
- Runs: 21 successful, 7 failed (Total: 28, Rate: 75.0%)
- Evidence Hit Rate: 0.190 (Denominator: 21 successful valid runs)
- Evidence Recall: 0.143 (Denominator: 21 successful valid runs)
- Mean Latency: 34.92s | Median: 29.84s | P95: 60.24s
- Verified Claims Avg: 0.00 | Selected Claims Avg: 1.38

### NO_CONTRADICTION_ANALYSIS
- Runs: 20 successful, 8 failed (Total: 28, Rate: 71.4%)
- Evidence Hit Rate: 0.100 (Denominator: 20 successful valid runs)
- Evidence Recall: 0.075 (Denominator: 20 successful valid runs)
- Mean Latency: 37.04s | Median: 31.60s | P95: 66.05s
- Verified Claims Avg: 1.50 | Selected Claims Avg: 1.30

### NO_CROSSLINGUAL_AGREEMENT
- Runs: 20 successful, 8 failed (Total: 28, Rate: 71.4%)
- Evidence Hit Rate: 0.150 (Denominator: 20 successful valid runs)
- Evidence Recall: 0.100 (Denominator: 20 successful valid runs)
- Mean Latency: 37.13s | Median: 31.42s | P95: 65.62s
- Verified Claims Avg: 1.50 | Selected Claims Avg: 1.30

### NO_QUERY_REFORMULATION
- Runs: 20 successful, 8 failed (Total: 28, Rate: 71.4%)
- Evidence Hit Rate: 0.150 (Denominator: 20 successful valid runs)
- Evidence Recall: 0.100 (Denominator: 20 successful valid runs)
- Mean Latency: 32.00s | Median: 29.31s | P95: 46.13s
- Verified Claims Avg: 1.50 | Selected Claims Avg: 1.30

### NO_RETRIEVAL_MEMORY
- Runs: 20 successful, 8 failed (Total: 28, Rate: 71.4%)
- Evidence Hit Rate: 0.150 (Denominator: 20 successful valid runs)
- Evidence Recall: 0.100 (Denominator: 20 successful valid runs)
- Mean Latency: 36.26s | Median: 30.78s | P95: 66.83s
- Verified Claims Avg: 1.50 | Selected Claims Avg: 1.30

### NO_SELECTIVE_VERIFICATION
- Runs: 20 successful, 8 failed (Total: 28, Rate: 71.4%)
- Evidence Hit Rate: 0.150 (Denominator: 20 successful valid runs)
- Evidence Recall: 0.100 (Denominator: 20 successful valid runs)
- Mean Latency: 36.19s | Median: 31.66s | P95: 64.66s
- Verified Claims Avg: 1.50 | Selected Claims Avg: 0.00

## 3. Failure Distribution

### By Type
- json_parsing: 63
- timeout: 0
- model_api: 0
- controller: 0
- other: 0

### By Stage
- FAILED: 63

### By Category
- DIRECT_FACT: 8
- MULTI_HOP: 16
- METHOD: 8
- COMPARATIVE: 16
- QUANTITATIVE: 7
- CONTRADICTION: 8

## 4. Systematic Analysis
The failures appear broadly distributed across all variants, primarily driven by JSON parsing or validation errors during LLM extraction rather than a specific algorithmic failure.
