# Proposed Data Model

**Status:** conceptual schema only. No database or API is implemented yet.

## 1. Data separation

Do not use one generic emotion object for every kind of record. At minimum, distinguish:

- **user_event** — an event involving the user and any user-reported affect;
- **agent_action** — an action taken by Lilith or one of its components;
- **state_transition** — a validated change in an internal computational variable;
- **reflection** — a bounded, evidence-linked review of an agent action or outcome.

This separation prevents a program variable from being mistaken for a user's feeling, or a generated self-description from being mistaken for evidence of subjective experience.

## 2. Proposed event record

The following is illustrative JSON, not an implemented or final schema:

~~~json
{
  "schema_version": "0.1",
  "record_id": "generated-id",
  "record_kind": "user_event",
  "subject": "user",
  "occurred_at": "2026-11-15T10:30:00+01:00",
  "recorded_at": "2026-11-15T10:31:00+01:00",
  "source": {
    "kind": "user_reported",
    "event_id": "conversation-event-reference"
  },
  "consent": {
    "status": "granted",
    "confirmed_at": "2026-11-15T10:31:00+01:00"
  },
  "event": {
    "summary": "User-confirmed short description of an important event"
  },
  "appraisal": {
    "relevance": null,
    "goal_congruence": null,
    "expectedness": null,
    "coping_potential": null,
    "normative_significance": null
  },
  "affect_model": {
    "valence": null,
    "arousal": null
  },
  "emotion_labels": [
    {
      "label": "relief",
      "origin": "user_reported",
      "confidence": null
    }
  ],
  "uncertainties": [
    "The cause of the reported emotion has not been established."
  ],
  "retention": {
    "class": "user_controlled",
    "expires_at": null
  }
}
~~~

Null means unknown or not assessed. It must not be replaced with a guessed value.

## 3. Numeric conventions

If a later implementation uses numeric values, it must publish and validate a fixed scale:

- valence: -1.0 to +1.0;
- arousal: 0.0 to 1.0;
- appraisal dimensions: use a documented scale with explicit meaning for each endpoint.

The numeric value is a model coordinate, not a measurement of a person's true internal experience. Confidence is not the same as intensity.

## 4. Model inference record

A model inference should be stored separately from a confirmed user report. It should include:

- model/provider identifier and version, if available;
- prompt/schema version;
- the evidence references used;
- alternative interpretations;
- unknowns and uncertainty;
- creation time;
- whether the user confirmed, rejected, or corrected it.

Raw prompts and full transcripts should not be retained by default. Store only the minimum summary needed for the purpose.

## 5. Consent lifecycle

Proposed states:

- **ephemeral** — may be used for the current response but not stored as a memory;
- **pending** — a save proposal has been made, but no approval exists;
- **granted** — the user explicitly approved storage;
- **revoked** — the user withdrew permission; the memory and user-derived copies must be deleted according to the deletion policy.

Consent is a hard storage gate. An LLM cannot grant consent on a user's behalf.

## 6. Deletion, correction, and export

A future implementation must support listing stored memories in understandable language, editing a summary or correcting an interpretation, deleting one record and its derived references, exporting records in a documented format, and checking that deleted records are no longer retrievable.

The exact handling of backups, indexes, and database encryption must be decided before real personal data is stored.

## 7. Storage proposal

SQLite is a reasonable first local persistence layer because it is lightweight and available in Python's standard library. This is a proposal, not a settled decision. Encryption at rest, migrations, backup handling, and data deletion guarantees must be designed and tested before storing sensitive emotional memories.
