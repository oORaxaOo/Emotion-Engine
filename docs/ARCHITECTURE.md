# Architecture

**Status:** Phases 1–6 are merged. A native Hermes plugin adapter is in development; it uses the documented Hermes plugin API and remains opt-in.

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

Stores only records that meet consent and retention rules. Phase 5 encrypts user-event payloads with AES-256-GCM, but does not encrypt the entire database or manage host key custody, access controls, or backups. See the Phase 5 privacy boundary before deployment.

### 2.6 Internal State and Reflection-Cascade State

The Phase 6 prototype keeps an explicit in-memory cascade state: current step, remaining step budget, pending evidence question, and terminal status. These are ordinary control variables. They are not affective states or subjective feelings. The cascade does not write its generated hypotheses to emotional memory.

### 2.7 Self-Observation

The self-observation module reviews one recorded agent action against caller-selected, source-labelled operational evidence. Its strict output contract separates a trace assessment, evidence-linked finding, mandatory self-challenge, explicitly tentative causal hypotheses, limitations, and at most one generated follow-up question. Every continuation requires new external evidence and one explicit host call. The maximum is four model invocations per cascade.

The model is instructed to actively try to falsify its recorded decision before proposing causes. It can evaluate only what the host supplies. A mismatch may show that an answer was unsupported or contradicted; it does not establish deliberate deception or a hidden motive. The module cannot inspect model weights, activations, or private reasoning. Its parser checks structure and evidence-ID membership, not whether the cited text semantically proves the claim.

## 3. Processing flow

1. Receive a bounded event and assign evidence identifiers to source fragments.
2. Supply only permission-scoped context to an approved text-only model transport.
3. Receive one structured interpretation proposal.
4. Validate the schema, numeric ranges, and evidence references deterministically.
5. Keep model proposals ephemeral while they are reviewed.
6. For self-observation, provide a bounded action record and selected operational evidence to the self-observation contract.
7. If a concrete follow-up question is produced, the host may collect new evidence and explicitly advance one step; otherwise the cascade ends.
8. Only a separate consent-controlled memory workflow may persist an approved user event.
9. Any persistent operational-state update must use explicit deterministic transition rules and its own audit record.

The standalone data layer, encrypted user-event payload store, concept catalogue, appraisal checks, interpretation parser, injected model adapter, and bounded self-observation engine exist. The Phase 8 adapter connects self-observation to Hermes through its public plugin API; no active Hermes profile is changed by this repository.

## 4. Authority and trust boundaries

| Component | May do | Must not do |
|---|---|---|
| LLM | Propose interpretations, alternatives, and questions | Certify truth, grant consent, set permissions, or write memory directly |
| Parser | Validate schema, ranges, and evidence-reference membership | Claim semantic correctness |
| Model adapter | Send a bounded evidence envelope to an injected text-only transport | Add history, retry automatically, or write memory |
| Memory store | Persist approved records | Store unapproved emotional data |
| State engine | Apply defined and tested transitions | Create unlimited self-directed goals |
| Self-Observation | Propose evidence-linked audit findings, hypotheses, and one next question | Treat model-generated hypotheses or previous questions as facts |
| Hermes | Orchestrate messages and tools | Be replaced by an unbounded inner loop |

## 5. Bounded feedback

Each reflection step is one model call, never an automatic recursive call. One cascade is limited to four steps. A continuation requires new evidence identifiers and an explicit host call; prior model claims are not carried forward as factual evidence. No background scheduler, tool call, memory write, or permission change is performed by the reflection engine.

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
