# Architecture

**Status:** proposed architecture, not implemented.

## 1. System boundary

Emotion Engine is a standalone Python component. Hermes remains the conversation orchestrator. The language model is an optional interpretation service, not the database, policy authority, or source of truth.

The engine has two related but distinct research tracks:

- **User-oriented affect modelling:** analyse events and emotional meaning that a user has explicitly expressed or agreed to preserve.
- **Agent-oriented self-observation:** record Lilith's own software actions, computational state changes, decisions, and outcomes.

These tracks must not be merged into one undifferentiated emotion record. A user's reported feeling is not the same thing as a model-generated interpretation; a program variable is not evidence that the program feels something.

## 2. Proposed components

### 2.1 Psychological Knowledge Base

A versioned catalogue of concepts, definitions, relationships, competing theories, source references, and known limitations. Concepts must be traceable to sources. The catalogue must not present a single theory of emotion as universally settled.

### 2.2 Emotional Event Analyzer

Takes a bounded event description and relevant, permission-scoped context. It returns structured hypotheses:

- what happened, as reported or observed;
- what meaning the person may have assigned to it;
- which appraisal dimensions may be relevant;
- which emotion labels may fit, including mixed or uncertain alternatives;
- what remains unknown.

The analyzer must distinguish direct user reports from model inferences. It must not infer diagnoses.

### 2.3 Emotional Memory

Stores only records that meet the consent and retention rules. It stores concise summaries and provenance, not complete conversation transcripts by default. The user must be able to inspect, correct, export, and delete records.

### 2.4 Internal State Model

Represents explicit computational variables used by the software. Candidate variables include current task and active objective, unresolved questions, uncertainty in a particular interpretation, conflict between declared system objectives, and relevant state transitions with their causes.

Optional affect-like coordinates such as valence and arousal may be evaluated in a clearly labelled simulation experiment. They must not be described as subjective feelings.

### 2.5 Self-Observation

Reviews structured records of Lilith's own actions and outcomes. A reflection can identify a discrepancy, uncertainty, repeated failure, or possible improvement. It is a hypothesis until supported by observable evidence or approved by the relevant human.

Self-Observation must not rewrite source code, expand permissions, change safety policy, or silently alter long-term goals.

### 2.6 Emergence Research Harness

Runs controlled and repeatable experiments. It records component versions, configuration, test inputs, state transitions, outputs, and evaluation results. It supports baseline comparisons and ablation studies.

## 3. Processing flow

1. Receive a conversation event or a system action record.
2. Classify the record type and its provenance.
3. Apply privacy and consent rules before any persistence.
4. If analysis is needed, produce bounded appraisal hypotheses.
5. Validate the proposed structure and numeric ranges deterministically.
6. Store only permitted records.
7. Update explicitly defined internal variables through deterministic transition rules.
8. Optionally run one bounded self-observation pass after a completed task.
9. Make a small, permission-scoped summary available to Lilith when relevant.

## 4. Authority and trust boundaries

| Component | May do | Must not do |
|---|---|---|
| LLM | Propose event interpretation, alternatives, explanations | Certify truth, grant consent, set permissions, directly write unrestricted state |
| Validator | Check schema, ranges, provenance, policy | Guess missing facts |
| Memory store | Persist approved records and return scoped matches | Store unapproved emotional data |
| State engine | Apply defined and testable transitions | Create unlimited self-directed goals |
| Self-Observation | Compare action records with outcomes | Treat its own narrative as evidence |
| Hermes | Orchestrate messages and tools | Be replaced by an unbounded inner loop |

## 5. Bounded feedback

Feedback is allowed only through explicit, finite transitions. A proposed first implementation should allow at most one reflection pass per completed task. Reflection output must not recursively trigger another reflection. A budget and maximum depth must be enforced in code, not merely requested in a prompt.

## 6. Failure behaviour

- If consent is missing or unclear, do not persist user emotional data.
- If an LLM response is invalid, discard the interpretation and continue without it.
- If storage is unavailable, do not pretend that a memory was saved.
- If state validation fails, retain the previous valid state.
- If a reflection pass exceeds its budget, stop it and record a technical status without blocking normal conversation.

## 7. Non-goals

The architecture does not assert that Lilith has, can develop, or will develop subjective experience. It does not attempt clinical assessment, emotional dependency, persuasive profiling, uncontrolled self-modification, or unrestricted autonomous operation.
