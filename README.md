# Emotion Engine

**Emotion Engine** is a research-oriented, local-first project for Lilith. It explores how emotional-event modelling, persistent memory, bounded internal state, and self-observation can work together in a transparent and testable software system.

## Research objective

Build a system that can:

- represent affective state without pretending that numeric variables are human feelings;
- analyse events through context and appraisal rather than relying only on emotion labels;
- preserve user-confirmed emotional memories with clear provenance and user control;
- observe Lilith's own recorded actions and outcomes;
- study whether interactions between these components produce novel, persistent, and reproducible behaviour.

## Important distinction

The project can implement affective computation, self-monitoring, memory, and complex adaptive behaviour. None of those capabilities, alone or together, demonstrates subjective experience, sentience, or life. The project must report what it measures and must not claim more.

## Status

**Stage:** foundational architecture and research specification.

There is no runtime implementation or Hermes integration yet. The first development work is to define the concepts, data boundaries, safety rules, and evaluation method before adding executable behaviour.

## Design principles

1. **Local-first:** no cloud service or external model is required by the core.
2. **Script-first:** deterministic code owns validation, persistence, budgets, and state transitions. An LLM may propose interpretations, never certify them as facts.
3. **Provenance:** distinguish user statements, system observations, and model hypotheses.
4. **Consent and control:** emotional memories are not silently promoted into long-term records. Users can inspect, correct, export, and delete them.
5. **No diagnosis or manipulation:** this is not a clinical tool and must not be used to profile, pressure, or emotionally steer people.
6. **Bounded reflection:** self-observation must be finite, auditable, and unable to grant itself new permissions or modify its own code.
7. **Scientific humility:** emergent behaviour is an observation to investigate, not proof of consciousness.

## Initial architecture areas

- Psychological Knowledge Base
- Emotional Event Analysis
- Emotional Memory
- Internal State Model
- Self-Observation
- Emergence Research and Evaluation

See the project documentation in [docs/](docs/) as it is added.
