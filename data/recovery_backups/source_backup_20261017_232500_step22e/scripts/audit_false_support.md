# False Support Targeted Audit

## 1. Extract Every False-Support Case
I extracted all 31 cases where an `UNANSWERABLE` question was marked as `SUPPORTED`. The full JSON output is at `data/results/false_support_targeted_audit.json`.

## 2. Root Cause Classification
I traced the evidence chain for cases such as `q_unans_01` and `q_unans_02`.
- `q_unans_02`: The *Coverage Estimator* erroneously marked unrelated evidence as sufficient because the chunk matched the "hardware" terminology. (Root Cause C)
- `q_unans_01`: The *Coverage Estimator* correctly marked the evidence as insufficient (`requirement_1_success: false`). However, the Answer Generator hallucinates an answer and blindly cites a semantically valid but requirement-unrelated claim (Root Cause H: Answer generator treats RELATED evidence as SUPPORTS, and Root Cause I: Final answer guardrail checks provenance existence but not semantic support).

In short, there was a missing link: No component verified whether the extracted **Claim** actually satisfied the **Information Requirement**.

## 3. The Fix
I introduced a **Requirement-level Support Validation layer**:
- I created `RequirementSupportValidator` (`app/verification/requirement_support.py`) which evaluates whether the generated `answer` and its supporting `claims` genuinely satisfy the user's `requirement` derived by the Planner.
- In `app/controller/controller.py`, I added a guardrail after the Answer Generator completes. If the Answer Generator yields `SUPPORTED`, the Controller asks the `RequirementSupportValidator` to check if at least one requirement is met. If NOT, the Controller downgrades the status to `INSUFFICIENT_EVIDENCE`.

## 4. Testing
I added a deterministic test (`test_requirement_support_guardrail`) to `tests/test_requirement_support.py` mimicking Case A (genuine support), Case B/F (related but no semantic support for requirement), and Case E (partial support), as well as a dedicated regression test for the exact failure pattern. All tests passed.

## 5. Next Steps
I have launched the new targeted regression matrix (88 runs) on a fresh experiment ID (`exp_targeted_re_eval_20261006_234000`) and isolated caches. We are currently waiting for it to finish to verify the **False Support Rate = 0** and make our final decision.
