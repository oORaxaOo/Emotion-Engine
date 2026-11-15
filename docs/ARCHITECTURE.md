# Architecture

**Status:** Phase 1 data foundation merged; Phase 2 adds a deterministic concept catalogue and structured appraisal completeness assessment. Free-text interpretation, internal-state policies, self-observation, and Hermes integration remain future work.

## 1. System boundary

Emotion Engine is a standalone Python component. Hermes remains the conversation orchestrator. The language model is an optional interpretation service, not the database, policy authority, or source of truth.

The engine has two related but distinct research tracks:

- **User-oriented affect modelling:** analyse events and emotional meaning that a user has explicitly expressed or agreed to preserve.
- **Agent-oriented self-observation:** record Lilith's own software actions, computational state changes, decisions, and outcomes.

These tracks must not be merged into one undifferentiated emotion record. A user's reported feeling is not the same thing as a model-generated interpretation; a program variable is not evidence that the program feels something.

## 2. Components

### 2.1 Psychological Knowledge Base

A versioned catalogue of concepts, definitions, scope, limitations, and research references. The initial catalogue is implemented in `emotion_engine.knowledge`. It records multiple theoretical perspectives separately and does not present one theory as universally settled.

### 2.2 Emotional Event Analyzer

The Phase 2 prototype accepts structured appraisal values and reports which dimensions are supplied, which remain unknown, and which combinations merit review. It does not interpret free text, assign emotion labels, diagnose, or persist records. See [Phase 2 appraisal prototype](PHASE_2_APPRAISAL.md).

### 2.3 Emotional Memory

Stores only records that meet consent and retention rules. It stores concise summaries and provenance, not complete conversation transcripts by default. The current prototype provides local SQLite persistence for user event records, but does not yet implement encryption, retention expiry, a user-facing review/export interface, or derived-memory invalidation.

### 2.4 Internal State Model

Represents explicit computational variables used by the software. The current prototype can persist typed state-transition records linked to technical agent actions. It does not yet define state variables, transition policies, update rules, or autonomous state changes.

Optional affect-like coordinates such as valence and arousal may be evaluated in a clearly labelled simulation experiment. They must not be described as subjective feelings.

### 2.5 Self-Observation

Will review structured records of Lilith's own actions and outcomes. A reflection can identify a discrepancy, uncertainty, repeated failure, or possible improvement. It is a hypothesis until supported by observable evidence or approved by the relevant human. This component is not implemented.

Self-Observation must not rewrite source code, expand permissions, change safety policy, or silently alter long-term goals.

### 2.6 Emergence Research Harness

Will run controlled and repeatable experiments. It records component versions, configuration, test inputs, state transitions, outputs, and evaluation results. It supports baseline comparisons and ablation studies. This component is not implemented.

## 3. Implemented foundations

The initial Python package is `emotion_engine` and uses only the standard library:

- immutable typed records for user events, emotion labels, appraisals, affect coordinates, agent actions, and state transitions;
- range and timezone validation;
- explicit provenance and epistemic status;
- SQLite persistence with separate tables for user events, agent actions, and state transitions;
- a hard persistence check requiring `ConsentStatus.GRANTED` for user event records;
- inspection, correction, listing, and deletion methods for user event records;
- foreign-key validation linking state transitions to recorded agent actions;
- a versioned psychological concept catalogue;
- deterministic appraisal completeness reporting and review flags;
- unit tests using synthetic data and in-memory SQLite.

The SQLite store is a prototype and is not encrypted. Do not use it for real sensitive memories yet.

## 4. Processing flow

The intended future flow is:

1. Receive a conversation event or a system action record.
2. Classify the record type and its provenance.
3. Apply privacy and consent rules before any persistence.
4. If analysis is needed, produce bounded appraisal hypotheses.
5. Validate the proposed structure and numeric ranges deterministically.
6. Store only permitted records.
7. Update explicitly defined internal variables through deterministic transition rules.
8. Optionally run one bounded self-observation pass after a completed task.
9. Make a small, permission-scoped summary available to Lilith when relevant.

Only the typed-record, local-persistence, concept-catalogue, and structured appraisal-completeness foundations currently exist.

## 5. Authority and trust boundaries

| Component | May do | Must not do |
|---|---|---|
| LLM | Propose event interpretation, alternatives, explanations | Certify truth, grant consent, set permissions, directly write unrestricted state |
| Validator | Check schema, ranges, provenance, policy | Guess missing facts |
| Memory store | Persist approved records and return scoped matches | Store unapproved emotional data |
| State engine | Apply defined and testable transitions | Create unlimited self-directed goals |
| Self-Observation | Compare action records with outcomes | Treat its own narrative as evidence |
| Hermes | Orchestrate messages and tools | Be replaced by an unbounded inner loop |

## 6. Bounded feedback

Feedback is allowed only through explicit, finite transitions. A proposed first implementation should allow at most one reflection pass per completed task. Reflection output must not recursively trigger another reflection. A budget and maximum depth must be enforced in code, not merely requested in a prompt.

## 7. Failure behaviour

- If consent is missing or unclear, do not persist user emotional data.
- If an LLM response is invalid, discard the interpretation and continue without it.
- If storage is unavailable, do not pretend that a memory was saved.
- If state validation fails, retain the previous valid state.
- If a reflection pass exceeds its budget, stop it and record a technical status without blocking normal conversation.

## 8. Non-goals

The architecture does not assert that Lilith has, can develop, or will develop subjective experience. It does not attempt clinical assessment, emotional dependency, persuasive profiling, uncontrolled self-modification, or unrestricted autonomous operation.
