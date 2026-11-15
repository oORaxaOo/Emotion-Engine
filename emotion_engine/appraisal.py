"""Deterministic appraisal assessment from explicitly supplied structured inputs.

This module does not infer a person's inner state from free text. It reports
which dimensions were supplied, which remain unknown, and simple review flags.
"""
from __future__ import annotations

from dataclasses import dataclass

from .errors import RecordValidationError
from .models import Appraisal


@dataclass(frozen=True, slots=True)
class AppraisalInput:
    appraisal: Appraisal
    stated_goal: str | None = None
    context_note: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.appraisal, Appraisal):
            raise RecordValidationError("appraisal must be an Appraisal")
        for name, value in (("stated_goal", self.stated_goal), ("context_note", self.context_note)):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise RecordValidationError(f"{name} must be a non-empty string or None")
            if value is not None and len(value) > 1000:
                raise RecordValidationError(f"{name} exceeds 1000 characters")


@dataclass(frozen=True, slots=True)
class AppraisalAssessment:
    supplied_dimensions: tuple[str, ...]
    unknown_dimensions: tuple[str, ...]
    review_flags: tuple[str, ...]
    stated_goal: str | None
    context_note: str | None
    interpretation_policy: str = "descriptive_only_no_emotion_diagnosis"


_DIMENSIONS = (
    "relevance",
    "expectedness",
    "goal_congruence",
    "coping_potential",
    "normative_significance",
)


def assess_appraisal(value: AppraisalInput) -> AppraisalAssessment:
    """Assess completeness and flag combinations for human/model review.

    Thresholds are engineering heuristics, not psychological cut-offs.
    No emotion label is generated and no causal explanation is asserted.
    """
    if not isinstance(value, AppraisalInput):
        raise RecordValidationError("value must be an AppraisalInput")

    supplied = tuple(
        name for name in _DIMENSIONS
        if getattr(value.appraisal, name) is not None
    )
    unknown = tuple(name for name in _DIMENSIONS if name not in supplied)
    flags: list[str] = []
    appraisal = value.appraisal

    if appraisal.goal_congruence is not None and value.stated_goal is None:
        flags.append("goal_congruence_without_stated_goal")
    if (
        appraisal.relevance is not None
        and appraisal.relevance >= 0.75
        and appraisal.coping_potential is not None
        and appraisal.coping_potential <= 0.25
    ):
        flags.append("high_relevance_low_perceived_coping")
    if (
        appraisal.expectedness is not None
        and appraisal.expectedness <= 0.2
    ):
        flags.append("low_expectedness_review_context")
    if (
        appraisal.normative_significance is not None
        and appraisal.normative_significance >= 0.75
    ):
        flags.append("high_normative_significance_review_stated_standard")

    return AppraisalAssessment(
        supplied_dimensions=supplied,
        unknown_dimensions=unknown,
        review_flags=tuple(flags),
        stated_goal=value.stated_goal,
        context_note=value.context_note,
    )
