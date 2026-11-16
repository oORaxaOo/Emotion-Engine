# Emotion Engine

**Emotion Engine** is a research-oriented, local-first project for Lilith. It
explores emotional-event modelling, persistent memory, bounded internal
state, and self-observation in a transparent and testable software system.

## Research objective

Build a system that can:
- represent affective appraisals without claiming numeric variables are human feelings;
- analyse events through context and appraisal rather than relying only on emotion labels;
- preserve user-confirmed emotional memories with clear provenance and user control;
- observe Lilith's recorded actions, computational state changes, and outcomes;
- study whether interactions between components produce novel, persistent, and reproducible behaviour.

## Important distinction

Affective computation, self-monitoring, memory, and complex adaptive behaviour
do not by themselves demonstrate subjective experience, sentience, or life.
The project reports what it measures and does not claim more.

## Optional KIE integration

The Hermes adapter can optionally publish a bounded
`emotion.reflection_summary` event to the KIE event ledger after an explicit
reflection call. Only status labels and aggregate counts are shared. Reflection
narratives, assistant response text, evidence content, causal hypotheses,
next-question text, and persistent emotional-memory records remain inside
the Emotion Engine.

The integration is opt-in and fail-open. It does not expose the persistent
emotional-memory APIs or create emotional memories.

## Status

Phases 1–6 and the initial Hermes plugin adapter are implemented in the
standalone repository. The plugin has not been installed or enabled in a live
Hermes profile.

## Architecture

1. **Psychological Knowledge Base** — versioned concepts and research references.
2. **Emotional Event Analysis** — context and appraisal hypotheses.
3. **Interpretation Contract** — validates bounded model proposals and evidence references.
4. **Bounded Model Adapter** — makes one controlled call through an injected text transport.
5. **Emotional Memory** — user-controlled, provenance-aware event memories.
6. **Internal State Model** — explicit computational state, not a claim of feeling.
7. **Self-Observation** — structured review of Lilith's own actions and outcomes.
8. **Emergence Research** — controlled experiments and ablation tests.

## Design principles

1. **Local-first:** the core must not require a cloud service or external model.
2. **Script-first:** deterministic code owns validation, persistence, budgets, and state transitions. An LLM may propose interpretations; it cannot certify them as facts.
3. **Provenance:** distinguish user statements, system observations, and model hypotheses.
4. **Consent and control:** emotional memories are not silently promoted into long-term records.
5. **No diagnosis or manipulation:** this is not a clinical tool and must not be used to profile, pressure, or emotionally steer people.
6. **Bounded reflection:** self-observation must be finite and auditable.
7. **Scientific humility:** emergent behaviour is an observation to investigate, not proof of consciousness.

See [Hermes integration](docs/HERMES_INTEGRATION.md) and [Safety and privacy](docs/SAFETY_AND_PRIVACY.md).

## Local test command

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```
