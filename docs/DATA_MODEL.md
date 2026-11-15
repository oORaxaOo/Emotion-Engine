# Data Model

**Status:** initial typed record and SQLite implementation exists in the Phase 1 prototype. The schema remains versioned and subject to review.

## 1. Data separation

Do not use one generic emotion object for every kind of record. The first implementation distinguishes:

- **user_event** — an event involving the user and any user-reported affect;
- **agent_action** — a technical action taken by Lilith or one of its components;
- **state_transition** — a validated change in an explicit internal computational variable.

A reflection record will be added in a later phase. These record kinds must not be merged into one undifferentiated emotion object.

## 2. Typed records

The package `emotion_engine.models` currently defines:

- `UserEventRecord`
- `EmotionLabel`
- `Appraisal`
- `AffectCoordinates`
- `AgentActionRecord`
- `StateTransitionRecord`

Records are immutable dataclasses. Their constructors validate required text, enum types, timezone-aware timestamps, numeric ranges, and JSON-scalar state values.

## 3. Provenance and epistemic status

Every emotion label includes an origin:

- `user_reported` — explicitly stated by the user;
- `system_observed` — derived from a concrete software event or measured state;
- `model_inferred` — proposed by an LLM and not independently established;
- `human_confirmed` — explicitly reviewed and confirmed by the user or an authorised operator.

Each label also has an epistemic status: `reported`, `hypothesis`, `confirmed`, `disputed`, or `unknown`.

A model-inferred label cannot be marked as directly reported or confirmed. This is a schema guard, not an independent verification of the psychological interpretation.

## 4. Optional numeric annotations

The first implementation supports optional values:

- valence: `-1.0` to `+1.0`;
- arousal: `0.0` to `1.0`;
- appraisal relevance: `0.0` to `1.0`;
- expectedness: `0.0` to `1.0`;
- goal congruence: `-1.0` to `+1.0`;
- coping potential: `0.0` to `1.0`;
- normative significance: `0.0` to `1.0`.

Null means unknown or not assessed. These values are computational annotations, not measurements of a person's true internal experience. No model confidence score is treated as emotion intensity.

## 5. Consent lifecycle

The model defines:

- `ephemeral` — may be used for the current response but not stored as a memory;
- `pending` — a save proposal has been made, but no approval exists;
- `granted` — the user explicitly approved storage;
- `revoked` — the user withdrew permission.

The SQLite store requires both `ConsentStatus.GRANTED` and an injected application `consent_verifier` that returns the literal boolean `True` for each write/update. The record flag alone is insufficient. The verifier must consult trusted application state created by a real user approval flow; this library does not provide a consent UI, user authentication, or identity system. A model cannot grant consent.

## 6. Persistence API

`SQLiteEmotionStore` currently provides:

- `save_user_event(record)`
- `get_user_event(record_id)`
- `list_user_events(limit=100)`
- `update_user_event(record)`
- `delete_user_event(record_id)`
- `delete_all_user_events()`
- `delete_user_events_before(cutoff)` — explicit, timezone-aware recorded-at retention cutoff
- `export_user_events()` — versioned JSON export of user records only, with a 10,000-record safety ceiling
- `record_agent_action(record)`
- `get_agent_action(action_id)`
- `record_state_transition(record)`
- `list_state_transitions(state_key=None, limit=100)`

The store uses parameterised SQL and a foreign key from state transitions to agent actions. It supports the in-memory SQLite database for isolated tests.

## 7. Example record

The following is illustrative JSON, not a direct serialisation contract for the Python dataclass:

~~~json
{
  "schema_version": "0.1",
  "record_id": "generated-id",
  "record_kind": "user_event",
  "occurred_at": "2026-11-15T10:30:00+01:00",
  "source_origin": "user_reported",
  "consent_status": "granted",
  "summary": "A user-confirmed short description of an important event",
  "emotion_labels": [
    {
      "label": "relief",
      "origin": "user_reported",
      "status": "reported"
    },
    {
      "label": "disappointment",
      "origin": "model_inferred",
      "status": "hypothesis"
    }
  ],
  "uncertainties": [
    "The cause of the reported emotion has not been established."
  ]
}
~~~

## 8. Storage and privacy limitation

SQLite is used because it is lightweight and available in Python's standard library. The current implementation does **not** encrypt the database or manage encryption keys. Use synthetic fixtures only. Encryption at rest, key handling, filesystem permissions, backup behaviour, retention expiry, derived-record deletion, and user-facing export must be designed and tested before storing real personal emotional data.
