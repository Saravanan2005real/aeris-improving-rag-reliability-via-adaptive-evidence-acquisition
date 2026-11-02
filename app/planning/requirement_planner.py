import json
import time
from app.performance_cache import aeris_cache
import re
from typing import Optional

import ollama

from app.config import settings
from app.planning.schemas import RequirementPlan
from app.utils.json_parser import extract_json
from app.utils.model_client import get_ollama_client, timed_model_chat, ModelCallError


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
        timeout: Optional[float] = None,
    ):
        self.model = model or settings.ollama_model
        self.host = host or settings.ollama_host
        self.timeout = timeout or settings.ollama_timeout

        self.client = get_ollama_client(host=self.host, timeout=self.timeout)

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

15. Return ONLY valid JSON. Do not include markdown blocks, preamble, or explanation outside the JSON.
    Start your response exactly with {{ and end exactly with }}.

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

        cache_key = {"q": question}
        cached = aeris_cache.get("planner", cache_key)
        if cached:
            return RequirementPlan(**cached)

        from app.utils.diagnostics import log_generation_attempt
        messages = [{"role": "user", "content": prompt}]
        
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            parse_success = False
            schema_success = False
            repair_invoked = False
            retry_invoked = (attempt > 1)
            
            try:
                chat_res = timed_model_chat(
                    client=self.client,
                    model=self.model,
                    messages=messages,
                    options={
                        "temperature": 0,
                        "num_predict": 1024,
                    },
                    stage="Planning",
                )
                raw_content = chat_res["content"]
                elapsed = chat_res["elapsed_seconds"]
            except Exception as e:
                elapsed = 0.0
                ctx_size = len(messages[-1]["content"])
                print(f"Error during requirement planning [Model: {self.model}, Stage: planner, Context: {ctx_size} chars]: {e}")
                raise e

            ctx_size = len(messages[-1]["content"])

            try:
                # To detect if repair was used, we check if original fails standard json
                import json as std_json
                try:
                    std_json.loads(raw_content)
                except:
                    repair_invoked = True
                    
                json_text = extract_json(raw_content)
                parse_success = True
                
                data = std_json.loads(json_text)
                plan = RequirementPlan.model_validate(data)
                schema_success = True
                
                log_generation_attempt("Planning", "UNKNOWN", "UNKNOWN", attempt, self.model, ctx_size, elapsed, parse_success, schema_success, repair_invoked, retry_invoked)
                break  # Success, exit loop
                
            except Exception as e:
                log_generation_attempt("Planning", "UNKNOWN", "UNKNOWN", attempt, self.model, ctx_size, elapsed, parse_success, schema_success, repair_invoked, retry_invoked)
                if attempt == max_attempts:
                    class RequirementPlanningError(Exception):
                        def __init__(self, msg):
                            super().__init__(msg)
                    raise RequirementPlanningError(f"Requirement planning failed after {max_attempts} attempts. Error: {str(e)}")
                    
                messages.append({"role": "assistant", "content": raw_content})
                import pydantic
                missing_fields = []
                if isinstance(e, pydantic.ValidationError):
                    for err in e.errors():
                        if err.get("type") == "missing":
                            loc_str = " -> ".join(map(str, err.get("loc", [])))
                            missing_fields.append(loc_str)
                
                if missing_fields:
                    error_msg = f"Your previous response omitted required fields:\n{missing_fields}\n\nReturn a complete RequirementPlan containing every required field. Do not omit fields."
                else:
                    error_msg = f"Your previous response failed validation with error: {str(e)}. Please correct the JSON structure and schema to strictly match the requested format. Do not omit required fields."
                messages.append({"role": "user", "content": error_msg})

        # Ensure the planner preserves the exact user question.
        plan.question = question

        aeris_cache.set("planner", cache_key, plan.model_dump())

        return plan
