# Architecture

**Status:** Phase 1 data foundation, Phase 2 appraisal prototype, and Phase 3 interpretation contract are merged. Phase 4 adds a one-shot provider-neutral model adapter. No concrete provider connection, autonomous state update, or Hermes integration is active.

## 1. System boundary

Emotion Engine is a standalone Python component. Hermes remains the conversation orchestrator. A language model is an optional interpretation service, not the database, policy authority, or source of truth.

The engine has two related but distinct research tracks:

- **User-oriented affect modelling:** analyse events and emotional meaning that a user has explicitly expressed or agreed to preserve.
- **Agent-oriented self-observation:** record Lilith's own software actions, computational state changes, decisions, and outcomes.

These tracks must not be merged into one undifferentiated emotion record. A user's reported feeling is not the same thing as a model-generated interpretation; a program variable is not evidence that the program feels something.

## 2. Components

### 2.1 Psychological Knowledge Base

A versioned catalogue of concepts, definitions, scope, limitations, and research references. The initial catalogue is implemented in `emotion_engine.knowledge`. It keeps distinct theoretical perspectives separate.

### 2.2 Emotional Event Analyzer

The deterministic appraisal prototype reports which appraisal dimensions are supplied, which remain unknown, and which combinations merit review. It does not interpret raw text or assign emotion labels.

### 2.3 Interpretation Contract

The parser validates a bounded model proposal. Claims must cite evidence identifiers supplied by the caller. Model-produced emotion labels are forced to `model_inferred` and `hypothesis`. The contract checks structure and reference integrity, not semantic correctness.

### 2.4 Bounded Model Adapter

The one-shot adapter accepts a caller-selected event evidence envelope and invokes an injected text-only generator once. It enforces prompt and response character limits, passes token and timeout limits to the transport, and validates the returned JSON through the interpretation contract.

The generic adapter cannot forcibly cancel an arbitrary blocking provider function; the provider-specific transport must enforce its timeout and token cap. The adapter does not retry, write memory, or update internal state.

### 2.5 Emotional Memory

Stores only records that meet consent and retention rules. The existing SQLite prototype is local but not encrypted. It must not hold real sensitive memories until encryption, key handling, access controls, backups, retention, export, and deletion guarantees are designed and tested.

### 2.6 Internal State Model

Represents explicit computational variables used by the software. Typed state-transition records can be persisted, but no state variables, transition policies, or autonomous updates are currently active.

Optional affect-like coordinates such as valence and arousal are computational annotations, not subjective feelings.

### 2.7 Self-Observation and Emergence Research

Future components will compare structured action records and outcomes and run controlled, repeatable experiments. They must not treat generated self-narratives as evidence of subjective experience or grant new permissions.

## 3. Processing flow

1. Receive a bounded event and assign evidence identifiers to source fragments.
2. Supply only permission-scoped context to an approved text-only model transport.
3. Receive one structured interpretation proposal.
4. Validate the schema, numeric ranges, and evidence references deterministically.
5. Keep the proposal ephemeral while it is reviewed.
6. Ask for clarification or user confirmation when appropriate.
7. Only a separate consent-controlled memory workflow may persist an approved user event.
8. Any future internal state update must use explicit deterministic transition rules and its own audit record.

Only the typed data layer, local prototype persistence, concept catalogue, structured appraisal checks, interpretation parser, and injected model adapter currently exist. No model endpoint or Hermes callback is configured.

## 4. Authority and trust boundaries

| Component | May do | Must not do |
|---|---|---|
| LLM | Propose interpretations, alternatives, and questions | Certify truth, grant consent, set permissions, or write memory directly |
| Parser | Validate schema, ranges, and evidence-reference membership | Claim semantic correctness |
| Model adapter | Send a bounded evidence envelope to an injected text-only transport | Add history, retry automatically, or write memory |
| Memory store | Persist approved records | Store unapproved emotional data |
| State engine | Apply defined and tested transitions | Create unlimited self-directed goals |
| Self-Observation | Compare action records with outcomes | Treat its own narrative as evidence |
| Hermes | Orchestrate messages and tools | Be replaced by an unbounded inner loop |

## 5. Bounded feedback

Future feedback must be finite and auditable. The first self-observation implementation should allow at most one reflection pass per completed task. Reflection must not recursively trigger another reflection. Budgets and maximum depth must be enforced in code.

## 6. Failure behaviour

- If consent is missing or unclear, do not persist user emotional data.
- If model invocation fails, do not automatically retry.
- If model output is invalid, discard the proposal and continue without it.
- If evidence references do not match the supplied event envelope, reject the proposal.
- If storage is unavailable, do not pretend that a memory was saved.
- If state validation fails, retain the previous valid state.
- If a reflection pass exceeds its budget, stop it without blocking normal conversation.

## 7. Non-goals

The architecture does not assert that Lilith has, can develop, or will develop subjective experience. It does not attempt clinical assessment, manipulative profiling, uncontrolled self-modification, or unrestricted autonomous operation.
