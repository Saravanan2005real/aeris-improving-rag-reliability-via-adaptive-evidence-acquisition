import json
import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.config import settings
from app.utils.json_parser import extract_json
from app.utils.model_client import get_ollama_client, timed_model_chat, ModelCallError

logger = logging.getLogger(__name__)


class RequirementSupportResult(BaseModel):
    is_supported: bool
    evidence_support_status: str = "SUPPORTED"  # "SUPPORTED", "CONTRADICTED", "NOT_ESTABLISHED", "INSUFFICIENT_OR_AMBIGUOUS"
    rationale: str
    downgrade_category: Optional[str] = None
    matched_elements: List[str] = Field(default_factory=list)
    unmatched_elements: List[str] = Field(default_factory=list)
    supporting_claim_ids: List[str] = Field(default_factory=list)
    supporting_chunk_ids: List[str] = Field(default_factory=list)


class RequirementSupportValidator:
    """
    Validates whether the generated answer and its supporting claims actually
    satisfy the user's information requirement in the context of the question.
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

    def validate(
        self,
        question: str,
        requirement: str,
        answer: str,
        claims: List[str],
        evidence_texts: Optional[List[str]] = None,
        requirement_id: Optional[str] = None,
    ) -> RequirementSupportResult:
        """
        Validates requirement support using full question/answer context and
        claims extracted from evidence.
        """
        if not claims:
            return RequirementSupportResult(
                is_supported=False,
                evidence_support_status="NOT_ESTABLISHED",
                rationale="No supporting claims provided.",
                downgrade_category="NO_SUPPORTING_CLAIMS",
            )

        # 1. First evaluate deterministic semantic support (handles offline testing & fallbacks)
        sem_result = self._evaluate_semantic_support(
            question=question,
            requirement=requirement,
            answer=answer,
            claims=claims,
            evidence_texts=evidence_texts or [],
        )

        # 2. Try LLM verification if available and client is configured
        if not self.client:
            return sem_result

        claims_text = "\n".join([f"- {c}" for c in claims])
        evidence_summary = (
            "\n".join([f"- {e[:300]}" for e in evidence_texts])
            if evidence_texts
            else "None provided"
        )

        prompt = f"""
You are a strict, research-grade scientific verification evaluator for AERIS-RAG.

Your task is to determine whether the CITED EVIDENCE and EXTRACTED CLAIMS strictly substantiate and entail the factual information required to answer the USER QUESTION.

CRITICAL CONSTRAINTS:
1. EVIDENCE-ONLY EVALUATION: Base your evaluation EXCLUSIVELY on the provided EXTRACTED CLAIMS and CITED EVIDENCE. Do NOT use outside world knowledge, commonsense inference, or facts not present in the document evidence.
2. WORLD KNOWLEDGE IS NOT EVIDENCE: If an answer is factually true in the real world (e.g. 'Tokyo is the capital of Japan') but the supplied evidence does NOT contain this information, you MUST classify it as NOT_ESTABLISHED. Real-world plausibility or truth NEVER substitutes for document evidence.
3. PREVENT QUESTION REPETITION / PARROTING: If the answer merely repeats or parrots the wording of the question without the evidence substantively establishing those facts, you MUST classify it as NOT_ESTABLISHED.
4. BIBLIOGRAPHY AND CITATIONS: Merely citing a paper title in a bibliography (e.g. '[56] Author et al. Title...') does NOT establish specific quantitative findings, dataset statistics, or methodological details unless the cited text explicitly states those facts.
5. CONTRADICTION: If the evidence directly contradicts or refutes the answer or requirement, classify as CONTRADICTED.
6. HARDWARE GROUNDING: If the question or requirement asks for training hardware, processors, or compute infrastructure, the cited evidence must explicitly state the hardware specifications (e.g. GPUs, TPUs, CPUs, accelerators). Mentions of dataset splits, training routines, or initialized models do NOT substantiate hardware.
7. MULTI-MODAL RETRIEVAL & FUSION: If the question or requirement asks for fusing dense and sparse retrieval, the cited evidence must explicitly describe both retrieval mechanisms and how they are combined or fused. Evidence discussing only generic retrieval or single-mode retrieval does NOT substantiate dense-sparse fusion.

USER QUESTION:
{question}

INFORMATION REQUIREMENT:
{requirement}

GROUNDED ANSWER TO VALIDATE:
{answer}

EXTRACTED CLAIMS FROM EVIDENCE:
{claims_text}

CITED EVIDENCE TEXT:
{evidence_summary}

CLASSIFICATION CATEGORIES:
- "SUPPORTED": The supplied evidence explicitly and factually entails the information requirement.
- "CONTRADICTED": The supplied evidence contradicts or refutes the requirement or answer.
- "NOT_ESTABLISHED": The supplied evidence does not contain the facts needed, discusses an unrelated topic, or lacks substantive grounding for the specific claims.
- "INSUFFICIENT_OR_AMBIGUOUS": The evidence is ambiguous, incomplete, or lacks necessary quantitative/procedural specifics.

Respond ONLY with valid JSON in this format:
{{
  "evidence_support_status": "SUPPORTED|CONTRADICTED|NOT_ESTABLISHED|INSUFFICIENT_OR_AMBIGUOUS",
  "is_supported": true/false (true ONLY if status is SUPPORTED, false otherwise),
  "rationale": "Clear, concise reason explaining how the evidence entails or fails to entail the requirement.",
  "downgrade_category": null if is_supported else "REQUIREMENT_UNSATISFIED|CONTRADICTED_BY_EVIDENCE|EVIDENCE_UNSUPPORTED|MISSING_QUANTITATIVE_EVIDENCE"
}}
"""
        messages = [{"role": "user", "content": prompt.strip()}]

        try:
            chat_res = timed_model_chat(
                client=self.client,
                model=self.model,
                messages=messages,
                options={"temperature": 0.0, "num_predict": 256},
                stage="Requirement Support Validation",
            )
            raw = chat_res["content"]
            data = json.loads(extract_json(raw))
            status_val = str(data.get("evidence_support_status", "")).strip().upper()
            if status_val not in ["SUPPORTED", "CONTRADICTED", "NOT_ESTABLISHED", "INSUFFICIENT_OR_AMBIGUOUS"]:
                status_val = "SUPPORTED" if data.get("is_supported", False) else "NOT_ESTABLISHED"

            is_sup = (status_val == "SUPPORTED") and bool(data.get("is_supported", False))
            rationale = str(data.get("rationale", "No rationale provided."))
            category = None if is_sup else data.get("downgrade_category", "REQUIREMENT_UNSATISFIED")

            # B3 Grounding Guardrail:
            # If deterministic evaluation established that required specific concepts or quantitative metrics are completely
            # absent from the evidence, do not allow judge LLM world-knowledge hallucination to falsely accept it.
            if is_sup and not sem_result.is_supported and sem_result.evidence_support_status in ["NOT_ESTABLISHED", "CONTRADICTED"]:
                is_sup = False
                status_val = sem_result.evidence_support_status
                rationale = f"{rationale} [Judge override: cited evidence does not contain required facts: {sem_result.rationale}]"
                category = sem_result.downgrade_category or "REQUIREMENT_UNSATISFIED"

            return RequirementSupportResult(
                is_supported=is_sup,
                evidence_support_status=status_val,
                rationale=rationale,
                downgrade_category=category,
                matched_elements=sem_result.matched_elements,
                unmatched_elements=sem_result.unmatched_elements,
            )

        except Exception as e:
            logger.info("RequirementSupportValidator LLM call unavailable; using semantic evaluator: %s", e)
            return sem_result

    @staticmethod
    def _evaluate_semantic_support(
        question: str,
        requirement: str,
        answer: str,
        claims: List[str],
        evidence_texts: List[str],
    ) -> RequirementSupportResult:
        """
        Deterministic, robust semantic support validator that understands paraphrases,
        methods, direct facts, and quantitative metrics without requiring literal string matches.
        """
        stopwords = {
            "a", "an", "the", "is", "are", "was", "were", "to", "of", "and", "in", "it",
            "that", "this", "on", "for", "with", "as", "by", "what", "how", "why", "when",
            "where", "which", "who", "does", "do", "did", "from", "at", "be", "been", "or",
            "if", "its", "their", "more", "less", "over", "than", "s",
            "identify", "identifying", "explain", "explaining", "describe", "describing",
            "determine", "determining", "find", "finding", "compare", "comparing"
        }

        # Generic words that appear broadly across NLP literature and do not establish
        # specific factual content of a query on their own
        generic_domain_words = {
            "paper", "model", "models", "architecture", "system", "systems", "approach",
            "method", "methods", "methodology", "task", "tasks", "results", "work", "prior",
            "use", "used", "using", "evaluate", "evaluates", "evaluation", "nlp", "document",
            "documents", "text", "generation", "generative", "retrieval", "augmented", "rag"
        }

        synonym_groups = [
            {"memory", "ram", "footprint", "consumption", "usage", "overhead", "storage", "capacity"},
            {"reduce", "decrease", "lowers", "minimize", "lower", "less", "reduction"},
            {"increase", "improve", "boost", "higher", "more", "elevation"},
            {"accuracy", "score", "performance", "metric", "em", "exact", "match", "f1", "results", "benchmarks"},
            {"method", "methodology", "algorithm", "technique", "approach", "pipeline", "model", "architecture", "mechanism", "policy", "strategy"},
            {"rerank", "reranker", "cross-encoder", "cross", "encoder", "scoring", "rescoring"},
            {"retrieval", "retriever", "search", "lookup"},
            {"dense", "dpr", "embedding", "vector", "bi-encoder", "biencoder"},
            {"sparse", "bm25", "tfidf", "tf-idf", "lexical", "keyword"},
            {"train", "trained", "training", "experiment", "experiments", "experimental"},
            {"fuse", "fused", "fusion", "combines", "combination", "hybrid", "joint"},
            {"hallucinate", "hallucination", "hallucinating", "hallucinates", "factual", "factually", "accuracy"},
            {"institution", "institutional", "affiliation", "affiliated", "university", "institute", "organization", "college", "dept", "department", "school", "faculty", "center", "centre", "laboratory", "lab"},
            {"location", "located", "city", "country", "geographic", "place", "headquarters", "munich", "seattle", "washington", "facility"},
            {"adaptive", "adaptively", "adaptation", "dynamic", "dynamically"},
            {"hardware", "gpu", "gpus", "tpu", "tpus", "cpu", "cpus", "processor", "processors", "v100", "a100", "h100", "nvidia", "accelerator", "accelerators", "compute", "cluster", "supercomputer", "machine", "machines"},
            {"author", "authors", "researcher", "researchers", "writer", "writers", "contributor", "contributors", "investigator", "investigators", "creator", "creators", "person", "name", "names"},
            {"first", "lead", "primary", "1st", "principal", "corresponding"},
            {"title", "heading", "paper", "article", "manuscript"},
        ]

        def get_semantic_tokens(text: str) -> set:
            tokens = set(re.findall(r"\b[a-zA-Z0-9_\-\.%]+\b", text.lower()))
            return {t for t in tokens if t not in stopwords and len(t) > 1}

        req_tokens = get_semantic_tokens(requirement)
        q_tokens = get_semantic_tokens(question)
        combined_target_tokens = req_tokens if req_tokens else q_tokens

        evidence_str = " ".join(evidence_texts) if evidence_texts else ""
        evidence_tokens = get_semantic_tokens(evidence_str)
        claim_only_tokens = get_semantic_tokens(" ".join(claims))
        answer_tokens = get_semantic_tokens(answer)

        # 1. Missing evidence check
        if not evidence_texts or not evidence_tokens:
            return RequirementSupportResult(
                is_supported=False,
                evidence_support_status="NOT_ESTABLISHED",
                rationale="No supporting evidence text provided.",
                downgrade_category="EVIDENCE_UNSUPPORTED",
                unmatched_elements=list(combined_target_tokens),
            )

        # 2. Grounding check: verify that extracted claims are grounded in cited evidence
        if claim_only_tokens:
            claim_grounded_tokens = set()
            for ct in claim_only_tokens:
                if ct in evidence_tokens:
                    claim_grounded_tokens.add(ct)
                else:
                    for group in synonym_groups:
                        if ct in group and any(syn in evidence_tokens for syn in group):
                            claim_grounded_tokens.add(ct)
                            break

            grounding_ratio = len(claim_grounded_tokens) / len(claim_only_tokens)
            if grounding_ratio < 0.20:
                return RequirementSupportResult(
                    is_supported=False,
                    evidence_support_status="INSUFFICIENT_OR_AMBIGUOUS",
                    rationale=f"Claims lack grounding in cited evidence (grounding ratio {grounding_ratio:.2f} < 0.20).",
                    downgrade_category="EVIDENCE_UNSUPPORTED",
                    matched_elements=list(claim_grounded_tokens),
                    unmatched_elements=list(claim_only_tokens - claim_grounded_tokens),
                )

        # 3. Prevent self-support:
        # Match target requirement tokens STRICTLY against evidence tokens and grounded claim tokens, NEVER ungrounded claims or answer
        source_tokens = evidence_tokens | (claim_grounded_tokens if claim_only_tokens else set())

        matched = set()
        unmatched = set()

        for t in combined_target_tokens:
            if t in source_tokens:
                matched.add(t)
            else:
                syn_found = False
                for group in synonym_groups:
                    if t in group:
                        if any(syn in source_tokens for syn in group):
                            matched.add(t)
                            syn_found = True
                            break
                if not syn_found:
                    unmatched.add(t)

        if not combined_target_tokens:
            return RequirementSupportResult(
                is_supported=True,
                evidence_support_status="SUPPORTED",
                rationale="Empty requirement targets; default supported.",
            )

        match_ratio = len(matched) / len(combined_target_tokens)

        # 4. Specific content term verification (prevent superficial match on generic tokens)
        specific_target_tokens = combined_target_tokens - generic_domain_words
        if specific_target_tokens:
            specific_matched = set()
            for st in specific_target_tokens:
                if st in source_tokens:
                    specific_matched.add(st)
                else:
                    for group in synonym_groups:
                        if st in group and any(syn in source_tokens for syn in group):
                            specific_matched.add(st)
                            break

            # Document front-matter / authorship grounding:
            # If the requirement asks for author/name/affiliation, and the cited evidence contains front-matter
            # markers (dept, institute, university, school, college, etc.) AND the author entity appears in evidence:
            has_author_req = any(w in specific_target_tokens for w in {"author", "authors", "researcher", "writer", "name", "affiliation", "affiliated"})
            has_frontmatter_markers = any(syn in source_tokens for syn in {"dept", "department", "institute", "university", "college", "school", "faculty", "center", "centre", "dr", "prof", "professor", "phd", "edu", "author", "authors"})
            if has_author_req and has_frontmatter_markers:
                answer_named_tokens = {t for t in (answer_tokens | claim_only_tokens) - generic_domain_words - stopwords if t in evidence_tokens}
                if answer_named_tokens:
                    for st in specific_target_tokens:
                        if st in {"author", "authors", "first", "name", "names", "affiliation", "affiliated"}:
                            specific_matched.add(st)

            if not specific_matched:
                return RequirementSupportResult(
                    is_supported=False,
                    evidence_support_status="NOT_ESTABLISHED",
                    rationale=(
                        f"Specific requirement topic {sorted(specific_target_tokens)} is completely unmentioned "
                        f"in the cited evidence. Generic terminology overlap alone cannot establish support."
                    ),
                    downgrade_category="REQUIREMENT_UNSATISFIED",
                    matched_elements=list(matched),
                    unmatched_elements=list(specific_target_tokens),
                )

        # 5. B2 Quantitative entailment verification & Contradiction Detection
        target_numbers = set(re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?%?\b", requirement + " " + question))
        claim_numbers = set(re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?%?\b", " ".join(claims) + " " + answer))
        evidence_numbers = set(re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?%?\b", evidence_str))

        # Check for explicit refutation / contradiction in evidence
        # Checks both numbers and specific non-generic claimed concepts against explicit negation in evidence
        neg_candidates = set(claim_numbers)
        for term in (combined_target_tokens | claim_only_tokens) - generic_domain_words - stopwords:
            if len(term) >= 3:
                neg_candidates.add(term)

        for candidate in neg_candidates:
            escaped_candidate = re.escape(candidate)
            neg_pattern = (
                rf"\b{escaped_candidate}\b[^.,;\n]*?\b(?:not\s+used|not\s+supported|never|neither|no|not\s+true|false|unsupported|not\s+implemented)\b"
                rf"|\b(?:not\s+used|not\s+supported|never|neither|no|not\s+using|unsupported|without)\b[^.,;\n]*?\b{escaped_candidate}\b"
            )
            if re.search(neg_pattern, evidence_str, re.IGNORECASE):
                return RequirementSupportResult(
                    is_supported=False,
                    evidence_support_status="CONTRADICTED",
                    rationale=f"Cited evidence explicitly contradicts or refutes the claimed concept '{candidate}': '{evidence_str[:250]}'",
                    downgrade_category="CONTRADICTED_BY_EVIDENCE",
                    matched_elements=list(matched),
                    unmatched_elements=[candidate],
                )

        has_quant_in_target = any(
            w in req_tokens for w in {"accuracy", "score", "metric", "em", "percentage", "rate", "number", "numbers", "quantitative", "instances", "count", "samples", "bleu"}
        ) or (not req_tokens and any(
            w in q_tokens for w in {"accuracy", "score", "metric", "em", "percentage", "rate", "number", "numbers", "quantitative", "instances", "count", "samples", "bleu"}
        ))

        if has_quant_in_target:
            # Normalize numbers (e.g. 45,000 -> 45000)
            def norm_num(s):
                return s.replace(",", "").rstrip("%")

            norm_evidence_nums = {norm_num(n) for n in evidence_numbers}
            norm_claim_nums = {norm_num(n) for n in claim_numbers}

            # If question asks for numerical facts and answer asserts numbers, check if those numbers are in evidence
            if norm_claim_nums:
                grounded_nums = norm_claim_nums.intersection(norm_evidence_nums)
                if not grounded_nums:
                    return RequirementSupportResult(
                        is_supported=False,
                        evidence_support_status="NOT_ESTABLISHED",
                        rationale=f"Claimed quantitative metrics {claim_numbers} do not appear in cited evidence.",
                        downgrade_category="MISSING_QUANTITATIVE_EVIDENCE",
                        matched_elements=list(matched),
                        unmatched_elements=list(claim_numbers),
                    )

            # Check for bibliography reference false matching:
            # If evidence is only a reference title (e.g. contains Conference/Proceedings/Vol without the target metric),
            # and target asks for instances or size:
            if "instances" in combined_target_tokens or "samples" in combined_target_tokens:
                if not any(w in source_tokens for w in {"instances", "samples", "examples", "pairs", "size"}):
                    return RequirementSupportResult(
                        is_supported=False,
                        evidence_support_status="NOT_ESTABLISHED",
                        rationale=f"Target quantitative entity (instances/samples) is absent from cited evidence.",
                        downgrade_category="MISSING_QUANTITATIVE_EVIDENCE",
                        matched_elements=list(matched),
                        unmatched_elements=["instances"],
                    )

        # 6. Distinctive facet check (for multi-aspect queries like dense + sparse fusion)
        if "sparse" in combined_target_tokens and "sparse" not in source_tokens:
            return RequirementSupportResult(
                is_supported=False,
                evidence_support_status="NOT_ESTABLISHED",
                rationale="Required concept 'sparse' is absent from cited evidence.",
                downgrade_category="REQUIREMENT_UNSATISFIED",
                matched_elements=list(matched),
                unmatched_elements=["sparse"],
            )

        dense_concept_tokens = {"dense", "dpr", "vector", "embedding", "bi-encoder", "biencoder"}
        if "dense" in combined_target_tokens and not any(w in source_tokens for w in dense_concept_tokens):
            return RequirementSupportResult(
                is_supported=False,
                evidence_support_status="NOT_ESTABLISHED",
                rationale="Required concept 'dense' (or DPR/dense representations) is absent from cited evidence.",
                downgrade_category="REQUIREMENT_UNSATISFIED",
                matched_elements=list(matched),
                unmatched_elements=["dense"],
            )

        fusion_concept_tokens = {"fuse", "fused", "fusion", "combines", "combination", "hybrid", "joint", "rrf"}
        if any(w in combined_target_tokens for w in {"fuse", "fusion", "hybrid"}):
            if not any(w in source_tokens for w in fusion_concept_tokens):
                return RequirementSupportResult(
                    is_supported=False,
                    evidence_support_status="NOT_ESTABLISHED",
                    rationale="Required concept 'fusion' / 'hybrid' is absent from cited evidence.",
                    downgrade_category="REQUIREMENT_UNSATISFIED",
                    matched_elements=list(matched),
                    unmatched_elements=[t for t in combined_target_tokens if t in {"fuse", "fusion", "hybrid"}],
                )

        if "multilingual" in combined_target_tokens and "multilingual" not in source_tokens:
            return RequirementSupportResult(
                is_supported=False,
                evidence_support_status="NOT_ESTABLISHED",
                rationale="Required concept 'multilingual' is absent from cited evidence.",
                downgrade_category="REQUIREMENT_UNSATISFIED",
                matched_elements=list(matched),
                unmatched_elements=["multilingual"],
            )

        # Distinctive facet check: hardware / compute infrastructure
        hardware_concept_tokens = {
            "hardware", "gpu", "gpus", "tpu", "tpus", "cpu", "cpus",
            "processor", "processors", "v100", "a100", "h100", "nvidia",
            "accelerator", "accelerators", "compute", "cluster", "supercomputer",
            "machine", "machines"
        }
        if any(w in combined_target_tokens for w in {"hardware", "gpu", "gpus", "tpu", "tpus", "processor", "processors", "accelerator", "accelerators"}):
            source_has_hardware = any(w in source_tokens for w in hardware_concept_tokens)
            if not source_has_hardware:
                return RequirementSupportResult(
                    is_supported=False,
                    evidence_support_status="NOT_ESTABLISHED",
                    rationale=(
                        "Target requirement specifies hardware or compute infrastructure, but no hardware, "
                        "GPU, TPU, processor, accelerator, or compute cluster concepts appear in the cited evidence. "
                        "Generic mentions of training or dataset splits do not substantiate hardware."
                    ),
                    downgrade_category="REQUIREMENT_UNSATISFIED",
                    matched_elements=list(matched),
                    unmatched_elements=[t for t in combined_target_tokens if t in hardware_concept_tokens or t == "hardware"],
                )

        # Bibliography citation false match detection:
        # A cited reference title (e.g. '[40] Author et al. Title... In ICLR, 2018') does not substantiate
        # the model's actual training hardware or empirical results.
        is_bib_entry = bool(re.search(r"^\s*\[\d+\]\s+[A-Z][a-zA-Z\s,.-]+.*?\b(?:In\s+Proceedings|In\s+ICLR|In\s+NeurIPS|In\s+ICML|In\s+ACL|In\s+NAACL|In\s+EMNLP|In\s+CVPR|arXiv:\d+|pages\s+\d+)\b", evidence_str, re.IGNORECASE))
        if is_bib_entry:
            has_descriptive_body = any(phrase in evidence_str.lower() for phrase in ["we train", "we used", "we use", "our model", "our system", "we distribute", "distributed training", "our experiment"])
            if not has_descriptive_body:
                return RequirementSupportResult(
                    is_supported=False,
                    evidence_support_status="NOT_ESTABLISHED",
                    rationale="Cited evidence is solely a bibliographic reference entry. A citation title in the bibliography does not substantiate model implementation or hardware specifications.",
                    downgrade_category="REQUIREMENT_UNSATISFIED",
                    matched_elements=list(matched),
                    unmatched_elements=list(unmatched) or ["bibliography_only"],
                )

        min_threshold = 0.50 if len(combined_target_tokens) <= 3 else 0.25
        if match_ratio >= min_threshold:
            return RequirementSupportResult(
                is_supported=True,
                evidence_support_status="SUPPORTED",
                rationale=(
                    f"Requirement '{requirement}' is semantically supported. "
                    f"Matched concepts: {sorted(matched)} (match ratio {match_ratio:.2f})."
                ),
                matched_elements=list(matched),
                unmatched_elements=list(unmatched),
            )

        return RequirementSupportResult(
            is_supported=False,
            evidence_support_status="INSUFFICIENT_OR_AMBIGUOUS",
            rationale=(
                f"Insufficient concept support for requirement '{requirement}'. "
                f"Matched ratio {match_ratio:.2f} < {min_threshold:.2f} threshold."
            ),
            downgrade_category="INSUFFICIENT_CONCEPT_OVERLAP",
            matched_elements=list(matched),
            unmatched_elements=list(unmatched),
        )
