import json
import re
from typing import Optional

import ollama

from app.config import settings
from app.planning.schemas import RequirementPlan


class RequirementPlanner:
    """
    Converts a user question into explicit information requirements.

    The planner is intentionally separated from retrieval so that
    requirement decomposition can later be evaluated independently.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        host: Optional[str] = None,
    ):
        self.model = model or settings.ollama_model
        self.host = host or settings.ollama_host

        self.client = ollama.Client(host=self.host)

    def _build_prompt(self, question: str) -> str:
        return f"""
You are the Information Requirement Planner of AERIS-RAG.

AERIS-RAG answers questions over user-provided documents.

Your task is NOT to answer the user's question.

Your task is to decompose the question into the distinct pieces of
information that must be retrieved from the document before a complete,
evidence-grounded answer can be produced.

The central principle is:

ONE QUESTION MAY REQUIRE MULTIPLE DISTINCT PIECES OF EVIDENCE.

Do not simply rewrite the user's question as one requirement.

You must identify the atomic information requirements needed to answer it.

PLANNING RULES:

1. Identify the actual information requested by the user.

2. Break complex questions into separate requirements.

3. Do NOT create redundant requirements.

4. Each requirement should represent a distinct piece of evidence.

5. If the question asks for a comparison:
   - create requirements for the important characteristics of each item
   - create a requirement for the actual comparison

6. If the question asks for experimental results:
   consider requirements such as:
   - evaluated datasets/tasks
   - evaluation metrics
   - quantitative results
   - baseline comparisons
   - important findings
   Only include requirements that are relevant to the question.

7. If the question asks for multiple facts:
   create separate requirements for each fact.

8. If answering the question requires connecting information from
   different parts of the document, classify the relevant requirement
   as "multi_hop".

9. A simple definition question may legitimately contain only one
   requirement.

10. Do not artificially create requirements just to increase the count.

11. Requirements must be document-independent.
    Do not invent facts that are not present in the question.

12. Entities must be extracted from the question or be generic concepts
    directly implied by it. NEVER invent placeholder entities such as:
    "dataset1", "dataset2", "model1", "method1".
    If the exact entity name is unknown from the question, use a generic
    concept such as "dataset", "model", "performance", or leave the list empty.

13. Retrieval queries must be useful for finding evidence in a document.

14. Generate 1-3 retrieval queries per requirement.

15. Return ONLY valid JSON.

QUESTION TYPES:

- definition
- factual
- list
- comparison
- quantitative
- causal
- procedural
- multi_hop
- summary
- other

COMPLEXITY:

- simple = one main piece of information
- moderate = multiple related pieces of information
- complex = multiple pieces of evidence, comparison, multi-hop reasoning,
  or distributed information

REQUIREMENT TYPES:

- definition = meaning or definition
- fact = specific factual information
- factual = factual information request
- list = multiple items
- comparison = comparing entities
- quantitative = numerical values, metrics, measurements
- causal = cause/effect relationship
- procedural = how something works or is performed
- multi_hop = requires connecting multiple pieces of evidence
- summary = synthesis of several findings
- other = anything else

PRIORITY:

1 = essential
2 = very important
3 = useful
4 = secondary
5 = optional

EXPECTED EVIDENCE TYPES MAY INCLUDE:

- definition
- explanation
- dataset
- table
- numerical result
- metric
- comparison
- methodology
- procedure
- experiment
- conclusion
- example
- statement

IMPORTANT EXAMPLES:

Example 1:

Question:
"What is Retrieval-Augmented Generation?"

Good requirements:

R1:
Understand the definition of Retrieval-Augmented Generation.

Only one requirement is appropriate because this is a simple definition question.

Example 2:

Question:
"What is the difference between RAG-Sequence and RAG-Token?"

Good requirements should separate:

R1:
How RAG-Sequence operates.

R2:
How RAG-Token operates.

R3:
The important differences between RAG-Sequence and RAG-Token.

Example 3:

Question:
"What are the main experimental results?"

Good requirements should consider:

R1:
What datasets/tasks were evaluated?

R2:
What metrics were used?

R3:
What quantitative results were obtained?

R4:
How did the model compare with relevant baselines?

R5:
What major experimental findings were reported?

Only retain requirements that are actually relevant and supported by the
wording of the question.

Example 4:

Question:
"Which dataset was used to evaluate the model and what performance did
the model achieve on it?"

Good requirements:

R1:
Identify the dataset used for evaluation.

R2:
Identify the performance achieved on that dataset.

Example 5:

Question:
"How does the retriever work?"

Good requirements may include:

R1:
What retrieval mechanism is used?

R2:
How does the retriever identify or rank relevant evidence?

Only create both if the question requires both pieces.

JSON STRUCTURE:

{{
  "question": "original question",
  "question_type": "definition|factual|list|comparison|quantitative|causal|procedural|multi_hop|summary|other",
  "complexity": "simple|moderate|complex",
  "requirements": [
    {{
      "requirement_id": "R1",
      "description": "specific information that must be retrieved",
      "requirement_type": "definition|fact|factual|list|comparison|quantitative|causal|procedural|multi_hop|summary|other",
      "priority": 1,
      "expected_evidence_type": "expected evidence type",
      "entities": ["entity1", "entity2"],
      "retrieval_queries": [
        "retrieval query 1",
        "retrieval query 2"
      ]
    }}
  ],
  "reasoning_summary": "short explanation of the decomposition"
}}

User question:

{question}
""".strip()

    @staticmethod
    def _extract_json(text: str) -> str:
        """
        Extract a JSON object even if the model accidentally adds
        surrounding text.
        """

        text = text.strip()

        # Remove markdown fences if present.
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        # Locate the outermost JSON object.
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise ValueError("No valid JSON object found in model response.")

        return text[start : end + 1]

    def plan(self, question: str) -> RequirementPlan:
        """
        Generate a structured information requirement plan.
        """

        if not isinstance(question, str):
            raise TypeError("question must be a string")

        question = question.strip()

        if not question:
            raise ValueError("question cannot be empty")

        prompt = self._build_prompt(question)

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            format="json",
            options={
                "temperature": 0,
            },
        )

        raw_content = response["message"]["content"]

        json_text = self._extract_json(raw_content)

        data = json.loads(json_text)

        plan = RequirementPlan.model_validate(data)

        # Ensure the planner preserves the exact user question.
        plan.question = question

        return plan
