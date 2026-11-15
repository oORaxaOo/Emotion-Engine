# Emotion Engine

**Emotion Engine** is a research-oriented, local-first project for Lilith. It explores how emotional-event modelling, persistent memory, bounded internal state, and self-observation can work together in a transparent and testable software system.

## Research objective

Build a system that can:

- represent affective appraisals without claiming numeric variables are human feelings;
- analyse events through context and appraisal rather than relying only on emotion labels;
- preserve user-confirmed emotional memories with clear provenance and user control;
- observe Lilith's recorded actions, internal processing, and outcomes;
- study whether interactions between these components produce novel, persistent, and reproducible behaviour.

## Important distinction

The project can implement affective computation, self-monitoring, memory, and complex adaptive behaviour. None of those capabilities, alone or together, demonstrates subjective experience, sentience, or life. The project must report what it measures and must not claim more.

## Status

**Stage:** foundational architecture and research specification.

There is no runtime implementation or Hermes integration yet. The first development work is to define concepts, data boundaries, safety rules, and evaluation methods before adding executable behaviour.

## Architecture at a glance

1. **Psychological Knowledge Base** — versioned concepts and research references.
2. **Emotional Event Analysis** — context and appraisal hypotheses.
3. **Emotional Memory** — user-controlled, provenance-aware event memories.
4. **Internal State Model** — explicit computational state, not a claim of feeling.
5. **Self-Observation** — structured review of Lilith's own actions and outcomes.
6. **Emergence Research** — controlled experiments and ablation tests.

## Design principles

1. **Local-first:** the core must not require a cloud service or external model.
2. **Script-first:** deterministic code owns validation, persistence, budgets, and state transitions. An LLM may propose interpretations; it cannot certify them as facts.
3. **Provenance:** distinguish user statements, system observations, and model hypotheses.
4. **Consent and control:** emotional memories are not silently promoted into long-term records. Users can inspect, correct, export, and delete them.
5. **No diagnosis or manipulation:** this is not a clinical tool and must not be used to profile, pressure, or emotionally steer people.
6. **Bounded reflection:** self-observation must be finite and auditable. It cannot grant itself new permissions or modify its own code.
7. **Scientific humility:** emergent behaviour is an observation to investigate, not proof of consciousness.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Concepts and research foundations](docs/CONCEPTS.md)
- [Proposed data model](docs/DATA_MODEL.md)
- [Safety and privacy](docs/SAFETY_AND_PRIVACY.md)
- [Research and evaluation plan](docs/RESEARCH_PLAN.md)
- [Hermes integration plan](docs/HERMES_INTEGRATION.md)

## Initial development sequence

- **Phase 0 — Specification:** define concepts, boundaries, data ownership, and evaluation.
- **Phase 1 — Data foundation:** typed records, validation, local persistence, and deletion tests.
- **Phase 2 — Appraisal prototype:** structured event analysis with uncertainty and alternatives.
- **Phase 3 — Memory:** explicit consent, retrieval, correction, and retention controls.
- **Phase 4 — Internal state and self-observation:** bounded state transitions and auditable reflection.
- **Phase 5 — Research harness:** repeatable experiments, baselines, and ablation tests.
- **Phase 6 — Hermes adapter:** integrate only after the standalone engine is tested.

Every phase must have passing tests and clear limitations before the next phase begins.
