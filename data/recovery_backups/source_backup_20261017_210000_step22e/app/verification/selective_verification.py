from enum import Enum
from typing import List

from pydantic import BaseModel, Field

from app.claim_graph.schemas import (
    ClaimVerificationStatus,
    EvidenceRelationType,
    EdgeType,
)
from app.claim_graph.graph import ClaimEvidenceGraphBuilder


class VerificationPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    SKIP = "SKIP"


class VerificationReason(str, Enum):
    CONTRADICTED = "CONTRADICTED"
    CONFLICTED = "CONFLICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNVERIFIED = "UNVERIFIED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    CROSS_LINGUAL_CONFLICT = "CROSS_LINGUAL_CONFLICT"
    EVIDENCE_CONFLICT = "EVIDENCE_CONFLICT"
    CONTEXTUAL_DIFFERENCE = "CONTEXTUAL_DIFFERENCE"
    STRONG_SUPPORT = "STRONG_SUPPORT"
    MULTILINGUAL_AGREEMENT = "MULTILINGUAL_AGREEMENT"


class VerificationCandidate(BaseModel):
    claim_id: str
    claim: str
    priority: VerificationPriority
    reasons: List[VerificationReason] = Field(default_factory=list)

    raw_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    calibrated_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    claim_status: ClaimVerificationStatus

    evidence_count: int = Field(ge=0)

    requires_verification: bool


class SelectiveVerificationPolicy:
    """
    Determines which claims should receive deeper verification.

    This is a transparent rule-based decision layer.
    It does not perform verification itself.
    """

    def __init__(
        self,
        low_confidence_threshold: float = 0.50,
        high_confidence_threshold: float = 0.85,
    ):
        self.low_confidence_threshold = low_confidence_threshold
        self.high_confidence_threshold = high_confidence_threshold

    def evaluate_claim(
        self,
        graph: ClaimEvidenceGraphBuilder,
        claim_id: str,
        raw_confidence: float | None = None,
        calibrated_confidence: float | None = None,
    ) -> VerificationCandidate:

        if claim_id not in graph.claims:
            raise ValueError(f"Unknown claim_id: {claim_id}")

        claim = graph.claims[claim_id]

        edges = graph.get_claim_evidence(claim_id)

        evidence_count = len(edges)

        if evidence_count == 0:
            status = ClaimVerificationStatus.UNVERIFIED

            return VerificationCandidate(
                claim_id=claim_id,
                claim=claim.text,
                priority=VerificationPriority.SKIP,
                reasons=[VerificationReason.INSUFFICIENT_EVIDENCE],
                raw_confidence=raw_confidence,
                calibrated_confidence=calibrated_confidence,
                claim_status=status,
                evidence_count=0,
                requires_verification=False,
            )

        labels = {edge.edge_type for edge in edges}

        # Determine current claim status.
        if EdgeType.CONTRADICTS in labels and EdgeType.SUPPORTS in labels:
            status = ClaimVerificationStatus.CONFLICTED

        elif EdgeType.CONTRADICTS in labels:
            status = ClaimVerificationStatus.CONTRADICTED

        elif EdgeType.SUPPORTS in labels:
            status = ClaimVerificationStatus.SUPPORTED

        else:
            status = ClaimVerificationStatus.INSUFFICIENT

        reasons = []

        # ---------------------------------------------------------
        # CRITICAL CONDITIONS
        # ---------------------------------------------------------

        if status == ClaimVerificationStatus.CONFLICTED:
            reasons.append(VerificationReason.CONFLICTED)

            return VerificationCandidate(
                claim_id=claim_id,
                claim=claim.text,
                priority=VerificationPriority.CRITICAL,
                reasons=reasons,
                raw_confidence=raw_confidence,
                calibrated_confidence=calibrated_confidence,
                claim_status=status,
                evidence_count=evidence_count,
                requires_verification=True,
            )

        if status == ClaimVerificationStatus.CONTRADICTED:
            reasons.append(VerificationReason.CONTRADICTED)

            return VerificationCandidate(
                claim_id=claim_id,
                claim=claim.text,
                priority=VerificationPriority.CRITICAL,
                reasons=reasons,
                raw_confidence=raw_confidence,
                calibrated_confidence=calibrated_confidence,
                claim_status=status,
                evidence_count=evidence_count,
                requires_verification=True,
            )

        if status in {
            ClaimVerificationStatus.UNVERIFIED,
            ClaimVerificationStatus.INSUFFICIENT,
        }:
            if status == ClaimVerificationStatus.UNVERIFIED:
                reasons.append(VerificationReason.UNVERIFIED)
            else:
                reasons.append(VerificationReason.INSUFFICIENT_EVIDENCE)

            return VerificationCandidate(
                claim_id=claim_id,
                claim=claim.text,
                priority=VerificationPriority.HIGH,
                reasons=reasons,
                raw_confidence=raw_confidence,
                calibrated_confidence=calibrated_confidence,
                claim_status=status,
                evidence_count=evidence_count,
                requires_verification=True,
            )

        # ---------------------------------------------------------
        # HIGH PRIORITY: LOW CONFIDENCE
        # ---------------------------------------------------------

        effective_confidence = (
            calibrated_confidence
            if calibrated_confidence is not None
            else raw_confidence
        )

        if (
            effective_confidence is not None
            and effective_confidence < self.low_confidence_threshold
        ):
            reasons.append(VerificationReason.LOW_CONFIDENCE)

            return VerificationCandidate(
                claim_id=claim_id,
                claim=claim.text,
                priority=VerificationPriority.HIGH,
                reasons=reasons,
                raw_confidence=raw_confidence,
                calibrated_confidence=calibrated_confidence,
                claim_status=status,
                evidence_count=evidence_count,
                requires_verification=True,
            )

        # ---------------------------------------------------------
        # MEDIUM PRIORITY: EVIDENCE CONFLICT
        # ---------------------------------------------------------

        evidence_relations = graph.get_evidence_relations(claim_id)

        relation_types = {
            relation.relation_type
            for relation in evidence_relations
        }

        if EvidenceRelationType.CONTRADICTION in relation_types:
            reasons.append(VerificationReason.EVIDENCE_CONFLICT)

            return VerificationCandidate(
                claim_id=claim_id,
                claim=claim.text,
                priority=VerificationPriority.MEDIUM,
                reasons=reasons,
                raw_confidence=raw_confidence,
                calibrated_confidence=calibrated_confidence,
                claim_status=status,
                evidence_count=evidence_count,
                requires_verification=True,
            )

        if EvidenceRelationType.CONTEXTUAL_DIFFERENCE in relation_types:
            reasons.append(VerificationReason.CONTEXTUAL_DIFFERENCE)

            return VerificationCandidate(
                claim_id=claim_id,
                claim=claim.text,
                priority=VerificationPriority.MEDIUM,
                reasons=reasons,
                raw_confidence=raw_confidence,
                calibrated_confidence=calibrated_confidence,
                claim_status=status,
                evidence_count=evidence_count,
                requires_verification=True,
            )

        # ---------------------------------------------------------
        # LOW / SKIP
        # ---------------------------------------------------------

        if (
            status == ClaimVerificationStatus.SUPPORTED
            and effective_confidence is not None
            and effective_confidence >= self.high_confidence_threshold
        ):
            reasons.append(VerificationReason.STRONG_SUPPORT)

            return VerificationCandidate(
                claim_id=claim_id,
                claim=claim.text,
                priority=VerificationPriority.SKIP,
                reasons=reasons,
                raw_confidence=raw_confidence,
                calibrated_confidence=calibrated_confidence,
                claim_status=status,
                evidence_count=evidence_count,
                requires_verification=False,
            )

        reasons.append(VerificationReason.STRONG_SUPPORT)

        return VerificationCandidate(
            claim_id=claim_id,
            claim=claim.text,
            priority=VerificationPriority.LOW,
            reasons=reasons,
            raw_confidence=raw_confidence,
            calibrated_confidence=calibrated_confidence,
            claim_status=status,
            evidence_count=evidence_count,
            requires_verification=False,
        )


class SelectiveVerificationSelector:
    """
    Evaluates multiple claims and selects the claims that
    require deeper verification under a verification budget.
    """

    PRIORITY_ORDER = {
        VerificationPriority.CRITICAL: 0,
        VerificationPriority.HIGH: 1,
        VerificationPriority.MEDIUM: 2,
        VerificationPriority.LOW: 3,
        VerificationPriority.SKIP: 4,
    }

    def __init__(
        self,
        policy: SelectiveVerificationPolicy | None = None,
    ):
        self.policy = policy or SelectiveVerificationPolicy()

    def evaluate(
        self,
        graph: ClaimEvidenceGraphBuilder,
        claims: list[dict],
    ) -> list[VerificationCandidate]:

        candidates = []

        seen_claims = set()

        for item in claims:

            claim_id = item["claim_id"]

            if claim_id in seen_claims:
                continue

            seen_claims.add(claim_id)

            candidate = self.policy.evaluate_claim(
                graph=graph,
                claim_id=claim_id,
                raw_confidence=item.get("raw_confidence"),
                calibrated_confidence=item.get("calibrated_confidence"),
            )

            candidates.append(candidate)

        candidates.sort(
            key=lambda candidate: self.PRIORITY_ORDER[
                candidate.priority
            ]
        )

        return candidates

    def select(
        self,
        candidates: list[VerificationCandidate],
        budget: int,
    ) -> list[VerificationCandidate]:

        if budget < 0:
            raise ValueError("budget must be non-negative")

        selected = [
            candidate
            for candidate in candidates
            if candidate.requires_verification
        ]

        return selected[:budget]
