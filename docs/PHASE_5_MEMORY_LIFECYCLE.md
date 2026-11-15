# Phase 5 — Memory Lifecycle and Privacy

**Status:** merged in PR #6. This is a standalone library capability, not a deployment approval for real personal data.

## Scope

Phase 5 adds controlled persistence and lifecycle operations for user-event memories:

- AES-256-GCM encryption of each user-event JSON payload.
- A required application-supplied consent verifier on every insert and update.
- Versioned JSON export of user memories, excluding technical agent-action and state-transition rows.
- Explicit retention pruning based on the time a memory was recorded.
- Review, correction, individual deletion, and bulk deletion through the existing store and the new `MemoryLifecycle` facade.
- A fail-closed migration path from schema version 1 plaintext user-event payloads to version 2 encrypted payloads.

## Encryption model

The store requires a caller-supplied 32-byte key to write, read, list, or export user memories. AES-GCM uses a fresh 96-bit nonce for every payload. The record ID is included as authenticated additional data, so moving ciphertext to another record ID causes authentication to fail. Authentication failure, a wrong key, malformed ciphertext, or an unsupported plaintext payload raises `EncryptionError`; the code never silently falls back to plaintext.

`generate_encryption_key()` returns 32 random bytes. It does not save them. The host application must store and retrieve the key using a secure OS-backed secret store. Do not hardcode it, put it in Git, or save it beside the database. Key rotation is not implemented.

The encryption boundary is intentionally narrow. The following remain visible in the SQLite database: record IDs, occurred/recorded timestamps, consent status, the agent-action table, and the state-transition table. SQLite journals, filesystem snapshots, and backups are also outside this encryption layer. Do not put personal emotional content into technical action/state rows.

## Consent boundary

A user-event record carrying `ConsentStatus.GRANTED` is only a data claim. The host must also inject a `consent_verifier(record)` callback. It must consult trusted application consent state and return the literal boolean `True` only when the user explicitly approved this memory. A missing verifier, a false/non-boolean result, or an exception rejects the write/update. The package does not implement the UI, identity, or authentication that would make the user's approval trustworthy.

On withdrawal, the host should first update its own consent authority so the verifier rejects new writes, then invoke `MemoryLifecycle.forget_all()` (or the appropriate individual deletion). This two-system process is not atomic; the host must report partial failure honestly.

## Lifecycle operations

- `review(limit=...)` returns user memories for inspection.
- `export()` returns a versioned JSON string. It does not write a file or encrypt the export. The caller is responsible for secure handling.
- `forget(record_id)` removes one memory.
- `forget_all()` removes all user memories.
- `RetentionPolicy(max_age=...)` configures a positive duration. No default retention period is imposed. `apply_retention(now=...)` must be called by the host scheduler and removes records whose `recorded_at` is older than the computed cutoff.

Exports are bounded at 10,000 records and fail rather than silently returning a partial export. Retention uses an explicit timezone-aware cutoff. No background scheduler is included.

## Legacy database migration

A schema version 1 database with plaintext user-event payloads cannot be opened without a key. When a key is supplied, migration encrypts each payload and advances `PRAGMA user_version` to 2 inside one SQLite transaction. The migration preserves the original record IDs and timestamps. The host should make a protected backup first and verify that the new key is securely stored before migration.

## Guarantees and non-guarantees

This phase does **not** provide full-database encryption, secure key storage, key rotation, user authentication, authorization between multiple local users, encrypted exports, secure deletion from SQLite free pages/WAL/backups, backup encryption, or live Hermes integration. SQLite `DELETE` is logical deletion, not a forensic erasure guarantee. The host must set restrictive filesystem permissions, manage backups and logs, and protect exports.

Tests cover encryption at rest of user-event payloads, missing/denied consent, tampering/wrong keys, legacy migration, export boundaries, retention, and deletion. All fixtures are synthetic.
