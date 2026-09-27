from typing import List

from pydantic import BaseModel, Field

from app.claim_graph.graph import ClaimEvidenceGraphBuilder
from app.verification.cross_lingual_agreement import (
    CrossLingualEvidenceClassifier,
    CrossLingualAgreementLabel,
)


class CrossLingualPairResult(BaseModel):
    evidence_a_chunk_id: str
    evidence_b_chunk_id: str

    language_a: str
    language_b: str

    label: CrossLingualAgreementLabel
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    rationale: str


class ClaimCrossLingualResult(BaseModel):
    claim_id: str
    claim: str

    evidence_count: int = Field(ge=1)
    language_count: int = Field(ge=1)

    pair_count: int = Field(ge=0)

    agreement_count: int = Field(ge=0)
    contradiction_count: int = Field(ge=0)
    contextual_difference_count: int = Field(ge=0)
    uncertain_count: int = Field(ge=0)

    overall_label: CrossLingualAgreementLabel
    confidence: float = Field(ge=0.0, le=1.0)

    rationale: str

    pair_results: List[CrossLingualPairResult] = Field(
        default_factory=list
    )


class ClaimCrossLingualAnalyzer:
    """
    Performs cross-lingual consistency analysis for a single claim.

    Only evidence connected to the requested claim is considered.

    Evidence pairs are compared only when their languages differ.
    """

    def __init__(
        self,
        classifier: CrossLingualEvidenceClassifier,
    ):
        self.classifier = classifier

    def analyze_claim(
        self,
        graph: ClaimEvidenceGraphBuilder,
        claim_id: str,
        evidence_languages: dict[str, str],
    ) -> ClaimCrossLingualResult:

        if claim_id not in graph.claims:
            raise ValueError(
                f"Unknown claim_id: {claim_id}"
            )

        claim = graph.claims[claim_id]

        edges = graph.get_claim_evidence(claim_id)

        if not edges:
            raise ValueError(
                f"No evidence connected to claim: {claim_id}"
            )

        evidence_items = []

        for edge in edges:

            chunk_id = edge.chunk_id

            if chunk_id not in graph.evidence:
                raise ValueError(
                    f"Missing evidence node: {chunk_id}"
                )

            if chunk_id not in evidence_languages:
                raise ValueError(
                    f"Missing language for evidence: {chunk_id}"
                )

            evidence_items.append(
                (
                    chunk_id,
                    graph.evidence[chunk_id].text,
                    evidence_languages[chunk_id],
                )
            )

        languages = {
            item[2]
            for item in evidence_items
        }

        pair_results = []

        for i in range(len(evidence_items)):

            for j in range(i + 1, len(evidence_items)):

                chunk_a, text_a, language_a = evidence_items[i]
                chunk_b, text_b, language_b = evidence_items[j]

                # Same-language evidence is not part of
                # cross-lingual analysis.
                if language_a == language_b:
                    continue

                result = self.classifier.classify(
                    evidence_a=text_a,
                    evidence_b=text_b,
                    language_a=language_a,
                    language_b=language_b,
                )

                pair_results.append(
                    CrossLingualPairResult(
                        evidence_a_chunk_id=chunk_a,
                        evidence_b_chunk_id=chunk_b,
                        language_a=language_a,
                        language_b=language_b,
                        label=result.label,
                        confidence=result.confidence,
                        rationale=result.rationale,
                    )
                )

        agreement_count = sum(
            result.label
            == CrossLingualAgreementLabel.AGREEMENT
            for result in pair_results
        )

        contradiction_count = sum(
            result.label
            == CrossLingualAgreementLabel.CONTRADICTION
            for result in pair_results
        )

        contextual_difference_count = sum(
            result.label
            == CrossLingualAgreementLabel.CONTEXTUAL_DIFFERENCE
            for result in pair_results
        )

        uncertain_count = sum(
            result.label
            == CrossLingualAgreementLabel.UNCERTAIN
            for result in pair_results
        )

        pair_count = len(pair_results)

        if pair_count == 0:

            overall_label = (
                CrossLingualAgreementLabel.UNCERTAIN
            )

            confidence = 0.35

            rationale = (
                "No cross-lingual evidence pair was available "
                "for this claim."
            )

        elif contradiction_count > 0:

            overall_label = (
                CrossLingualAgreementLabel.CONTRADICTION
            )

            confidence = 0.90

            rationale = (
                f"{contradiction_count} cross-lingual "
                f"evidence pair(s) were classified as "
                "CONTRADICTION."
            )

        elif agreement_count == pair_count:

            overall_label = (
                CrossLingualAgreementLabel.AGREEMENT
            )

            confidence = 0.90

            rationale = (
                "All cross-lingual evidence pairs for the "
                "claim expressed compatible factual information."
            )

        elif contextual_difference_count > 0:

            overall_label = (
                CrossLingualAgreementLabel.CONTEXTUAL_DIFFERENCE
            )

            confidence = 0.80

            rationale = (
                f"{contextual_difference_count} cross-lingual "
                "evidence pair(s) differed by context."
            )

        else:

            overall_label = (
                CrossLingualAgreementLabel.UNCERTAIN
            )

            confidence = 0.35

            rationale = (
                "The available cross-lingual evidence was "
                "insufficient to establish consistent agreement."
            )

        return ClaimCrossLingualResult(
            claim_id=claim_id,
            claim=claim.text,
            evidence_count=len(evidence_items),
            language_count=len(languages),
            pair_count=pair_count,
            agreement_count=agreement_count,
            contradiction_count=contradiction_count,
            contextual_difference_count=(
                contextual_difference_count
            ),
            uncertain_count=uncertain_count,
            overall_label=overall_label,
            confidence=confidence,
            rationale=rationale,
            pair_results=pair_results,
        )
