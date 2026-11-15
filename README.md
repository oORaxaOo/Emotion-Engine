# Emotion Engine

**Emotion Engine** is a research-oriented, local-first project for Lilith. It explores emotional-event modelling, persistent memory, bounded internal state, and self-observation in a transparent and testable software system.

## Research objective

Build a system that can:
- represent affective appraisals without claiming numeric variables are human feelings;
- analyse events through context and appraisal rather than relying only on emotion labels;
- preserve user-confirmed emotional memories with clear provenance and user control;
- observe Lilith's recorded actions, computational state changes, and outcomes;
- study whether interactions between components produce novel, persistent, and reproducible behaviour.

## Important distinction

Affective computation, self-monitoring, memory, and complex adaptive behaviour do not by themselves demonstrate subjective experience, sentience, or life. The project reports what it measures and does not claim more.

## Status

**Phase 1 — Data foundation:** merged in PR #2. Validated records, consent-gated user-event persistence, separate agent-action and state-transition records, and in-memory SQLite tests.

**Phase 2 — Appraisal prototype:** merged in PR #3. Versioned psychological concepts and deterministic assessment of explicitly supplied appraisal dimensions.

**Phase 3 — Interpretation contract:** implemented in the current development branch. A strict, provider-neutral parser validates event summaries, appraisal notes, meaning hypotheses, emotion hypotheses, alternative explanations, unknowns, and clarifying questions. It verifies that cited evidence IDs belong to the supplied event envelope. It does not call a model or write to memory.

**Privacy warning:** the SQLite prototype does not encrypt its database. Use synthetic test data only. Do not store real personal or emotional memories until encryption, key handling, access controls, backups, retention, export, and deletion behaviour have been designed and verified.

## Architecture

1. **Psychological Knowledge Base** — versioned concepts and research references.
2. **Emotional Event Analysis** — context and appraisal hypotheses.
3. **Interpretation Contract** — validates bounded model proposals and evidence references.
4. **Emotional Memory** — user-controlled, provenance-aware event memories.
5. **Internal State Model** — explicit computational state, not a claim of feeling.
6. **Self-Observation** — structured review of Lilith's own actions and outcomes.
7. **Emergence Research** — controlled experiments and ablation tests.

## Design principles

1. **Local-first:** the core must not require a cloud service or external model.
2. **Script-first:** deterministic code owns validation, persistence, budgets, and state transitions. An LLM may propose interpretations; it cannot certify them as facts.
3. **Provenance:** distinguish user statements, system observations, and model hypotheses.
4. **Consent and control:** emotional memories are not silently promoted into long-term records.
5. **No diagnosis or manipulation:** this is not a clinical tool and must not be used to profile, pressure, or emotionally steer people.
6. **Bounded reflection:** self-observation must be finite and auditable.
7. **Scientific humility:** emergent behaviour is an observation to investigate, not proof of consciousness.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Concepts and research foundations](docs/CONCEPTS.md)
- [Phase 2 appraisal prototype](docs/PHASE_2_APPRAISAL.md)
- [Phase 3 interpretation contract](docs/PHASE_3_INTERPRETATION_CONTRACT.md)
- [Data model](docs/DATA_MODEL.md)
- [Safety and privacy](docs/SAFETY_AND_PRIVACY.md)
- [Research and evaluation plan](docs/RESEARCH_PLAN.md)
- [Hermes integration plan](docs/HERMES_INTEGRATION.md)

## Local test command

From the repository root:

```bash
python -m unittest discover -s tests -v
```

The tests use only Python's standard library and in-memory SQLite.

## Development sequence

- **Phase 0 — Specification:** initial architecture and research documentation.
- **Phase 1 — Data foundation:** merged; validated records and consent-gated persistence.
- **Phase 2 — Appraisal prototype:** merged; concept catalogue and structured appraisal checks.
- **Phase 3 — Interpretation contract:** current development branch; strict validation of bounded model proposals.
- **Phase 4 — Bounded model adapter:** optional LLM invocation with strict context, output limits, and no direct database writes.
- **Phase 5 — Memory lifecycle and encryption:** review/export, retention, key handling, and deletion guarantees before real personal data is used.
- **Phase 6 — Internal state and self-observation:** bounded state transitions and auditable reflection.
- **Phase 7 — Research harness:** repeatable experiments, baselines, and ablation tests.
- **Phase 8 — Hermes adapter:** integrate only after standalone behaviour is tested.

Every phase must have passing tests and clear limitations before the next phase begins.
