# Safety and Privacy

**Status:** mandatory design constraints for all future implementation work.

Emotion-related records can reveal sensitive personal information. Privacy and user control are core requirements, not optional enhancements.

## 1. Consent before persistence

- Conversation content may be analysed transiently to answer the current message.
- Emotional information must not be stored as a long-term memory without explicit user approval.
- A model's interpretation is not consent.
- Consent must be specific enough for the user to understand what will be stored and why.
- If consent is missing, ambiguous, or unavailable, the record remains ephemeral.
- The store requires a `ConsentStatus.GRANTED` record and an injected `consent_verifier` callback that returns literal `True`. The callback is an application boundary, not proof by itself: the host must implement an understandable approval flow and consult trusted, current consent state on every write/update. If the callback is missing, rejects, or raises, storage fails closed.

## 2. Data minimisation

- Do not store complete conversation transcripts as emotional memories by default.
- Prefer a short, user-visible summary over raw message history.
- Avoid collecting information that is not needed for the stated purpose.
- Do not infer or store clinical diagnoses, trauma histories, or other sensitive psychological labels.
- Keep event records, agent operational records, and technical diagnostics separate.

## 3. User control

The library provides programmatic review, correction, individual/all-memory deletion, explicit retention pruning, and versioned JSON export. The host application must expose these controls in an understandable interface. On consent withdrawal, the host must first mark its consent authority as revoked so subsequent writes are rejected, then delete affected memories and any future derived data. Exported JSON is plaintext and must be handled as sensitive data.

Deleting a memory must also remove or invalidate derived summaries and indexes once those are introduced. A system must not claim deletion is complete until its defined deletion process has been verified.

## 4. No clinical or manipulative use

Emotion Engine is not a medical or mental-health diagnostic system. It must not claim to diagnose, treat, or determine a person's psychological condition.

It must not exploit emotional memories to increase dependency or engagement, use guilt or pressure to influence a user, rank people by emotional vulnerability, infer needs or motives as established facts, or treat a person as a fixed psychological profile based on a few events.

The purpose is context-aware assistance, not influence or control.

## 5. Agent self-observation boundaries

Self-Observation may review documented actions, outcomes, and state transitions. The Phase 6 prototype accepts only caller-selected operational evidence and returns an evidence-linked finding, a mandatory evidence-linked self-challenge, tentative causal hypotheses, limitations, and at most one follow-up question. A continuation requires new evidence and an explicit host call; one cascade is limited to four steps. It cannot change its own source code, grant itself permissions or tool access, bypass approval or safety controls, change core objectives or privacy policy, create an unlimited recursive reflection loop, or present generated statements about its own feelings as evidence. Model statements about hidden motives are never facts.

Any persistent policy or configuration change requires a separately authorised process and a reviewable diff.

## 6. Local-first security

The initial design targets local processing and local storage. Phase 5 encrypts only user-event payloads with AES-256-GCM. It does not encrypt IDs/timestamps, technical action/state tables, SQLite journals, or backups, and does not manage key custody, host authentication, access-control policy, or secure deletion. The host must supply a 32-byte key from a secure OS-backed store. Version-1 plaintext event records are migrated only when a key is supplied; without it, opening the database fails closed. Use synthetic fixtures only until the host's full security model and backup/restore workflow are implemented and reviewed.

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
