"""Small, versioned psychological concept catalogue.

The catalogue describes research concepts; it does not diagnose people or
claim that any one theory completely explains emotion.
"""
from __future__ import annotations

from dataclasses import dataclass


CATALOGUE_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class Concept:
    key: str
    name: str
    definition: str
    scope: str
    limitations: tuple[str, ...]
    research_basis: tuple[str, ...]


CONCEPTS: tuple[Concept, ...] = (
    Concept(
        key="event",
        name="Event representation",
        definition="A bounded account of what happened, separated from interpretations of its meaning.",
        scope="Describes the situation before appraisal.",
        limitations=("A text summary may omit context or contain an inaccurate report.",),
        research_basis=("appraisal_approaches",),
    ),
    Concept(
        key="relevance",
        name="Personal relevance",
        definition="The degree to which an event matters to a person's concerns or goals.",
        scope="Appraisal dimension; requires person-specific context.",
        limitations=("Relevance cannot be inferred reliably from topic alone.",),
        research_basis=("component_process_model",),
    ),
    Concept(
        key="expectedness",
        name="Expectedness",
        definition="How far an event matches what was anticipated.",
        scope="Appraisal dimension concerning novelty and expectation.",
        limitations=("An unexpected event is not necessarily negative or emotional.",),
        research_basis=("component_process_model",),
    ),
    Concept(
        key="goal_congruence",
        name="Goal congruence",
        definition="Whether the event appears to support or obstruct a stated goal.",
        scope="Appraisal dimension; direction is represented separately from importance.",
        limitations=("The system must know the relevant goal and whose goal it is.",),
        research_basis=("component_process_model",),
    ),
    Concept(
        key="coping_potential",
        name="Coping potential",
        definition="A person's perceived ability or resources to respond to the situation.",
        scope="Appraisal dimension concerning perceived control and capacity.",
        limitations=("It is not an objective measure of ability or a judgement of competence.",),
        research_basis=("component_process_model",),
    ),
    Concept(
        key="normative_significance",
        name="Normative significance",
        definition="The perceived relationship between an event and personal standards, values, or social norms.",
        scope="Appraisal dimension concerning standards and values.",
        limitations=("The relevant standard must not be assumed by the system.",),
        research_basis=("component_process_model",),
    ),
    Concept(
        key="valence",
        name="Valence",
        definition="A broad pleasant-to-unpleasant affective dimension.",
        scope="Optional descriptive coordinate in circumplex-inspired models.",
        limitations=("Valence alone does not identify a specific emotion.",),
        research_basis=("circumplex_model",),
    ),
    Concept(
        key="arousal",
        name="Arousal",
        definition="A broad low-to-high activation dimension.",
        scope="Optional descriptive coordinate in circumplex-inspired models.",
        limitations=("Activation is not the same as emotional intensity or distress.",),
        research_basis=("circumplex_model",),
    ),
)

THEORIES = {
    "circumplex_model": {
        "name": "Circumplex model of affect",
        "reference": "Russell (1980), DOI: 10.1037/h0077714",
        "use": "A compact dimensional description using valence and arousal.",
        "caution": "Does not by itself explain event meaning or uniquely identify emotion categories.",
    },
    "component_process_model": {
        "name": "Component Process Model and appraisal approach",
        "reference": "Scherer (2001), Appraisal Considered as a Process of Multilevel Sequential Checking",
        "use": "Structures appraisal across relevance, implications, coping potential, and normative significance.",
        "caution": "A framework, not a deterministic emotion lookup table.",
    },
    "constructed_emotion": {
        "name": "Theory of constructed emotion",
        "reference": "Barrett (2017), DOI: 10.1093/scan/nsw154",
        "use": "A distinct perspective on emotion categories, prediction, interoception, and categorisation.",
        "caution": "Not interchangeable with appraisal or circumplex approaches; debated in the field.",
    },
}


def get_concept(key: str) -> Concept | None:
    """Return a concept by stable key, or None when it is not in the catalogue."""
    return next((item for item in CONCEPTS if item.key == key), None)


def list_concepts() -> tuple[Concept, ...]:
    """Return the immutable concept catalogue."""
    return CONCEPTS
