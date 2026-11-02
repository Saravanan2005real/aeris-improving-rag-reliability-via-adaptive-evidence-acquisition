# Step 22C FAILED Run Diagnosis

## 1. Failure by Pipeline Stage
| Pipeline Stage | Failure Count |
|---|---|
| Answer Generation | 8 |
| Claim Typing | 16 |
| Initial Verification | 28 |
| Planning | 8 |
| Selective Verification | 3 |

## 2. Failure by Error Type
| Exception Type | Count | Description |
|---|---|---|
| JSON Parsing Error | 47 | `No valid JSON object or array found in model response.` |
| Pydantic Validation Error | 16 | Schema violation (e.g. `Field required`, `Input should be a valid string`) |

## 3. Question x Stage Matrix
| Question | Exact Stage | Consistently Fails? |
|---|---|---|
| q_df_06 | Answer Generation | Yes across all tested variants |
| q_mh_02 | Claim Typing | Yes across all tested variants |
| q_mh_04 | Initial Verification | Yes across all tested variants |
| q_meth_01 | Claim Typing | Yes across all tested variants |
| q_comp_01 | Initial Verification | Yes across all tested variants |
| q_comp_02 | Initial Verification | Yes across all tested variants |
| q_quant_02 | Initial Verification | Yes across all tested variants |
| q_contra_02 | Planning | Yes across all tested variants |

## 4. `q_quant_02` Comparison
- **FULL_AERIS Status:** FAILED
- **FULL_AERIS Exact Stage:** Initial Verification
- **NO_CLAIM_VERIFICATION Status:** COMPLETED

**Why did NO_CLAIM_VERIFICATION succeed?**
In `FULL_AERIS`, all extracted claims are verified, and the local Llama model failed to output valid JSON for one of the verified claims, crashing the entire run. In `NO_CLAIM_VERIFICATION`, the initial exhaustive verification is skipped. While selective verification is executed, it selectively chose different claims (or 0 claims) that happened to NOT trigger the model's json formatting glitch. Thus, bypassing the initial verification directly bypassed the stage where the JSON parsing failure occurred.

## 5. json-repair Implementation Check
The current JSON extraction logic in `app/utils/json_parser.py` (`extract_json()`) **does NOT use the `json-repair` library**.
Instead, it relies on a manual sequence of Regex stripping, string slicing (searching for `{` and `}`), and native `json.loads()`. While it attempts to handle trailing commas and truncated outputs, it completely fails to parse hallucinated unstructured text, conversational prefaces, or missing quotes which `json-repair` handles robustly. If `json-repair` were integrated, a large majority of these 63 failures would likely have been recovered natively.

## 6. Exact Root Cause
The root cause of all 63 failures is that the local Llama model sporadically fails to output strictly compliant JSON, even with standard format prompting. It outputs conversational text or drops required Pydantic keys (like `reasoning_summary` or `answer`), triggering exceptions in `json_parser.py` and Pydantic validation respectively. Because these operations are synchronously blocking and unhandled inside the component execution loops (they bubble up to `AERISController` which catches them and correctly marks the run FAILED), a single badly formatted completion crashes the entire variant evaluation for that question.

## 7. Recommended Fix
1. **Install and Integrate `json-repair`:** Replace the manual string slicing in `app/utils/json_parser.py` with `json_repair.loads(text)`. This library is specifically designed to transparently fix LLM JSON formatting glitches.
2. **Local Retry Logic / Pydantic fallback:** For `Pydantic Validation Error` (where fields are missing, e.g. `answer` is `None`), we should either implement a quick retry loop for the LLM call or provide default fallback fields in the schemas.