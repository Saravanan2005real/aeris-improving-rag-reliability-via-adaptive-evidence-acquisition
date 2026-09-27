import time
import json
from app.coverage.evidence_coverage import EvidenceCoverageEstimator, EvidenceItem
from app.planning.requirement_planner import RequirementPlanner
from app.planning.schemas import InformationRequirement

def main():
    p = RequirementPlanner()
    print("Planning requirement...")
    plan = p.plan("What is the capital of Japan?")
    requirement = plan.requirements[0]
    
    # Overriding to exact test expectation
    requirement = InformationRequirement(
        requirement_id="R1",
        description="Identify the capital of Japan",
        requirement_type="factual",
        priority=1,
        expected_evidence_type="entity",
        entities=["datasets", "experiments"],
        retrieval_queries=["What datasets were used?"]
    )
    print(f"Requirement: {requirement.description}")

    evidence_text = "Table 7: Number of instances in the datasets used... Natural Questions TriviaQA WebQuestions CuratedTrec Jeopardy Question Generation MS-MARCO FEVER-3-way FEVER-2-way..."
    
    evidence = EvidenceItem(
        chunk_id='test_document_p019_c041',
        document_id='test_document',
        text=evidence_text,
        language='en',
        pages=[19],
        start_page=19,
        end_page=19
    )

    c = EvidenceCoverageEstimator()
    print("Evaluating pair...")
    t0 = time.perf_counter()
    try:
        result = c._evaluate_pair(requirement, evidence)
        t1 = time.perf_counter()
        print(f"Result: {json.dumps(result, indent=2)}")
        print(f"Time: {t1 - t0:.2f} seconds")
    except Exception as e:
        t1 = time.perf_counter()
        print(f"Exception caught: {type(e).__name__}: {e}")
        print(f"Time before failure: {t1 - t0:.2f} seconds")

if __name__ == "__main__":
    main()
