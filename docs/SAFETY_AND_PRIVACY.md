# Safety and Privacy

**Status:** mandatory design constraints for all future implementation work.

Emotion-related records can reveal sensitive personal information. Privacy and user control are core requirements, not optional enhancements.

## 1. Consent before persistence

- Conversation content may be analysed transiently to answer the current message.
- Emotional information must not be stored as a long-term memory without explicit user approval.
- A model's interpretation is not consent.
- Consent must be specific enough for the user to understand what will be stored and why.
- If consent is missing, ambiguous, or unavailable, the record remains ephemeral.
- The current SQLite prototype checks that user-event records carry `ConsentStatus.GRANTED`; the application layer must still obtain and verify the user's actual approval.

## 2. Data minimisation

- Do not store complete conversation transcripts as emotional memories by default.
- Prefer a short, user-visible summary over raw message history.
- Avoid collecting information that is not needed for the stated purpose.
- Do not infer or store clinical diagnoses, trauma histories, or other sensitive psychological labels.
- Keep event records, agent operational records, and technical diagnostics separate.

## 3. User control

The current prototype provides programmatic inspection, correction, and deletion methods for user event records. A future release must expose these controls in an understandable user interface and support export.

Deleting a memory must also remove or invalidate derived summaries and indexes once those are introduced. A system must not claim deletion is complete until its defined deletion process has been verified.

## 4. No clinical or manipulative use

Emotion Engine is not a medical or mental-health diagnostic system. It must not claim to diagnose, treat, or determine a person's psychological condition.

It must not exploit emotional memories to increase dependency or engagement, use guilt or pressure to influence a user, rank people by emotional vulnerability, infer needs or motives as established facts, or treat a person as a fixed psychological profile based on a few events.

The purpose is context-aware assistance, not influence or control.

## 5. Agent self-observation boundaries

Self-Observation may review documented actions, outcomes, and state transitions. It may propose improvements, but it cannot change its own source code, grant itself permissions or tool access, bypass approval or safety controls, change core objectives or privacy policy, create an unlimited recursive reflection loop, or present generated statements about its own feelings as evidence.

Any persistent policy or configuration change requires a separately authorised process and a reviewable diff.

## 6. Local-first security

The initial design targets local processing and local storage. The current SQLite prototype is **not encrypted** and does not manage keys, access-control policy, backups, or secure deletion. Use synthetic fixtures only; do not put real emotional or personal data into this prototype.

Before real personal data is stored, implementation must specify encryption at rest and key handling, filesystem permissions, backup and restore behaviour, log redaction, retention and deletion semantics, which components may read each record, and whether any provider receives user data.

No external transmission should occur by default.

## 7. Fail-safe defaults

- Unknown consent: do not store.
- Invalid model output: discard it.
- Unknown provenance: label it unknown; do not promote it.
- Failed state update: retain the last valid state.
- Exceeded reflection budget: stop the reflection.
- Failed deletion: report the failure honestly and do not claim success.

## 8. Research integrity

Unexpected behaviour, fluent self-description, emotional language, or a model's claim to be conscious is not evidence of subjective experience. Research reports must describe observable capabilities, experimental conditions, and limitations without using a consciousness score or unsupported claims.
