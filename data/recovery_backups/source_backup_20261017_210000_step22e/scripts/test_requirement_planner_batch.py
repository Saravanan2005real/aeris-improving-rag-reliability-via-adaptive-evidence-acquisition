import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.planning.requirement_planner import RequirementPlanner


QUESTIONS = [
    "What is Retrieval-Augmented Generation?",
    "What datasets were used in the experiments?",
    "What are the main experimental results?",
    "What is the difference between RAG-Sequence and RAG-Token?",
    "How does the retriever work?",
    "Why does the model use external knowledge?",
    "Which dataset was used to evaluate the model and what performance did the model achieve on it?",
]


def main():
    planner = RequirementPlanner()

    successful = 0
    failed = 0

    print("=" * 80)
    print("AERIS-RAG REQUIREMENT PLANNER BATCH TEST")
    print("=" * 80)

    for index, question in enumerate(QUESTIONS, start=1):
        print("\n" + "-" * 80)
        print(f"TEST {index}")
        print("Question:", question)

        try:
            plan = planner.plan(question)

            print("Type:", plan.question_type)
            print("Complexity:", plan.complexity)
            print("Requirements:", len(plan.requirements))

            valid = True

            if not plan.requirements:
                valid = False

            requirement_ids = set()

            for requirement in plan.requirements:
                if requirement.requirement_id in requirement_ids:
                    valid = False

                requirement_ids.add(requirement.requirement_id)

                if not requirement.description.strip():
                    valid = False

                if not requirement.retrieval_queries:
                    valid = False

            if valid:
                print("Status: SUCCESS")
                successful += 1
            else:
                print("Status: FAILED VALIDATION")
                failed += 1

        except Exception as exc:
            print("Status: FAILED")
            print("Error:", exc)
            failed += 1

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print("Total:", len(QUESTIONS))
    print("Successful:", successful)
    print("Failed:", failed)

    if failed == 0:
        print("STATUS: SUCCESS")
    else:
        print("STATUS: REVIEW REQUIRED")


if __name__ == "__main__":
    main()
