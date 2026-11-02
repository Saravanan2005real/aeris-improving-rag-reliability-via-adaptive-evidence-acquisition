import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.planning.requirement_planner import RequirementPlanner


def print_plan(plan):
    print("\n" + "=" * 80)
    print("AERIS-RAG INFORMATION REQUIREMENT PLAN")
    print("=" * 80)

    print(f"\nQuestion:")
    print(plan.question)

    print(f"\nQuestion Type:")
    print(plan.question_type)

    print(f"\nComplexity:")
    print(plan.complexity)

    print(f"\nNumber of Requirements:")
    print(len(plan.requirements))

    for requirement in plan.requirements:
        print("\n" + "-" * 80)

        print(
            f"{requirement.requirement_id} "
            f"(Priority {requirement.priority})"
        )

        print(f"Type: {requirement.requirement_type}")

        print(f"Description:")
        print(requirement.description)

        print(f"Expected Evidence:")
        print(requirement.expected_evidence_type)

        print(f"Entities:")
        if requirement.entities:
            print(", ".join(requirement.entities))
        else:
            print("None")

        print(f"Retrieval Queries:")
        for query in requirement.retrieval_queries:
            print(f"  - {query}")

    print("\n" + "-" * 80)

    print("Planner Reasoning Summary:")
    print(plan.reasoning_summary)

    print("=" * 80)


def main():
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = input("Enter question: ").strip()

    planner = RequirementPlanner()

    print("\nRunning AERIS-RAG requirement planner...")
    print("Model:", planner.model)
    print("Ollama:", planner.host)

    plan = planner.plan(question)

    print_plan(plan)

    print("\nJSON VALIDATION")
    print("=" * 80)

    print(
        json.dumps(
            plan.model_dump(),
            indent=2,
            ensure_ascii=False,
        )
    )

    print("\nSTATUS: SUCCESS")


if __name__ == "__main__":
    main()
