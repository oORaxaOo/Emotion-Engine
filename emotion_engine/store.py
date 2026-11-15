"""Local SQLite persistence with encrypted user-event payloads.

Only user-event payloads are encrypted here. Record identifiers and timestamps,
agent-action rows, and state-transition rows remain ordinary SQLite data.
The caller must supply and securely manage the key and consent verifier.
"""

from __future__ import annotations

import json
import secrets
import sqlite3
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .errors import (
    ConsentRequiredError,
    EncryptionError,
    EncryptionKeyRequiredError,
    RecordNotFoundError,
    RecordValidationError,
)
from .models import (
    ActionOutcome,
    AffectCoordinates,
    AgentActionRecord,
    Appraisal,
    ClaimStatus,
    ConsentStatus,
    EmotionLabel,
    EvidenceOrigin,
    StateTransitionRecord,
    UserEventRecord,
)


_SCHEMA_VERSION = 2
_ENCRYPTION_PREFIX = "enc:v1:"
_NONCE_BYTES = 12
_KEY_BYTES = 32
_MAX_EXPORT_RECORDS = 10000
_SCHEMA = """
CREATE TABLE IF NOT EXISTS user_events (
    record_id TEXT PRIMARY KEY,
    occurred_at TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    consent_status TEXT NOT NULL CHECK (consent_status = 'granted'),
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_actions (
    action_id TEXT PRIMARY KEY,
    occurred_at TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS state_transitions (
    transition_id TEXT PRIMARY KEY,
    occurred_at TEXT NOT NULL,
    state_key TEXT NOT NULL,
    cause_action_id TEXT,
    payload_json TEXT NOT NULL,
    FOREIGN KEY (cause_action_id)
        REFERENCES agent_actions(action_id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_user_events_recorded_at
    ON user_events(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_actions_occurred_at
    ON agent_actions(occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_state_transitions_occurred_at
    ON state_transitions(occurred_at DESC);
"""


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _load_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _event_to_payload(record: UserEventRecord) -> dict[str, Any]:
    return {
        "schema_version": record.schema_version,
        "record_id": record.record_id,
        "occurred_at": record.occurred_at.isoformat(),
        "recorded_at": record.recorded_at.isoformat(),
        "summary": record.summary,
        "source_origin": record.source_origin.value,
        "consent_status": record.consent_status.value,
        "appraisal": (
            {
                "relevance": record.appraisal.relevance,
                "expectedness": record.appraisal.expectedness,
                "goal_congruence": record.appraisal.goal_congruence,
                "coping_potential": record.appraisal.coping_potential,
                "normative_significance": record.appraisal.normative_significance,
            }
            if record.appraisal is not None
            else None
        ),
        "affect": (
            {
                "valence": record.affect.valence,
                "arousal": record.affect.arousal,
            }
            if record.affect is not None
            else None
        ),
        "emotion_labels": [
            {
                "label": label.label,
                "origin": label.origin.value,
                "status": label.status.value,
            }
            for label in record.emotion_labels
        ],
        "uncertainties": list(record.uncertainties),
    }


def _event_from_payload(payload: dict[str, Any]) -> UserEventRecord:
    appraisal_data = payload.get("appraisal")
    affect_data = payload.get("affect")
    return UserEventRecord(
        schema_version=payload["schema_version"],
        record_id=payload["record_id"],
        occurred_at=_load_datetime(payload["occurred_at"]),
        recorded_at=_load_datetime(payload["recorded_at"]),
        summary=payload["summary"],
        source_origin=EvidenceOrigin(payload["source_origin"]),
        consent_status=ConsentStatus(payload["consent_status"]),
        appraisal=Appraisal(**appraisal_data) if appraisal_data is not None else None,
        affect=AffectCoordinates(**affect_data) if affect_data is not None else None,
        emotion_labels=tuple(
            EmotionLabel(
                label=item["label"],
                origin=EvidenceOrigin(item["origin"]),
                status=ClaimStatus(item["status"]),
            )
            for item in payload["emotion_labels"]
        ),
        uncertainties=tuple(payload["uncertainties"]),
    )


def _action_to_payload(record: AgentActionRecord) -> dict[str, Any]:
    return {
        "action_id": record.action_id,
        "occurred_at": record.occurred_at.isoformat(),
        "component": record.component,
        "action": record.action,
        "summary": record.summary,
        "outcome": record.outcome.value,
        "evidence_refs": list(record.evidence_refs),
    }


def _action_from_payload(payload: dict[str, Any]) -> AgentActionRecord:
    return AgentActionRecord(
        action_id=payload["action_id"],
        occurred_at=_load_datetime(payload["occurred_at"]),
        component=payload["component"],
        action=payload["action"],
        summary=payload["summary"],
        outcome=ActionOutcome(payload["outcome"]),
        evidence_refs=tuple(payload["evidence_refs"]),
    )


def _transition_to_payload(record: StateTransitionRecord) -> dict[str, Any]:
    return {
        "transition_id": record.transition_id,
        "occurred_at": record.occurred_at.isoformat(),
        "state_key": record.state_key,
        "previous_value": record.previous_value,
        "new_value": record.new_value,
        "reason": record.reason,
        "cause_action_id": record.cause_action_id,
    }


def _transition_from_payload(payload: dict[str, Any]) -> StateTransitionRecord:
    return StateTransitionRecord(
        transition_id=payload["transition_id"],
        occurred_at=_load_datetime(payload["occurred_at"]),
        state_key=payload["state_key"],
        previous_value=payload["previous_value"],
        new_value=payload["new_value"],
        reason=payload["reason"],
        cause_action_id=payload["cause_action_id"],
    )


def _validate_limit(limit: int) -> None:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
        raise RecordValidationError("limit must be an integer between 1 and 1000")



def generate_encryption_key() -> bytes:
    """Generate a random 256-bit key. The caller must store it outside the database."""
    return secrets.token_bytes(_KEY_BYTES)


def _associated_data(record_id: str) -> bytes:
    return b"emotion-engine:user-event:v1:" + record_id.encode("utf-8")


def _encrypt_payload(payload: str, key: bytes, record_id: str) -> str:
    nonce = secrets.token_bytes(_NONCE_BYTES)
    ciphertext = AESGCM(key).encrypt(
        nonce,
        payload.encode("utf-8"),
        _associated_data(record_id),
    )
    encoded = urlsafe_b64encode(nonce + ciphertext).decode("ascii")
    return _ENCRYPTION_PREFIX + encoded


def _decrypt_payload(value: str, key: bytes, record_id: str) -> str:
    if not isinstance(value, str) or not value.startswith(_ENCRYPTION_PREFIX):
        raise EncryptionError(
            "user memory payload is not encrypted with the supported format"
        )
    try:
        raw = urlsafe_b64decode(value[len(_ENCRYPTION_PREFIX):].encode("ascii"))
    except (ValueError, UnicodeEncodeError):
        raise EncryptionError("user memory payload is malformed") from None
    if len(raw) < _NONCE_BYTES + 16:
        raise EncryptionError("user memory payload is truncated")
    nonce, ciphertext = raw[:_NONCE_BYTES], raw[_NONCE_BYTES:]
    try:
        plaintext = AESGCM(key).decrypt(
            nonce, ciphertext, _associated_data(record_id)
        )
    except (InvalidTag, ValueError):
        raise EncryptionError(
            "user memory could not be authenticated; check the key or data integrity"
        ) from None
    try:
        return plaintext.decode("utf-8")
    except UnicodeDecodeError:
        raise EncryptionError("decrypted user memory is not valid UTF-8") from None


class SQLiteEmotionStore:
    """SQLite store with AES-256-GCM encrypted user-event payloads."""

    def __init__(
        self,
        database: str | Path,
        *,
        encryption_key: bytes | None = None,
        consent_verifier: Callable[[UserEventRecord], bool] | None = None,
    ) -> None:
        database_value = str(database)
        if not database_value:
            raise RecordValidationError("database path must not be empty")
        if encryption_key is not None and (
            not isinstance(encryption_key, bytes) or len(encryption_key) != _KEY_BYTES
        ):
            raise RecordValidationError("encryption_key must be exactly 32 bytes")
        if consent_verifier is not None and not callable(consent_verifier):
            raise RecordValidationError("consent_verifier must be callable or None")

        self._encryption_key = encryption_key
        self._consent_verifier = consent_verifier
        self._connection = sqlite3.connect(database_value)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._closed = False

        try:
            current_version = self._connection.execute(
                "PRAGMA user_version"
            ).fetchone()[0]
            if current_version > _SCHEMA_VERSION:
                raise RuntimeError(
                    f"unsupported database schema version: {current_version}"
                )
            if current_version == 0:
                self._connection.executescript(_SCHEMA)
                self._connection.execute(
                    f"PRAGMA user_version = {_SCHEMA_VERSION}"
                )
            elif current_version == 1:
                self._migrate_v1_to_v2()
                self._connection.executescript(_SCHEMA)
            else:
                self._connection.executescript(_SCHEMA)
        except Exception:
            self._connection.close()
            self._closed = True
            raise

    def _migrate_v1_to_v2(self) -> None:
        """Encrypt legacy plaintext user-event payloads in one transaction."""
        rows = self._connection.execute(
            "SELECT record_id, payload_json FROM user_events"
        ).fetchall()
        if rows and self._encryption_key is None:
            raise EncryptionKeyRequiredError(
                "legacy plaintext memories exist; supply a new 32-byte key to migrate them"
            )

        with self._connection:
            for row in rows:
                payload = row["payload_json"]
                if isinstance(payload, str) and payload.startswith(_ENCRYPTION_PREFIX):
                    plaintext = _decrypt_payload(
                        payload, self._encryption_key, row["record_id"]
                    )
                else:
                    plaintext = payload
                encrypted = _encrypt_payload(
                    plaintext, self._encryption_key, row["record_id"]
                )
                self._connection.execute(
                    "UPDATE user_events SET payload_json = ? WHERE record_id = ?",
                    (encrypted, row["record_id"]),
                )
            self._connection.execute(f"PRAGMA user_version = {_SCHEMA_VERSION}")

    def _require_encryption_key(self) -> bytes:
        if self._encryption_key is None:
            raise EncryptionKeyRequiredError(
                "a 32-byte encryption key is required to access user memories"
            )
        return self._encryption_key

    def _verify_consent(self, record: UserEventRecord) -> None:
        if record.consent_status is not ConsentStatus.GRANTED:
            raise ConsentRequiredError(
                "user event cannot be persisted without explicit granted consent"
            )
        if self._consent_verifier is None:
            raise ConsentRequiredError(
                "a trusted application consent_verifier is required; the record flag alone is insufficient"
            )
        try:
            verified = self._consent_verifier(record)
        except Exception:
            raise ConsentRequiredError(
                "consent verification failed; user memory was not stored"
            ) from None
        if verified is not True:
            raise ConsentRequiredError(
                "the application consent verifier did not approve this memory"
            )

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("Emotion store is closed")

    def close(self) -> None:
        if not self._closed:
            self._connection.close()
            self._closed = True

    def __enter__(self) -> "SQLiteEmotionStore":
        self._ensure_open()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def save_user_event(self, record: UserEventRecord) -> None:
        """Persist an emotional event only after explicit user consent."""
        self._ensure_open()
        if not isinstance(record, UserEventRecord):
            raise RecordValidationError("record must be a UserEventRecord")
        self._require_encryption_key()
        self._verify_consent(record)

        payload = _encrypt_payload(
            _dump(_event_to_payload(record)),
            self._encryption_key,
            record.record_id,
        )
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO user_events
                    (record_id, occurred_at, recorded_at, consent_status, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.record_id,
                    record.occurred_at.isoformat(),
                    record.recorded_at.isoformat(),
                    record.consent_status.value,
                    payload,
                ),
            )

    def update_user_event(self, record: UserEventRecord) -> None:
        """Replace an existing user event after re-checking consent."""
        self._ensure_open()
        if not isinstance(record, UserEventRecord):
            raise RecordValidationError("record must be a UserEventRecord")
        self._require_encryption_key()
        self._verify_consent(record)

        payload = _encrypt_payload(
            _dump(_event_to_payload(record)),
            self._encryption_key,
            record.record_id,
        )
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE user_events
                SET occurred_at = ?, recorded_at = ?, consent_status = ?, payload_json = ?
                WHERE record_id = ?
                """,
                (
                    record.occurred_at.isoformat(),
                    record.recorded_at.isoformat(),
                    record.consent_status.value,
                    payload,
                    record.record_id,
                ),
            )
            if cursor.rowcount != 1:
                raise RecordNotFoundError(f"user event not found: {record.record_id}")

    def get_user_event(self, record_id: str) -> UserEventRecord | None:
        self._ensure_open()
        key = self._require_encryption_key()
        row = self._connection.execute(
            "SELECT record_id, payload_json FROM user_events WHERE record_id = ?",
            (record_id,),
        ).fetchone()
        return (
            _event_from_payload(
                json.loads(
                    _decrypt_payload(row["payload_json"], key, row["record_id"])
                )
            )
            if row
            else None
        )

    def list_user_events(self, *, limit: int = 100) -> tuple[UserEventRecord, ...]:
        self._ensure_open()
        key = self._require_encryption_key()
        _validate_limit(limit)
        rows = self._connection.execute(
            """
            SELECT record_id, payload_json FROM user_events
            ORDER BY julianday(recorded_at) DESC, record_id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return tuple(
            _event_from_payload(
                json.loads(
                    _decrypt_payload(row["payload_json"], key, row["record_id"])
                )
            )
            for row in rows
        )

    def export_user_events(self) -> str:
        """Return a versioned JSON export of user memories only."""
        self._ensure_open()
        key = self._require_encryption_key()
        rows = self._connection.execute(
            """
            SELECT record_id, payload_json FROM user_events
            ORDER BY julianday(recorded_at) ASC, record_id ASC
            LIMIT ?
            """,
            (_MAX_EXPORT_RECORDS + 1,),
        ).fetchall()
        if len(rows) > _MAX_EXPORT_RECORDS:
            raise RecordValidationError(
                f"export exceeds the safety limit of {_MAX_EXPORT_RECORDS} records"
            )
        records = [
            _event_to_payload(
                _event_from_payload(
                    json.loads(
                        _decrypt_payload(row["payload_json"], key, row["record_id"])
                    )
                )
            )
            for row in rows
        ]
        return json.dumps(
            {
                "format": "emotion-engine-user-events",
                "format_version": 1,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "record_count": len(records),
                "records": records,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )

    def delete_user_events_before(self, cutoff: datetime) -> int:
        """Delete memories recorded before an explicit timezone-aware cutoff."""
        self._ensure_open()
        if (
            not isinstance(cutoff, datetime)
            or cutoff.tzinfo is None
            or cutoff.utcoffset() is None
        ):
            raise RecordValidationError(
                "cutoff must be a timezone-aware datetime"
            )
        cutoff_utc = cutoff.astimezone(timezone.utc).isoformat()
        with self._connection:
            cursor = self._connection.execute(
                """
                DELETE FROM user_events
                WHERE julianday(recorded_at) < julianday(?)
                """,
                (cutoff_utc,),
            )
        return cursor.rowcount

    def delete_user_event(self, record_id: str) -> bool:
        """Delete one user memory; return False when it was already absent."""
        self._ensure_open()
        with self._connection:
            cursor = self._connection.execute(
                "DELETE FROM user_events WHERE record_id = ?",
                (record_id,),
            )
        return cursor.rowcount == 1

    def delete_all_user_events(self) -> int:
        """Delete all user emotional memories and return the number removed."""
        self._ensure_open()
        with self._connection:
            cursor = self._connection.execute("DELETE FROM user_events")
        return cursor.rowcount

    def record_agent_action(self, record: AgentActionRecord) -> None:
        """Persist a technical action record, separate from user emotional memories."""
        self._ensure_open()
        if not isinstance(record, AgentActionRecord):
            raise RecordValidationError("record must be an AgentActionRecord")
        payload = _dump(_action_to_payload(record))
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO agent_actions (action_id, occurred_at, payload_json)
                VALUES (?, ?, ?)
                """,
                (record.action_id, record.occurred_at.isoformat(), payload),
            )

    def get_agent_action(self, action_id: str) -> AgentActionRecord | None:
        self._ensure_open()
        row = self._connection.execute(
            "SELECT payload_json FROM agent_actions WHERE action_id = ?",
            (action_id,),
        ).fetchone()
        return _action_from_payload(json.loads(row["payload_json"])) if row else None

    def record_state_transition(self, record: StateTransitionRecord) -> None:
        """Persist a state change, optionally linked to a recorded agent action."""
        self._ensure_open()
        if not isinstance(record, StateTransitionRecord):
            raise RecordValidationError("record must be a StateTransitionRecord")
        payload = _dump(_transition_to_payload(record))
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO state_transitions
                    (transition_id, occurred_at, state_key, cause_action_id, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.transition_id,
                    record.occurred_at.isoformat(),
                    record.state_key,
                    record.cause_action_id,
                    payload,
                ),
            )

    def list_state_transitions(
        self, *, state_key: str | None = None, limit: int = 100
    ) -> tuple[StateTransitionRecord, ...]:
        self._ensure_open()
        _validate_limit(limit)
        if state_key is None:
            rows = self._connection.execute(
                """
                SELECT payload_json FROM state_transitions
                ORDER BY occurred_at DESC, transition_id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        else:
            if not isinstance(state_key, str) or not state_key.strip():
                raise RecordValidationError("state_key must be a non-empty string or None")
            rows = self._connection.execute(
                """
                SELECT payload_json FROM state_transitions
                WHERE state_key = ?
                ORDER BY occurred_at DESC, transition_id ASC
                LIMIT ?
                """,
                (state_key, limit),
            ).fetchall()
        return tuple(
            _transition_from_payload(json.loads(row["payload_json"])) for row in rows
        )
