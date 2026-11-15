# Hermes Integration Plan

**Status:** not integrated. This document describes a future adapter boundary.

## 1. Keep the engine independent

Emotion Engine should work as a standalone Python package before it becomes a Hermes plugin. That makes the core easier to test and prevents Hermes lifecycle details from becoming part of the psychological data model.

Hermes remains responsible for receiving and routing messages, model/provider selection, tool permissions and approvals, platform connectivity, and conversation lifecycle.

Emotion Engine is responsible for validating and processing structured event records, enforcing memory consent and retention rules, maintaining its own local state and memory, returning a small scoped context summary when requested, and reporting its own health and limitations.

## 2. Proposed adapter contract

A future adapter may expose a narrow set of operations:

- **analyse_event(event)** — return a structured interpretation proposal;
- **save_memory(record, consent)** — persist only after explicit approval;
- **retrieve_memories(query, scope)** — return only records within the authorised scope;
- **record_agent_action(action)** — store a structured operational event;
- **reflect_on_outcome(action_id, outcome)** — run one bounded self-observation pass;
- **get_status()** — report component state without exposing private memories.

These names are illustrative. They are not implemented APIs.

## 3. LLM boundary

The LLM may be asked to fill a strict structured response for ambiguous interpretation. Deterministic code must validate the schema and allowed fields, numeric ranges, provenance labels, missing and unknown values, consent state, output size, and processing budget.

The model must not write directly to the database or invoke privileged tools through reflection output.

## 4. Context injection

Only a small summary relevant to the current task should be considered for context injection. A memory must not be included merely because it exists. Scope, relevance, consent, and retention must be checked first.

The adapter must not silently load the complete emotional memory store into every prompt.

## 5. Hermes version verification

Before implementation, verify the actual installed Hermes version, plugin manifest requirements, hook signatures, lifecycle behaviour, and validation commands against that version. Do not infer compatibility from another version or from documentation alone.

Initial development must not install or enable the plugin in a live WhatsApp profile. Use an isolated test profile or temporary Hermes home first.

## 6. Resource policy

- No permanent background LLM loop.
- No extra model is required for the core.
- Prefer deterministic parsing, validation, state transitions, and retrieval.
- Use the configured model only for ambiguous or high-value interpretation tasks.
- Enforce maximum tokens, timeouts, and per-task reflection limits.
- The engine must remain useful when the LLM is unavailable.

## 7. Integration acceptance criteria

Do not enable a live integration until standalone tests pass, memory consent and deletion tests pass, failure and budget limits are verified, the exact Hermes version's plugin validation succeeds, isolated integration tests pass, and no active profile or WhatsApp session is changed without explicit approval.
